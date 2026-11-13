"""Round 3 security, evidence and recovery acceptance tests on isolated data."""

from datetime import timedelta

import pytest
from conftest import login
from sqlalchemy import select

from app import models as m
from app.config import settings
from app.intelligence import parse_candidates


def ok(response):
    assert response.status_code in (200, 201, 202), response.text
    return response.json()


def start(client):
    session = ok(client.post("/api/auth/judge-demo/start"))
    client.headers["X-CSRF-Token"] = session["csrf_token"]
    people = ok(client.get("/api/auth/judge-demo/people"))
    project = ok(client.get("/api/projects"))[0]
    return session, people, "/api/projects/" + project["id"]


def switch(client, people, name):
    person = next(p for p in people if p["name"] == name)
    session = ok(client.post("/api/auth/judge-demo/switch", json={"user_id": person["id"]}))
    client.headers["X-CSRF-Token"] = session["csrf_token"]
    return person


def review_current(client, base):
    for claim in ok(client.get(base + "/claims")):
        if claim["status"] == "pending" and not claim.get("authority_conflict"):
            ok(
                client.post(
                    base + "/claims/" + claim["id"] + "/review",
                    json={
                        "action": "approve",
                        "note": "Inspected case-study source evidence in this controlled test.",
                    },
                )
            )


def prepare(client, base, people):
    ok(client.post(base + "/investigations", json={"focus": ""}))
    review_current(client, base)
    transition = ok(client.get(base + "/transitions"))[0]
    path = base + "/transitions/" + transition["id"]
    transition = ok(client.post(path + "/generate"))
    ok(client.post(path + "/approve", json={"note": "Inspected evidence and incoming-user access."}))
    for claim in transition["report"]["knowledge"]:
        if claim["kind"] == "responsibility" and claim["data"].get("owner_id") == transition["departing_id"]:
            ok(
                client.post(
                    path + "/assign",
                    json={
                        "claim_id": claim["id"],
                        "successor_id": transition["successor_id"],
                        "backup_id": next(p["id"] for p in people if p["name"] == "Rudransh"),
                    },
                )
            )
    return path, ok(client.post(path + "/exercises"))


def submit_all(client, base, transition):
    for transfer in transition["transfers"]:
        if transfer["status"] != "superseded":
            ok(
                client.post(
                    base + "/transfers/" + transfer["id"] + "/respond",
                    json={"action": "accept", "note": "Reviewed this example responsibility and accepted."},
                )
            )
    for exercise in transition["exercises"]:
        if exercise["status"] == "superseded":
            continue
        refs = [
            e["id"]
            for c in transition["report"]["knowledge"]
            for e in c["evidence"]
            if e["source_id"] in exercise["expected_source_ids"]
        ]
        ok(
            client.post(
                base + "/exercises/" + exercise["id"] + "/submit",
                json={
                    "answer": "Located source procedures, identified prerequisites and risks, and explained a safe staging walkthrough. No real cloud test was performed.",
                    "evidence_ids": refs,
                    "escalation": "Escalate missing evidence to the coordinator and technical specialist before execution.",
                },
            )
        )


def pass_all(client, base, transition):
    for exercise in transition["exercises"]:
        if exercise["status"] != "superseded":
            ok(
                client.post(
                    base + "/exercises/" + exercise["id"] + "/review",
                    json={
                        "action": "pass",
                        "criteria_passed": [True] * len(exercise["criteria"]),
                        "note": "Independently assessed all scenario criteria in this controlled explanation test. No operational execution claimed.",
                    },
                )
            )


def confirm_prerequisites(client, path, transition):
    ref = transition["report"]["knowledge"][0]["evidence"][0]["id"]
    for item in transition["report"].get("prerequisites", []):
        matching = [
            e["id"]
            for c in transition["report"]["knowledge"]
            for e in c["evidence"]
            if e["source_id"] in item.get("gap_source_ids", [])
        ]
        if matching:
            ref = matching[0]
        ok(
            client.post(
                path + "/prerequisites/" + item["id"] + "/review",
                json={
                    "status": "confirmed",
                    "owner_id": transition["successor_id"],
                    "due_date": "2027-01-01",
                    "evidence_ids": [ref],
                    "note": "Controlled evidence walkthrough assessed. Follow-up work retained; no real cloud recovery test claimed.",
                },
            )
        )


