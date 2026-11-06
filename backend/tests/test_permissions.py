import json

from conftest import login
from sqlalchemy import select

from app import models as m
from app.intelligence import current_claims, reconstruct_project


def test_restricted_source_never_enters_other_users_claims_graph_answers_or_handover(workspace):
    client, factory, project_id = workspace
    manager = login(client)
    base = f"/api/projects/{project_id}"
    text = "Responsibility: Restricted payment signing duty\nOwner: Alex Morgan\nSystem: restricted-signing-service\nCritical: true"
    response = client.post(
        base + "/sources/upload",
        files={"file": ("restricted.md", text.encode(), "text/markdown")},
        data={"allowed_user_ids": json.dumps([manager["id"]])},
    )
    assert response.status_code == 201, response.text
    source_id = response.json()["source"]["id"]
    with factory() as db:
        actor = db.get(m.User, manager["id"])
        reconstruct_project(db, actor, project_id)
        db.commit()
    claim = next(
        c for c in client.get(base + "/claims").json() if c["title"] == "Restricted payment signing duty"
    )
    assert (
        client.post(
            base + "/claims/" + claim["id"] + "/review",
            json={"action": "approve", "note": "Confirmed restricted source statement."},
        ).status_code
        == 200
    )
    login(client, "Jordan Lee")
    for endpoint in ["/claims", "/graph", "/investigations", "/gaps", "/overview", "/transitions"]:
        response = client.get(base + endpoint)
        assert response.status_code == 200
        assert "Restricted payment signing duty" not in response.text
        assert source_id not in response.text
    assert client.get(base + "/evidence/" + source_id).status_code == 404
    answer = client.post(
        base + "/successor/ask", json={"question": "Who owns restricted-signing-service?"}
    ).json()
    assert not answer["known"] and not answer["citations"]


def test_cross_tenant_project_and_source_access_is_denied(workspace):
    client, factory, project_id = workspace
    login(client)
    source_id = client.get(f"/api/projects/{project_id}/sources").json()[0]["id"]
    response = client.post(
        "/api/auth/register",
        json={
            "name": "External Admin",
            "email": "external@example.com",
            "password": "only-test-password-123",
            "organisation": "External tenant",
        },
    )
    assert response.status_code == 201
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    for endpoint in ["/claims", "/graph", "/overview", "/sources", "/transitions", "/evidence/" + source_id]:
        assert client.get(f"/api/projects/{project_id}" + endpoint).status_code == 404
    assert client.post(f"/api/projects/{project_id}/investigations", json={}).status_code == 404


def test_revocation_invalidates_verified_answers_and_deleted_text_is_erased(workspace):
    client, factory, project_id = workspace
    login(client)
    base = f"/api/projects/{project_id}"
    claim = client.get(base + "/claims", params={"kind": "procedure"}).json()[0]
    source_id = claim["evidence"][0]["source_id"]
    assert (
        client.post(
            base + "/claims/" + claim["id"] + "/review",
            json={"action": "approve", "note": "Procedure source verified."},
        ).status_code
        == 200
    )
    assert client.post(base + "/sources/" + source_id + "/revoke").status_code == 200
    assert claim["id"] not in {c["id"] for c in client.get(base + "/claims").json()}
    assert client.get(base + "/evidence/" + source_id).status_code == 404
    assert client.delete(base + "/sources/" + source_id).status_code == 200
    with factory() as db:
        assert db.get(m.Source, source_id) is None
        assert not list(db.scalars(select(m.Chunk).where(m.Chunk.source_id == source_id)))
        stored = db.get(m.Claim, claim["id"])
        assert stored.summary == "Source evidence was deleted."
        assert not stored.data


def test_changed_source_version_removes_claim_from_all_current_views(workspace):
    client, factory, project_id = workspace
    login(client)
    base = f"/api/projects/{project_id}"
    claim = client.get(base + "/claims").json()[0]
    source_id = claim["evidence"][0]["source_id"]
    with factory() as db:
        source = db.get(m.Source, source_id)
        source.version += 1
        db.commit()
    assert claim["id"] not in {c["id"] for c in client.get(base + "/claims").json()}
    assert claim["id"] not in {n["id"] for n in client.get(base + "/graph").json()["nodes"]}


def test_validation_and_feedback_reject_sensitive_content_without_echo(workspace):
    client, factory, project_id = workspace
    login(client)
    base = f"/api/projects/{project_id}"
    sensitive = "password=" + "fictional-sensitive-value-12345"
    response = client.post(base + "/successor/ask", json={"question": sensitive})
    assert response.status_code == 422
    assert sensitive not in response.text
    claim = client.get(base + "/claims").json()[0]
    response = client.post(
        base + "/claims/" + claim["id"] + "/review",
        json={
            "action": "approve",
            "note": "Attempted sensitive component submission.",
            "component": sensitive,
        },
    )
    assert response.status_code == 422
    assert sensitive not in response.text
    assert (
        next(c for c in client.get(base + "/claims").json() if c["id"] == claim["id"])["status"] == "pending"
    )
    response = client.post(
        base + "/connections/github", json={"repository": "fastapi/fastapi", "token": "z" * 301}
    )
    assert response.status_code == 422
    assert "z" * 301 not in response.text


def test_mixed_source_acl_claim_is_hidden_entirely(workspace):
    client, factory, project_id = workspace
    manager = login(client)
    with factory() as db:
        actor = db.get(m.User, manager["id"])
        claim = current_claims(db, actor, project_id)[0]
        source = m.Source(
            org_id=actor.org_id,
            project_id=project_id,
            name="Restricted corroboration",
            kind="txt",
            acl=[actor.id],
        )
        db.add(source)
        db.flush()
        chunk = m.Chunk(
            org_id=actor.org_id,
            project_id=project_id,
            source_id=source.id,
            source_version=1,
            ordinal=0,
            text="Restricted corroborating excerpt for permission testing.",
            locator="Line 1",
        )
        db.add(chunk)
        db.flush()
        db.add(
            m.Evidence(
                org_id=actor.org_id,
                project_id=project_id,
                claim_id=claim.id,
                chunk_id=chunk.id,
                source_id=source.id,
                source_version=1,
                quote=chunk.text,
            )
        )
        claim_id = claim.id
        db.commit()
    login(client, "Jordan Lee")
    assert claim_id not in {c["id"] for c in client.get(f"/api/projects/{project_id}/claims").json()}
