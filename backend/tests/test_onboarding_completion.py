from sqlalchemy import select
from test_round3 import ok, prepare, start, switch

from app import models as m


def test_membership_revocation_denies_all_project_boundaries_and_is_audited(workspace):
    client, factory, _ = workspace
    _, people, base = start(client)
    path, _ = prepare(client, base, people)
    incoming = switch(client, people, "Savinay")
    conv = ok(client.post(base + "/chat/conversations"))
    request = ok(
        client.post(
            base + "/access-requests",
            json={"purpose": "Need approved recovery evidence before taking ownership."},
        )
    )
    switch(client, people, "Rudransh")
    revoked = ok(
        client.post(
            base + "/members/" + incoming["id"] + "/revoke",
            json={"note": "Offboarding this controlled project member."},
        )
    )
    assert revoked["status"] == "revoked"
    assert not ok(client.get(path + "/readiness"))["ready"]
    report = ok(client.get(base + "/access-readiness"))[0]
    assert not report["membership_active"] and not report["ready"]
    assert (
        client.post(
            base + "/members/" + incoming["id"] + "/revoke",
            json={"note": "Replay membership removal request."},
        ).status_code
        == 404
    )
    with factory() as db:
        assert db.get(m.User, incoming["id"]).active
        assert db.get(m.AccessRequest, request["id"]).status == "revoked"
        assert db.scalar(
            select(m.Audit).where(
                m.Audit.action == "membership.revoked", m.Audit.resource_id == incoming["id"]
            )
        )
    switch(client, people, "Savinay")
    for suffix in (
        "/sources",
        "/claims",
        "/graph",
        "/transitions",
        "/access-readiness",
        "/chat/conversations/" + conv["id"],
    ):
        assert client.get(base + suffix).status_code == 404


def test_revocation_requires_admin_cannot_remove_self_or_cross_tenant(workspace):
    client, _, _ = workspace
    session, people, base = start(client)
    admin_id = session["user"]["id"]
    body = {"note": "Requested scoped project membership revocation."}
    assert client.post(base + "/members/" + admin_id + "/revoke", json=body).status_code == 409
    assert client.post(base + "/members/not-a-member/revoke", json=body).status_code == 404
    switch(client, people, "Gaurav")
    assert client.post(base + "/members/" + admin_id + "/revoke", json=body).status_code == 403


def test_access_readiness_withholds_hidden_titles_and_recovers_after_authorised_grant(workspace):
    client, factory, _ = workspace
    _, people, base = start(client)
    _, transition = prepare(client, base, people)
    ref = transition["report"]["knowledge"][0]["evidence"][0]
    admin = next(p for p in people if p["name"] == "Rudransh")
    with factory() as db:
        db.get(m.Source, ref["source_id"]).acl = [admin["id"]]
        db.commit()
    coordinator = ok(client.get(base + "/access-readiness"))[0]
    assert coordinator["missing_items"] > 0 and coordinator["missing_titles"]
    switch(client, people, "Savinay")
    incoming = ok(client.get(base + "/access-readiness"))[0]
    assert incoming["missing_items"] > 0 and not incoming["missing_titles"]
    item = ok(
        client.post(
            base + "/access-requests",
            json={"purpose": "Need approved handover knowledge for assigned responsibilities."},
        )
    )
    switch(client, people, "Rudransh")
    ok(
        client.post(
            base + "/access-requests/" + item["id"] + "/review",
            json={
                "action": "approve",
                "source_id": ref["source_id"],
                "note": "Approved scoped knowledge access for this handover.",
            },
        )
    )
    assert ok(client.get(base + "/access-readiness"))[0]["ready"]