def test_demo_isolation_expiry_and_source_permissions(workspace, monkeypatch):
    client, factory, original_id = workspace
    monkeypatch.setattr(settings, "demo_mode", False)
    session, people, base = start(client)
    first_org = session["user"]["org_id"]
    sources = ok(client.get(base + "/sources"))
    assert len(sources) == 13 and all(s["synthetic"] for s in sources)
    restricted = next(s for s in sources if s["restricted"])
    switch(client, people, "Savinay")
    assert len(ok(client.get(base + "/sources"))) == 12
    assert client.get(base + "/evidence/" + restricted["id"]).status_code == 404
    assert client.get(base + "/sources/" + restricted["id"] + "/impact").status_code == 404
    assert client.get("/api/projects/" + original_id + "/claims").status_code == 404
    assert client.post(base + "/investigations", json={}).status_code == 403
    _, second_people, second_base = start(client)
    assert second_base != base
    assert client.post("/api/auth/judge-demo/switch", json={"user_id": people[0]["id"]}).status_code == 404
    with factory() as db:
        for org_id in (first_org, second_people[0]["org_id"]):
            db.scalar(select(m.DemoVisit).where(m.DemoVisit.org_id == org_id)).expires_at = (
                m.utcnow() - timedelta(seconds=1)
            )
        db.commit()
    assert client.get("/api/auth/me").status_code == 401
    start(client)
    with factory() as db:
        assert db.get(m.Project, original_id)
        assert not db.get(m.Organisation, first_org)


def test_legacy_persona_login_cannot_enter_private_demo(workspace):
    client, _, _ = workspace
    _, people, _ = start(client)
    assert client.post("/api/auth/demo-login", json={"user_id": people[0]["id"]}).status_code == 403
    public_ids = {u["id"] for u in ok(client.get("/api/auth/demo-users"))}
    assert all(person["id"] not in public_ids for person in people)


def test_invitation_is_hashed_single_use_and_revocable(workspace):
    client, factory, pid = workspace
    login(client)
    base = f"/api/projects/{pid}"
    payload = {
        "name": "New Teammate",
        "email": "new-teammate@example.com",
        "title": "Incoming DevOps engineer",
        "role": "incoming",
    }
    invitation = ok(client.post(base + "/invitations", json=payload))
    token = invitation["join_path"].split("token=", 1)[1]
    with factory() as db:
        stored = db.get(m.Invitation, invitation["id"])
        assert stored.token_hash != token and len(stored.token_hash) == 64
    assert "join_path" not in ok(client.get(base + "/invitations"))[0]
    assert client.post(base + "/invitations", json={**payload, "role": "admin"}).status_code == 422
    joined = ok(
        client.post(
            "/api/auth/invitation/accept", json={"token": token, "password": "test-only-long-password"}
        )
    )
    client.headers["X-CSRF-Token"] = joined["csrf_token"]
    assert joined["user"]["role"] == "incoming"
    assert (
        client.post(
            "/api/auth/invitation/accept", json={"token": token, "password": "test-only-long-password"}
        ).status_code
        == 404
    )
    assert client.post(base + "/invitations", json=payload).status_code == 403
    login(client)
    second = ok(client.post(base + "/invitations", json={**payload, "email": "revoke-me@example.com"}))
    ok(client.post(base + "/invitations/" + second["id"] + "/revoke"))
    assert (
        client.post(
            "/api/auth/invitation/accept",
            json={"token": second["join_path"].split("token=")[1], "password": "test-only-long-password"},
        ).status_code
        == 404
    )


def test_expired_invitation_cannot_be_accepted(workspace):
    client, factory, pid = workspace
    login(client)
    invitation = ok(
        client.post(
            f"/api/projects/{pid}/invitations",
            json={
                "name": "Expired User",
                "email": "expired@example.com",
                "title": "Engineer",
                "role": "employee",
            },
        )
    )
    with factory() as db:
        db.get(m.Invitation, invitation["id"]).expires_at = m.utcnow() - timedelta(seconds=1)
        db.commit()
    assert (
        client.post(
            "/api/auth/invitation/accept",
            json={"token": invitation["join_path"].split("token=")[1], "password": "test-only-long-password"},
        ).status_code
        == 404
    )


