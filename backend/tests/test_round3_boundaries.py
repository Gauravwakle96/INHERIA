from conftest import login
from sqlalchemy import select
from test_round3 import confirm_prerequisites, ok, pass_all, prepare, start, submit_all, switch

from app import models as m


def test_existing_account_join_requires_auth_and_preserves_role(workspace):
    client, factory, pid = workspace
    admin = login(client)
    with factory() as db:
        person = m.User(
            org_id=admin["org_id"],
            name="Existing Engineer",
            email="existing@example.com",
            title="Engineer",
            role="employee",
            password_hash="unchanged",
        )
        db.add(person)
        db.commit()
        uid = person.id
    invite = ok(
        client.post(
            f"/api/projects/{pid}/invitations",
            json={
                "name": "Existing Engineer",
                "email": "existing@example.com",
                "title": "Lead",
                "role": "lead",
            },
        )
    )
    token = invite["join_path"].split("token=")[1]
    assert client.post("/api/auth/invitation/accept", json={"token": token}).status_code == 403
    with factory() as db:
        assert db.get(m.Invitation, invite["id"]).status == "pending"
    from fastapi import Response

    from app.security import create_session

    with factory() as db:
        response = Response()
        session = create_session(db, db.get(m.User, uid), response)
    from http.cookies import SimpleCookie

    cookie = SimpleCookie(response.headers["set-cookie"])
    client.cookies.set("inheria_session", cookie["inheria_session"].value)
    client.headers["X-CSRF-Token"] = session["csrf_token"]
    joined = ok(client.post("/api/auth/invitation/accept", json={"token": token}))
    assert joined["user"]["role"] == "employee"
    with factory() as db:
        assert db.get(m.User, uid).password_hash == "unchanged"
        assert (
            db.scalar(
                select(m.Membership).where(m.Membership.user_id == uid, m.Membership.project_id == pid)
            ).role
            == "employee"
        )


def test_prerequisite_details_are_withheld_after_source_acl_change(workspace):
    client, factory, _ = workspace
    _, people, base = start(client)
    path, transition = prepare(client, base, people)
    confirm_prerequisites(client, path, transition)
    with factory() as db:
        t = db.get(m.Transition, transition["id"])
        item = t.report["prerequisites"][0]
        item["note"] = "restricted-review-canary"
        t.report = {**t.report, "prerequisites": [item]}
        source = db.get(m.Source, next(iter(item["source_versions"])))
        source.acl = [next(p["id"] for p in people if p["name"] == "Rudransh")]
        db.commit()
    switch(client, people, "Savinay")
    assert "restricted-review-canary" not in client.get(base + "/transitions").text
    readiness = client.get(path + "/readiness")
    assert "restricted-review-canary" not in readiness.text
    assert not readiness.json()["ready"]


def test_manager_cannot_close_when_successor_loses_source_access(workspace):
    client, factory, _ = workspace
    _, people, base = start(client)
    path, transition = prepare(client, base, people)
    switch(client, people, "Savinay")
    submit_all(client, base, transition)
    switch(client, people, "Rudransh")
    pass_all(client, base, transition)
    confirm_prerequisites(client, path, transition)
    assert ok(client.get(path + "/readiness"))["ready"]
    with factory() as db:
        source_id = transition["report"]["knowledge"][0]["evidence"][0]["source_id"]
        db.get(m.Source, source_id).acl = [next(p["id"] for p in people if p["name"] == "Rudransh")]
        db.commit()
    assert not ok(client.get(path + "/readiness"))["ready"]
    assert client.post(path + "/close").status_code == 409
