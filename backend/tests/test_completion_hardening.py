import pytest
from fastapi import HTTPException
from sqlalchemy import select
from test_round3 import ok, prepare, start, switch

from app import models as m
from app.readiness_checks import validate_check


@pytest.mark.parametrize(
    "category,quote",
    [
        ("deployment", "The backup retention is seven days."),
        ("rollback", "The deployment passed its health check."),
        ("restore_test", "Recovery staging runbook: follow the restore procedure."),
        ("backup_owner", "The image registry serves deployment images."),
    ],
)
def test_typed_checks_refuse_unrelated_or_unexecuted_records(category, quote):
    with pytest.raises(HTTPException) as error:
        validate_check({"category": category}, [{"quote": quote}], access_ready=True)
    assert error.value.status_code == 422


def test_restore_check_requires_structured_observation_and_followup_requires_owner():
    validate_check(
        {"category": "restore_test"},
        [
            {
                "quote": "Recovery test result. Test environment: isolated local staging. Run ID: local-1. Artifact: sha256-test. Observed result: restored three rows.\nResult: passed."
            }
        ],
        access_ready=True,
    )
    with pytest.raises(HTTPException):
        validate_check(
            {"category": "follow_up"}, [{"quote": "Backup owner requires follow-up."}], access_ready=True
        )
    with pytest.raises(HTTPException):
        validate_check({"category": "access"}, [], access_ready=False)


def test_fresh_journey_and_critical_gap_followup_are_current(workspace):
    client, _, _ = workspace
    _, people, base = start(client)
    assert ok(client.get(base + "/continuation-plan"))["stage"] == "Reconstruct"
    path, transition = prepare(client, base, people)
    checks = [x for x in transition["report"]["prerequisites"] if x.get("category") == "follow_up"]
    assert checks and all(x["gap_id"] for x in checks)
    item = checks[0]
    refs = [
        e["id"]
        for c in transition["report"]["knowledge"]
        for e in c["evidence"]
        if e["source_id"] in item.get("gap_source_ids", [])
    ]
    body = {
        "status": "confirmed",
        "evidence_ids": refs[:1],
        "note": "Missing backup knowledge remains open, with an accountable follow-up.",
    }
    assert client.post(path + "/prerequisites/" + item["id"] + "/review", json=body).status_code == 422
    body.update(owner_id=transition["successor_id"], due_date="2027-01-01")
    assert client.post(path + "/prerequisites/" + item["id"] + "/review", json=body).status_code == 200
    switch(client, people, "Savinay")
    plan = ok(client.get(base + "/continuation-plan"))
    assert plan["next_action"]["actor"] == "Savinay"
    assert plan["next_action"]["path"].endswith(transition["id"])
    assert len(plan["responsibilities"]) == 3


def test_stale_version_and_duplicate_acceptance_preserve_work(workspace):
    client, factory, _ = workspace
    _, people, base = start(client)
    path, transition = prepare(client, base, people)
    ok(client.post(path + "/reopen", json={"note": "Review new version after evidence correction."}))
    fresh = ok(client.post(path + "/generate"))
    assert (
        client.post(
            path + "/approve",
            json={
                "note": "Stale tab reviewed the previous version.",
                "expected_version": transition["version"],
            },
        ).status_code
        == 409
    )
    ok(
        client.post(
            path + "/approve",
            json={"note": "Reviewed current regenerated handover.", "expected_version": fresh["version"]},
        )
    )
    switch(client, people, "Savinay")
    transfer = ok(client.get(base + "/transitions"))[0]["transfers"][0]
    endpoint = base + "/transfers/" + transfer["id"] + "/respond"
    body = {"action": "accept", "note": "Reviewed evidence and accepted this responsibility."}
    first = ok(client.post(endpoint, json=body))
    assert ok(client.post(endpoint, json=body)) == first
    with factory() as db:
        assert (
            len(
                list(
                    db.scalars(
                        select(m.Audit).where(
                            m.Audit.resource_id == transfer["id"], m.Audit.action == "responsibility.accepted"
                        )
                    )
                )
            )
            == 1
        )