def test_access_grant_requires_independent_authorised_reviewer(workspace):
    client, _, _ = workspace
    _, people, base = start(client)
    source = next(s for s in ok(client.get(base + "/sources")) if s["restricted"])
    switch(client, people, "Savinay")
    item = ok(
        client.post(
            base + "/access-requests",
            json={"purpose": "Need approved recovery coordination knowledge for my next steps."},
        )
    )
    assert "source_id" not in item
    assert (
        client.post(
            base + "/access-requests/" + item["id"] + "/review",
            json={"action": "approve", "source_id": source["id"], "note": "Attempt self approval."},
        ).status_code
        == 403
    )
    switch(client, people, "Rudransh")
    ok(
        client.post(
            base + "/access-requests/" + item["id"] + "/review",
            json={
                "action": "approve",
                "source_id": source["id"],
                "note": "Source authorised for this incoming case-study member.",
            },
        )
    )
    switch(client, people, "Savinay")
    assert client.get(base + "/evidence/" + source["id"]).status_code == 200
    switch(client, people, "Gaurav")
    assert ok(client.get(base + "/access-requests")) == []


def test_opposing_decisions_require_explicit_authority_resolution(workspace):
    client, _, _ = workspace
    _, _, base = start(client)
    ok(client.post(base + "/investigations", json={"focus": ""}))
    conflicts = [c for c in ok(client.get(base + "/claims")) if c.get("authority_conflict")]
    assert len(conflicts) == 2
    for claim in conflicts:
        assert (
            client.post(
                base + "/claims/" + claim["id"] + "/review",
                json={"action": "approve", "note": "Attempt contradictory approval."},
            ).status_code
            == 409
        )
    chosen = ok(
        client.post(
            base + "/claims/" + conflicts[0]["id"] + "/resolve-authority",
            json={"note": "Reviewed both sources and selected this authority for the controlled scenario."},
        )
    )
    assert chosen["status"] == "verified" and not chosen["authority_conflict"]
    assert any(c["status"] == "superseded" for c in ok(client.get(base + "/claims")))


def test_complete_demo_rejection_reopen_prerequisites_and_practical_review(workspace):
    client, _, _ = workspace
    _, people, base = start(client)
    path, transition = prepare(client, base, people)
    assert len(transition["transfers"]) == 3
    switch(client, people, "Savinay")
    transfer = transition["transfers"][0]
    ok(
        client.post(
            base + "/transfers/" + transfer["id"] + "/respond",
            json={"action": "reject", "note": "Need recovery evidence before accepting."},
        )
    )
    assert not ok(client.get(path + "/readiness"))["ready"]
    switch(client, people, "Rudransh")
    ok(client.post(path + "/reopen", json={"note": "Reopened to add a required recovery review."}))
    prerequisite = ok(
        client.post(
            path + "/prerequisites",
            json={"title": "Recovery readiness evidence walkthrough reviewed", "required": True},
        )
    )
    assert client.post(path + "/approve", json={"note": "Cannot skip generation."}).status_code == 409
    ok(client.post(path + "/generate"))
    ok(client.post(path + "/approve", json={"note": "Reviewed second version and recovery requirements."}))
    transition = ok(client.get(base + "/transitions"))[0]
    assert transition["version"] == 2
    switch(client, people, "Savinay")
    submit_all(client, base, transition)
    switch(client, people, "Rudransh")
    exercise = transition["exercises"][0]
    assert (
        client.post(
            base + "/exercises/" + exercise["id"] + "/review",
            json={"action": "pass", "note": "Attempt without criterion assessment."},
        ).status_code
        == 422
    )
    ok(
        client.post(
            base + "/exercises/" + exercise["id"] + "/review",
            json={
                "action": "needs_revision",
                "note": "Explain rollback restrictions using current evidence.",
            },
        )
    )
    assert client.post(path + "/close").status_code == 409
    switch(client, people, "Savinay")
    submit_all(client, base, transition)
    switch(client, people, "Rudransh")
    pass_all(client, base, transition)
    assert client.post(path + "/close").status_code == 409
    confirm_prerequisites(client, path, transition)
    evidence = transition["report"]["knowledge"][0]["evidence"][0]["id"]
    ok(
        client.post(
            path + "/prerequisites/" + prerequisite["id"] + "/review",
            json={
                "status": "confirmed",
                "note": "Evidence walkthrough reviewed. No actual restore test or cloud permission granted.",
                "evidence_ids": [evidence],
            },
        )
    )
    assert ok(client.get(path + "/readiness"))["ready"]
    assert ok(client.post(path + "/close"))["status"] == "closed"


