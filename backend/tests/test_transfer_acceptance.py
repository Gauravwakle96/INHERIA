"""Twelve distinct authorised/negative journeys; never executes cloud commands."""

import pytest
from test_round3 import confirm_prerequisites, ok, pass_all, prepare, start, submit_all, switch

from app import models as m

SCENARIOS = (
    "incoming_accepts",
    "wrong_owner_rejected",
    "missing_evidence_rejected",
    "supervisor_cannot_submit",
    "incoming_cannot_self_assess",
    "rejection_blocks_closure",
    "partial_rubric_rejected",
    "revision_then_reassessment",
    "critical_prerequisite_blocks",
    "reopen_requires_reapproval",
    "staging_citation_recorded",
    "staging_revocation_blocks",
)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_transfer_role_and_recovery_scenarios(workspace, scenario):
    client, factory, _ = workspace
    _, people, base = start(client)
    path, transition = prepare(client, base, people)
    transfer, exercise = transition["transfers"][0], transition["exercises"][0]
    refs = [
        e["id"]
        for c in transition["report"]["knowledge"]
        for e in c["evidence"]
        if e["source_id"] in exercise["expected_source_ids"]
    ]
    body = {
        "answer": "Reviewed the current release sources, staging scope, approval conditions and missing evidence. This is a controlled walkthrough, not a production execution.",
        "evidence_ids": refs,
        "escalation": "Escalate to the technical lead before using incomplete operational instructions.",
    }
    assessment = {
        "action": "pass",
        "criteria_passed": [True] * len(exercise["criteria"]),
        "note": "Independently reviewed all scenario requirements in the authorised evidence walkthrough.",
    }
    submit_path = base + "/exercises/" + exercise["id"] + "/submit"
    review_path = base + "/exercises/" + exercise["id"] + "/review"
    respond_path = base + "/transfers/" + transfer["id"] + "/respond"
    if scenario == "wrong_owner_rejected":
        assert (
            client.post(
                respond_path,
                json={"action": "accept", "note": "Administrator cannot accept for the successor."},
            ).status_code
            == 403
        )
        return
    if scenario == "supervisor_cannot_submit":
        assert client.post(submit_path, json=body).status_code == 403
        return
    switch(client, people, "Savinay")
    if scenario == "incoming_accepts":
        assert (
            ok(
                client.post(
                    respond_path, json={"action": "accept", "note": "Reviewed the proposed responsibility."}
                )
            )["status"]
            == "accepted"
        )
        assert not ok(client.get(path + "/readiness"))["ready"]
        return
    if scenario == "missing_evidence_rejected":
        assert client.post(submit_path, json={**body, "evidence_ids": []}).status_code == 422
        assert client.post(submit_path, json={**body, "evidence_ids": ["wrong-source"]}).status_code == 422
        return
    if scenario == "rejection_blocks_closure":
        ok(
            client.post(
                respond_path, json={"action": "reject", "note": "Recovery prerequisites remain incomplete."}
            )
        )
        switch(client, people, "Rudransh")
        assert client.post(path + "/close").status_code == 409
        return
    submit_all(client, base, transition)
    if scenario == "incoming_cannot_self_assess":
        assert client.post(review_path, json=assessment).status_code == 403
        return
    switch(client, people, "Rudransh")
    if scenario == "partial_rubric_rejected":
        assert (
            client.post(review_path, json={**assessment, "criteria_passed": [True, False]}).status_code == 422
        )
        return
    if scenario == "revision_then_reassessment":
        ok(
            client.post(
                review_path,
                json={
                    "action": "needs_revision",
                    "note": "Explain the migration stop conditions using current sources.",
                },
            )
        )
        switch(client, people, "Savinay")
        ok(client.post(submit_path, json=body))
        switch(client, people, "Rudransh")
        record = ok(client.post(review_path, json=assessment))
        assert [r["action"] for r in record["assessment"]["review_history"]] == ["needs_revision", "pass"]
        return
    if scenario == "reopen_requires_reapproval":
        ok(
            client.post(
                path + "/reopen", json={"note": "Corrected recovery instructions need a new approval."}
            )
        )
        assert client.post(review_path, json=assessment).status_code == 409
        assert (
            client.post(path + "/approve", json={"note": "Cannot approve before regenerating."}).status_code
            == 409
        )
        ok(client.post(path + "/generate"))
        assert (
            ok(client.post(path + "/approve", json={"note": "Reviewed the corrected handover version."}))[
                "version"
            ]
            == 2
        )
        return
    pass_all(client, base, transition)
    if scenario == "critical_prerequisite_blocks":
        assert client.post(path + "/close").status_code == 409
        confirm_prerequisites(client, path, transition)
        assert ok(client.get(path + "/readiness"))["ready"]
        return
    # An explicitly authored observation record is stored as verified evidence.
    # This fixture is not claimed to be a real deployment or restore.
    with factory() as db:
        t = db.get(m.Transition, transition["id"])
        source = m.Source(
            org_id=t.org_id,
            project_id=t.project_id,
            name="Controlled staging observation",
            kind="markdown",
            synthetic=True,
        )
        db.add(source)
        db.flush()
        chunk = m.Chunk(
            org_id=t.org_id,
            project_id=t.project_id,
            source_id=source.id,
            source_version=1,
            ordinal=0,
            locator="Authored staging observation",
            text="Authored staging observation: isolated test environment review of release health. No actual execution occurred.",
        )
        claim = m.Claim(
            org_id=t.org_id,
            project_id=t.project_id,
            kind="procedure",
            title="Controlled staging observation",
            summary=chunk.text,
            status="verified",
            verified_by=next(p["id"] for p in people if p["name"] == "Rudransh"),
            data={},
        )
        db.add_all([chunk, claim])
        db.flush()
        evidence = m.Evidence(
            org_id=t.org_id,
            project_id=t.project_id,
            source_id=source.id,
            source_version=1,
            chunk_id=chunk.id,
            claim_id=claim.id,
            quote=chunk.text,
        )
        db.add(evidence)
        db.commit()
        sid, eid = source.id, evidence.id
    switch(client, people, "Savinay")
    assert (
        client.post(
            submit_path, json={**body, "validation_kind": "staging_observation", "staging_evidence_ids": refs}
        ).status_code
        == 422
    )
    submitted = ok(
        client.post(
            submit_path,
            json={**body, "validation_kind": "staging_observation", "staging_evidence_ids": [eid]},
        )
    )
    assert submitted["assessment"]["staging_evidence_ids"] == [eid]
    switch(client, people, "Rudransh")
    if scenario == "staging_citation_recorded":
        record = ok(client.post(review_path, json=assessment))
        assert record["assessment"]["validation_kind"] == "staging_observation"
        assert record["assessment"]["staging_source_versions"] == {sid: 1}
    else:
        ok(client.post(base + "/sources/" + sid + "/revoke"))
        assert client.post(review_path, json=assessment).status_code == 409
        assert not ok(client.get(path + "/readiness"))["ready"]
