import json

import pytest
from conftest import login
from sqlalchemy import select
from test_workflow import post_ok

from app import models as m
from app.intelligence import citations, current_claims


def generated_handover(client, project_id):
    user = login(client)
    base = f"/api/projects/{project_id}"
    claims = client.get(base + "/claims").json()
    responsibility = next(
        c
        for c in claims
        if c["kind"] == "responsibility" and c["data"].get("owner_id") and "billing" in c["title"].lower()
    )
    post_ok(
        client,
        base + "/claims/" + responsibility["id"] + "/review",
        {"action": "approve", "note": "Reviewed exact evidence statement."},
    )
    team = client.get("/api/team", params={"project_id": project_id}).json()
    successor = next(u for u in team if u["name"] == "Jordan Lee")
    transition = post_ok(
        client,
        base + "/transitions",
        {
            "title": "Regression handover",
            "departing_id": responsibility["data"]["owner_id"],
            "successor_id": successor["id"],
            "departure_date": "2027-01-15",
        },
    )
    path = base + "/transitions/" + transition["id"]
    transition = post_ok(client, path + "/generate")
    return user, path, transition, responsibility


@pytest.mark.parametrize(
    "suffix,body",
    [
        ("/generate", None),
        ("/approve", {"note": "Read-only project member attempts approval."}),
        ("/assign", {"claim_id": "not-used", "successor_id": "not-used"}),
        ("/exercises", None),
        ("/close", None),
    ],
)
def test_org_privilege_does_not_bypass_read_only_project_membership(workspace, suffix, body):
    client, factory, project_id = workspace
    user, path, transition, claim = generated_handover(client, project_id)
    with factory() as db:
        member = db.scalar(
            select(m.Membership).where(
                m.Membership.project_id == project_id, m.Membership.user_id == user["id"]
            )
        )
        member.role = "incoming"
        db.commit()
    response = client.post(path + suffix, json=body) if body is not None else client.post(path + suffix)
    assert response.status_code == 403, response.text
    assert (
        client.post(
            f"/api/projects/{project_id}/claims/{claim['id']}/review",
            json={"action": "reject", "note": "Forbidden write."},
        ).status_code
        == 403
    )


def test_incorrect_evidence_attribution_cannot_read_restricted_chunk(workspace):
    client, factory, project_id = workspace
    user = login(client)
    with factory() as db:
        actor = db.get(m.User, user["id"])
        claim = current_claims(db, actor, project_id)[0]
        ref = db.scalar(select(m.Evidence).where(m.Evidence.claim_id == claim.id))
        restricted = m.Source(
            org_id=user["org_id"],
            project_id=project_id,
            name="Private chunk",
            kind="txt",
            acl=["another-user"],
        )
        db.add(restricted)
        db.flush()
        secret = m.Chunk(
            org_id=user["org_id"],
            project_id=project_id,
            source_id=restricted.id,
            source_version=1,
            ordinal=0,
            locator="Restricted",
            text="Confidential source content must never be attributed to a public source.",
        )
        db.add(secret)
        db.flush()
        ref.chunk_id, ref.quote = secret.id, secret.text
        claim_id = claim.id
        db.commit()
        assert claim_id not in {c.id for c in current_claims(db, actor, project_id)}
        assert citations(db, actor, claim) == []
    assert "Confidential source content" not in client.get(f"/api/projects/{project_id}/claims").text


def test_stored_simulation_and_audit_notes_obey_current_evidence(workspace):
    client, factory, project_id = workspace
    user, path, transition, claim = generated_handover(client, project_id)
    base = f"/api/projects/{project_id}"
    post_ok(client, path + "/approve", {"note": "Approved with source ACL checks."})
    transfer = post_ok(
        client, path + "/assign", {"claim_id": claim["id"], "successor_id": transition["successor_id"]}
    )
    simulation = post_ok(
        client,
        base + "/simulations",
        {"employee_id": transition["departing_id"], "scenario": "unavailability"},
    )
    with factory() as db:
        source = db.get(m.Source, claim["evidence"][0]["source_id"])
        source.version += 1
        transfer_record = db.get(m.Transfer, transfer["id"])
        transfer_record.note = "Restricted ownership review note."
        db.add(
            m.Audit(
                org_id=user["org_id"],
                project_id=project_id,
                actor_id=user["id"],
                action="responsibility.accepted",
                resource_type="transfer",
                resource_id=transfer["id"],
                details={"note": transfer_record.note},
            )
        )
        db.commit()
    assert simulation["id"] not in {s["id"] for s in client.get(base + "/simulations").json()}
    assert "Restricted ownership review note." not in client.get(base + "/audit").text


def test_assignment_requires_the_participant_whose_readiness_is_validated(workspace):
    client, factory, project_id = workspace
    user, path, transition, claim = generated_handover(client, project_id)
    post_ok(client, path + "/approve", {"note": "Manager reviewed handover scope."})
    team = client.get("/api/team", params={"project_id": project_id}).json()
    other = next(u for u in team if u["name"] == "Sam Rivera")
    assert (
        client.post(path + "/assign", json={"claim_id": claim["id"], "successor_id": other["id"]}).status_code
        == 422
    )


def test_employee_interview_is_pending_and_source_scope_is_inherited(workspace):
    client, factory, project_id = workspace
    login(client)
    base = f"/api/projects/{project_id}"
    post_ok(client, base + "/investigations", {})
    gap = next(g for g in client.get(base + "/gaps").json() if g["kind"] == "missing_procedure")
    login(client, "Alex Morgan")
    response = post_ok(
        client,
        base + "/gaps/" + gap["id"] + "/respond",
        {
            "answer": "Use the isolated canary test pipeline and inspect retry counters before requesting a release approval from Priya."
        },
    )
    assert response["status"] == "pending"
    assert response["data"]["employee_explanation"] is True
    assert response["evidence"][0]["source_kind"] == "interview"
    assert (
        client.post(
            base + "/claims/" + response["id"] + "/review",
            json={"action": "approve", "note": "Employee cannot approve authoritative knowledge."},
        ).status_code
        == 403
    )


def test_real_organisation_can_create_team_accounts_without_exposing_passwords(workspace):
    client, factory, project_id = workspace
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Org Administrator",
            "email": "newadmin@example.com",
            "password": "local-test-password-1234",
            "organisation": "Fresh Organisation",
        },
    )
    assert response.status_code == 201
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    project = post_ok(
        client, "/api/projects", {"name": "Fresh project", "description": "Authorised new project."}
    )
    password = "new-member-test-password-1234"
    member = post_ok(
        client,
        f"/api/projects/{project['id']}/members",
        {
            "name": "Incoming Engineer",
            "email": "incoming@example.com",
            "title": "Backend Engineer",
            "role": "incoming",
            "password": password,
        },
    )
    assert "password" not in member and "password_hash" not in member
    assert password not in json.dumps(client.get(f"/api/projects/{project['id']}/audit").json())
    response = client.post("/api/auth/login", json={"email": "incoming@example.com", "password": password})
    assert response.status_code == 200
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    assert project["id"] in {p["id"] for p in client.get("/api/projects").json()}
    assert (
        client.post(
            f"/api/projects/{project['id']}/members",
            json={
                "name": "Escalation Attempt",
                "email": "attempt@example.com",
                "title": "Manager",
                "role": "manager",
                "password": password,
            },
        ).status_code
        == 403
    )