@pytest.mark.parametrize(
    "revision_note",
    [
        "Check schema compatibility",
        "Require approved image digest",
        "Record health evidence",
        "Review migration risk",
        "Confirm deployment approver",
        "Identify failure stop conditions",
        "Inspect release logs",
        "Document rollback constraints",
        "Review staging isolation",
        "Record follow-up owner",
    ],
)
def test_source_change_invalidates_tasks_and_can_recover_without_duplicates(workspace, revision_note):
    client, _, _ = workspace
    _, people, base = start(client)
    path, transition = prepare(client, base, people)
    source = next(s for s in ok(client.get(base + "/sources")) if s["name"].startswith("03-"))
    content = b"Procedure: release-pipeline staging release walkthrough\nSystem: release-pipeline\nStatus: current\nCheck approved commit, build tests and specialist approvals. New procedure requires schema compatibility before rollback."
    content += ("\n" + revision_note + ".").encode()
    replaced = ok(
        client.post(
            base + "/sources/" + source["id"] + "/replace",
            files={"file": ("deployment-v2.md", content, "text/markdown")},
        )
    )
    assert replaced["source"]["version"] == 2
    impact = ok(client.get(base + "/sources/" + source["id"] + "/impact"))
    assert any(c["status"] == "invalidated" for c in impact["claims"])
    assert impact["transitions"][0]["requires_revalidation"]
    assert any(e["status"] == "needs_revision" for e in impact["exercises"])
    assert not ok(client.get(path + "/readiness"))["ready"]
    ok(client.post(base + "/investigations", json={"focus": ""}))
    review_current(client, base)
    ok(
        client.post(
            path + "/reopen", json={"note": "Source changed. Reopen for current evidence and reassessment."}
        )
    )
    ok(client.post(path + "/generate"))
    ok(client.post(path + "/approve", json={"note": "Reviewed new evidence for the incoming person."}))
    updated = ok(client.post(path + "/exercises"))
    switch(client, people, "Savinay")
    submit_all(client, base, updated)
    switch(client, people, "Rudransh")
    pass_all(client, base, updated)
    confirm_prerequisites(client, path, updated)
    assert ok(client.get(path + "/readiness"))["ready"]


@pytest.mark.parametrize("interrupted_at", [2, 3, 4, 7, 11])
def test_interrupted_investigation_has_durable_idempotent_resume(workspace, monkeypatch, interrupted_at):
    client, factory, _ = workspace
    _, _, base = start(client)
    import app.intelligence as intelligence

    original = intelligence.reconstruct_project
    calls = 0

    def interrupted(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == interrupted_at:
            raise RuntimeError("Controlled interruption after one durable checkpoint")
        return original(*args, **kwargs)

    monkeypatch.setattr(intelligence, "reconstruct_project", interrupted)
    run = ok(client.post(base + "/investigations", json={"focus": ""}))
    with factory() as db:
        record = db.get(m.Investigation, run["id"])
        assert record.status == "failed" and len(record.report["checkpoint"]["sources"]) == interrupted_at - 1
    monkeypatch.setattr(intelligence, "reconstruct_project", original)
    ok(client.post(base + "/investigations/" + run["id"] + "/resume"))
    assert ok(client.get(base + "/investigations"))[0]["status"] == "completed"
    count = len(ok(client.get(base + "/claims")))
    ok(client.post(base + "/investigations", json={"focus": ""}))
    assert len(ok(client.get(base + "/claims"))) == count


@pytest.mark.parametrize(
    "text,kind,field,value",
    [
        (
            "Gaurav is responsible for the release-pipeline. The team reviews release approvals.",
            "responsibility",
            "component",
            "the release-pipeline",
        ),
        (
            "We chose blue-green because application releases need safer rollback. We rejected rolling deployments.",
            "decision",
            "rationale",
            "application releases need safer rollback",
        ),
        (
            "release-pipeline depends on image-registry. This is an explicitly documented dependency.",
            "dependency",
            "to_component",
            "image-registry",
        ),
    ],
)
def test_supported_prose_fields_are_exact_source_spans(text, kind, field, value):
    user = m.User(id="test-person", name="Gaurav", email="person@example.com")
    candidates = parse_candidates(text, [user])
    assert candidates[0]["kind"] == kind and candidates[0]["data"][field] == value
    assert candidates[0]["quote"] in text
    assert all(span in text for span in candidates[0]["data"]["field_evidence"].values())
