from sqlalchemy import select

from app import models as m


def test_completed_account_copy_has_evidence_and_isolated_roles(workspace):
    client, factory, private_project = workspace
    response = client.post("/api/auth/judge-demo/start", json={"mode": "completed"})
    assert response.status_code == 201, response.text
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    project = client.get("/api/projects").json()[0]
    pid = project["id"]
    assert pid != private_project
    base = f"/api/projects/{pid}"
    assert len(client.get(base + "/sources").json()) == 51
    assert len(client.get(base + "/graph").json()["edges"]) > 50
    summary = client.get(base + "/continuity-summary").json()
    assert summary["completion"]["accepted"] == 8
    assert summary["completion"]["validated"] == 11
    assert summary["completion"]["current"]
    before = len(client.get(base + "/claims").json())
    assert client.post(base + "/investigations", json={"focus": ""}).status_code == 202
    assert len(client.get(base + "/claims").json()) == before
    people = client.get("/api/auth/judge-demo/people").json()
    assert {p["name"] for p in people} == {"Gaurav", "Savinay", "Rudransh"}
    for person in people:
        switch = client.post("/api/auth/judge-demo/switch", json={"user_id": person["id"]})
        assert switch.status_code == 200
        client.headers["X-CSRF-Token"] = switch.json()["csrf_token"]
        assert client.get(base + "/continuity-summary").json()["completion"]["current"]
        assert client.get(f"/api/projects/{private_project}/sources").status_code == 404
    with factory() as db:
        org_id = db.get(m.Project, pid).org_id
        assert db.scalar(select(m.AIConfiguration).where(m.AIConfiguration.org_id == org_id)) is None
        assert db.scalar(select(m.Conversation).where(m.Conversation.project_id == pid)) is None
        private_counts = db.query(m.Source).filter_by(project_id=private_project).count()
    second = client.post("/api/auth/judge-demo/start", json={"mode": "completed"})
    assert second.status_code == 201
    client.headers["X-CSRF-Token"] = second.json()["csrf_token"]
    assert client.get("/api/projects").json()[0]["id"] != pid
    assert client.get(base + "/sources").status_code == 404
    with factory() as db:
        assert db.query(m.Source).filter_by(project_id=private_project).count() == private_counts


def test_unknown_demo_mode_is_rejected(workspace):
    client, _, _ = workspace
    assert client.post("/api/auth/judge-demo/start", json={"mode": "private-account"}).status_code == 422
