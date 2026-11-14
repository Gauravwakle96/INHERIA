from app.acceptance_evaluation import evaluate_extraction


def test_frozen_holdout_reproduces_counts_and_discloses_misses(monkeypatch):
    import app.database as database

    monkeypatch.setattr(database, "SessionLocal", lambda: (_ for _ in ()).throw(AssertionError("No app DB")))
    first = evaluate_extraction()
    assert first == evaluate_extraction()
    assert first["counts"]["documents"] == 60
    assert first["counts"]["prose_documents"] >= 20
    assert len(first["details"]) == 60
    assert len(first["false_negatives"]) == first["candidate"]["false_negatives"]
    assert len(first["false_positives"]) == first["candidate"]["false_positives"]
    assert all(metric["denominator"] > 0 for metric in first["fields"].values())


def test_diverse_prose_regression_keeps_joint_ownership_uncertain():
    from pathlib import Path

    result = evaluate_extraction(Path("evaluation/diverse-prose-challenge.json"))
    assert result["counts"]["documents"] == 24
    joint = next(c for c in result["details"] if c["id"] == "owner-team")["observed"][0]
    assert joint["data"]["owner_id"] is None
    assert len(joint["data"]["candidate_owner_ids"]) == 2
    assert result["exact_quotes"]["rate"] == 1


def test_fresh_challenge_regression_keeps_unknown_fields_and_no_false_authority():
    from pathlib import Path

    result = evaluate_extraction(Path("evaluation/fresh-extraction-challenge.json"))
    assert result["counts"]["documents"] == 72
    assert result["targets_met"]
    assert result["exact_quotes"]["rate"] == 1
    assert not result["false_positives"]
    by_id = {d["id"]: d for d in result["details"]}
    for name in (
        "fresh-negative-not-assigned",
        "fresh-negative-indirect-rumour",
        "fresh-negative-descriptive",
    ):
        assert by_id[name]["observed"] == []
    # Pronouns require semantic/coreference resolution, not a guessed person.
    assert by_id["fresh-owner-pronoun-duty"]["observed"][0]["data"]["owner_id"] is None
    unknown = by_id["fresh-decision-without-rationale"]["observed"][0]["data"]
    assert not unknown.get("rationale")
    assert unknown["rationale_uncertainty"]


def test_uncertainty_after_duty_does_not_create_current_owner():
    from app import models as m
    from app.intelligence import parse_candidates

    person = m.User(id="ada", name="Ada Vale", email="ada@evaluation.example")
    for text in (
        "Ada Vale owns release coordination. This statement is no longer current.",
        "Ada Vale owns release coordination. This claim has not been confirmed.",
        "Ada Vale maintains the release pipeline. This is a rumour from a forwarded message.",
    ):
        assert not parse_candidates(text, [person])


def test_new_prose_upload_to_reviewed_handover_retains_exact_evidence(workspace):
    from conftest import login

    client, _, project_id = workspace
    login(client)
    base = f"/api/projects/{project_id}"
    prose = (
        "Release approval coordination is assigned to Alex Morgan. The technical lead reviews staging changes.\n\n"
        "The image registry is required by the release pipeline before an isolated staging build.\n\n"
        "An isolated recovery environment was chosen to keep restore testing away from customer databases."
    )
    uploaded = client.post(
        base + "/sources/upload", files={"file": ("fresh-approved-prose.md", prose, "text/markdown")}
    )
    assert uploaded.status_code == 201
    source_id = uploaded.json()["source"]["id"]
    assert client.post(base + "/investigations", json={"focus": "fresh prose evidence"}).status_code == 202
    claims = [
        c
        for c in client.get(base + "/claims").json()
        if any(e["source_id"] == source_id for e in c["evidence"])
    ]
    assert {c["kind"] for c in claims} == {"responsibility", "dependency", "decision"}
    assert all(c["status"] == "pending" and c["evidence"][0]["quote"] in prose for c in claims)
    for claim in claims:
        assert (
            client.post(
                base + f"/claims/{claim['id']}/review",
                json={"action": "approve", "note": "Reviewed this newly uploaded exact prose evidence."},
            ).status_code
            == 200
        )
    people = client.get(f"/api/team?project_id={project_id}").json()
    departing = next(p for p in people if p["name"] == "Alex Morgan")
    incoming = next(p for p in people if p["name"] == "Jordan Lee")
    created = client.post(
        base + "/transitions",
        json={
            "title": "Fresh prose handover",
            "departing_id": departing["id"],
            "successor_id": incoming["id"],
            "departure_date": "2027-01-01",
        },
    )
    assert created.status_code == 201
    generated = client.post(base + f"/transitions/{created.json()['id']}/generate")
    assert generated.status_code == 200
    included = {c["id"] for c in generated.json()["report"]["knowledge"]}
    assert {c["id"] for c in claims}.issubset(included)
