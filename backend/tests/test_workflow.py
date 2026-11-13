from conftest import login
from sqlalchemy import select

from app import models as m


def post_ok(client, path, body=None, codes=(200, 201, 202)):
    response = client.post(path, json=body) if body is not None else client.post(path)
    assert response.status_code in codes, response.text
    return response.json()


def test_complete_connect_to_validate_requires_each_human_gate(workspace):
    client, factory, project_id = workspace
    login(client)
    base = f"/api/projects/{project_id}"
    initial_summary = client.get(base + "/continuity-summary").json()
    assert initial_summary["completion"] is None
    assert initial_summary["completed_handovers"] == 0
    source_count = len(client.get(base + "/sources").json())
    assert source_count == 125
    claims = client.get(base + "/claims").json()
    assert claims and all(c["status"] == "pending" for c in claims)
    assert all(e["quote"] for c in claims for e in c["evidence"])
    post_ok(client, base + "/investigations", {"focus": ""})
    runs = client.get(base + "/investigations").json()
    assert runs[0]["status"] == "completed"
    assert any(f["kind"] == "single_owner" for f in runs[0]["report"]["findings"])
    people = client.get("/api/team", params={"project_id": project_id}).json()
    departing = next(u for u in people if u["name"] == "Alex Morgan")
    successor = next(u for u in people if u["name"] == "Jordan Lee")
    transition = post_ok(
        client,
        base + "/transitions",
        {
            "title": "Alex backend continuity",
            "departing_id": departing["id"],
            "successor_id": successor["id"],
            "departure_date": "2027-01-15",
        },
    )
    path = base + "/transitions/" + transition["id"]
    assert client.post(path + "/approve", json={"note": "Approved by manager."}).status_code == 409
    assert client.post(path + "/generate").status_code == 409
    # Verify machine candidates with exact evidence; no claims become verified automatically.
    for claim in claims:
        if claim.get("authority_conflict"):
            continue
        post_ok(
            client,
            base + "/claims/" + claim["id"] + "/review",
            {"action": "approve", "note": "Reviewed source statement and provenance."},
        )
    transition = post_ok(client, path + "/generate")
    assert transition["report"]["knowledge"]
    assert client.post(path + "/close").status_code == 409
    post_ok(client, path + "/approve", {"note": "Reviewed evidence and successor permissions."})
    obligations = [
        c
        for c in transition["report"]["knowledge"]
        if c["kind"] == "responsibility" and c["data"].get("owner_id") == departing["id"]
    ]
    assert len(obligations) >= 3
    transfers = [
        post_ok(client, path + "/assign", {"claim_id": c["id"], "successor_id": successor["id"]})
        for c in obligations
    ]
    transition = post_ok(client, path + "/exercises")
    assert transition["exercises"]
    for transfer in transfers:
        assert (
            client.post(
                base + "/transfers/" + transfer["id"] + "/respond",
                json={"action": "accept", "note": "Manager cannot impersonate successor."},
            ).status_code
            == 403
        )
    login(client, "Jordan Lee")
    for transfer in transfers:
        post_ok(
            client,
            base + "/transfers/" + transfer["id"] + "/respond",
            {"action": "accept", "note": "Reviewed responsibility and accepted ownership."},
        )
    for exercise in transition["exercises"]:
        ids = [
            e["id"]
            for c in transition["report"]["knowledge"]
            for e in c["evidence"]
            if e["source_id"] in exercise["expected_source_ids"]
        ]
        post_ok(
            client,
            base + "/exercises/" + exercise["id"] + "/submit",
            {
                "answer": "I located the documented steps, prerequisites and dependencies and described a safe test-environment walkthrough without production execution.",
                "evidence_ids": ids,
                "escalation": "Escalate any undocumented failure to the technical lead before making changes.",
            },
        )
        assert (
            client.post(
                base + "/exercises/" + exercise["id"] + "/review",
                json={"action": "pass", "note": "I cannot validate my own practical explanation."},
            ).status_code
            == 403
        )
    report = client.get(path + "/readiness").json()
    assert not report["ready"]
    assert report["accepted"] == len(obligations)
    login(client, "Priya Shah")
    for exercise in transition["exercises"]:
        post_ok(
            client,
            base + "/exercises/" + exercise["id"] + "/review",
            {
                "action": "pass",
                "criteria_passed": [True] * len(exercise["criteria"]),
                "note": "Validated documented evidence, safe walkthrough, prerequisites and escalation against each predefined criterion.",
            },
        )
    from test_round3 import confirm_prerequisites

    assert not client.get(path + "/readiness").json()["ready"]
    confirm_prerequisites(client, path, transition)
    assert client.get(path + "/readiness").json()["ready"]
    assert post_ok(client, path + "/close")["status"] == "closed"
    summary = client.get(base + "/continuity-summary").json()
    assert summary["completed_handovers"] == 1
    assert summary["completion"]["current"]
    assert summary["completion"]["accepted"] == len(obligations)
    assert summary["completion"]["validated"] == len(transition["exercises"])
    contributions = {p["id"]: p for p in summary["contributors"]}
    assert contributions[departing["id"]]["responsibilities_transferred"] == len(obligations)
    assert contributions[successor["id"]]["responsibilities_owned"] == len(obligations)
    assert contributions[successor["id"]]["responsibilities_accepted"] == len(obligations)
    assert contributions[successor["id"]]["walkthroughs_submitted"] == len(transition["exercises"])
    assert "password" not in str(summary)
    assert client.get("/api/projects/nonexistent/continuity-summary").status_code in {403, 404}
    login(client, "Jordan Lee")
    incoming_summary = client.get(base + "/continuity-summary").json()
    assert incoming_summary["completion"]["id"] == transition["id"]
    assert incoming_summary["completion"]["current"]
    login(client, "Priya Shah")
    with factory() as db:
        actions = set(db.scalars(select(m.Audit.action).where(m.Audit.project_id == project_id)))
        assert {
            "handover.approved",
            "responsibility.accepted",
            "validation.passed",
            "transition.closed",
            "ownership.transferred",
        } <= actions
        for obligation in obligations:
            transferred = db.get(m.Claim, obligation["id"])
            assert transferred.data["owner_id"] == successor["id"]
            assert transferred.data["previous_owner_id"] == departing["id"]
            assert transferred.data["ownership_provenance"]
        removed_source_id = obligations[0]["evidence"][0]["source_id"]
        ownership_source_id = db.get(m.Claim, obligations[0]["id"]).data["ownership_provenance"]
    assert client.delete(base + "/sources/" + removed_source_id).status_code == 200
    assert client.get(base + "/continuity-summary").json()["completion"] is None
    with factory() as db:
        assert not list(db.scalars(select(m.Chunk).where(m.Chunk.source_id == ownership_source_id)))
        assert db.get(m.Source, ownership_source_id).status == "revoked"
        assert db.get(m.Claim, obligations[0]["id"]).summary == "Source evidence was deleted."


def test_explanation_correction_returns_to_pending_and_needs_other_reviewer(workspace):
    client, factory, project_id = workspace
    login(client)
    base = f"/api/projects/{project_id}"
    claim = client.get(base + "/claims").json()[0]
    post_ok(
        client,
        base + "/claims/" + claim["id"] + "/review",
        {
            "action": "correct",
            "summary": "Corrected employee explanation remains independently unverified.",
            "note": "Correction requires independent review.",
        },
    )
    assert (
        client.post(
            base + "/claims/" + claim["id"] + "/review",
            json={"action": "approve", "note": "Attempt self verification."},
        ).status_code
        == 403
    )
    login(client, "Priya Shah")
    assert (
        post_ok(
            client,
            base + "/claims/" + claim["id"] + "/review",
            {"action": "approve", "note": "Independently reviewed correction and sources."},
        )["status"]
        == "verified"
    )


def test_simulation_is_hypothetical_and_does_not_change_ownership(workspace):
    client, factory, project_id = workspace
    login(client)
    base = f"/api/projects/{project_id}"
    people = client.get("/api/team", params={"project_id": project_id}).json()
    alex = next(u for u in people if u["name"] == "Alex Morgan")
    before = client.get(base + "/claims").json()
    report = post_ok(
        client,
        base + "/simulations",
        {
            "employee_id": alex["id"],
            "scenario": "unavailability",
            "assumptions": ["Employee unavailable for this hypothetical scenario."],
        },
    )
    assert report["report"]["hypothetical"] is True
    assert report["report"]["affected"]
    assert report["report"]["unknowns"]
    after = client.get(base + "/claims").json()
    assert [(c["id"], c["status"], c["data"]) for c in before] == [
        (c["id"], c["status"], c["data"]) for c in after
    ]


def test_digital_successor_abstains_without_verified_evidence(workspace):
    client, factory, project_id = workspace
    login(client)
    base = f"/api/projects/{project_id}"
    assert not post_ok(client, base + "/successor/ask", {"question": "How do we deploy billing-api?"})[
        "known"
    ]
    claims = client.get(base + "/claims", params={"kind": "procedure"}).json()
    assert claims
    claim = claims[0]
    post_ok(
        client,
        base + "/claims/" + claim["id"] + "/review",
        {"action": "approve", "note": "Procedure verified by reviewer."},
    )
    result = post_ok(client, base + "/successor/ask", {"question": claim["title"]})
    assert result["known"] and result["citations"]
    assert not post_ok(
        client, base + "/successor/ask", {"question": "What is the lunar gravity coefficient?"}
    )["known"]
