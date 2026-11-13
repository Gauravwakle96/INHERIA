import json
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import select
from test_round3 import ok, prepare, start, switch

from app import chat_provider
from app import models as m


def test_document_access_changes_update_readiness_without_erasing_knowledge(workspace):
    client, _, _ = workspace
    _, people, base = start(client)
    _, transition = prepare(client, base, people)
    source = transition["report"]["knowledge"][0]["evidence"][0]["source_id"]
    admin = next(p for p in people if p["name"] == "Rudransh")
    incoming = next(p for p in people if p["name"] == "Savinay")
    endpoint = base + "/sources/" + source + "/access"
    ok(
        client.post(
            endpoint,
            json={
                "allowed_user_ids": [admin["id"]],
                "note": "Restricted source pending authorised access review.",
            },
        )
    )
    assert ok(client.get(endpoint))["allowed_user_ids"] == [admin["id"]]
    assert not ok(client.get(base + "/access-readiness"))[0]["ready"]
    switch(client, people, "Savinay")
    assert client.get(endpoint).status_code == 403
    assert client.get(base + "/evidence/" + source).status_code == 404
    switch(client, people, "Rudransh")
    assert (
        client.post(
            endpoint,
            json={"allowed_user_ids": [incoming["id"]], "note": "Attempt to remove the current reviewer."},
        ).status_code
        == 422
    )
    ok(
        client.post(
            endpoint,
            json={
                "allowed_user_ids": [admin["id"], incoming["id"]],
                "note": "Authorised incoming employee knowledge access restored.",
            },
        )
    )
    assert ok(client.get(base + "/access-readiness"))[0]["ready"]


def test_member_revocation_never_widens_a_last_reader_acl(workspace):
    client, factory, _ = workspace
    _, people, base = start(client)
    incoming = next(p for p in people if p["name"] == "Savinay")
    with factory() as db:
        source = m.Source(
            org_id=incoming["org_id"],
            project_id=base.rsplit("/", 1)[1],
            name="Last reader only",
            kind="markdown",
            acl=[incoming["id"]],
        )
        db.add(source)
        db.commit()
        sid = source.id
    ok(
        client.post(
            base + "/members/" + incoming["id"] + "/revoke",
            json={"note": "Remove member with private last-reader source."},
        )
    )
    with factory() as db:
        assert db.get(m.Source, sid).status == "revoked"
        assert db.get(m.Source, sid).acl == [incoming["id"]]
        assert db.scalar(
            select(m.Audit).where(m.Audit.resource_id == sid, m.Audit.action == "source.reader_revoked")
        )
    assert sid not in {source["id"] for source in ok(client.get(base + "/sources"))}


def test_upstream_error_in_http_200_is_safe_provider_failure(monkeypatch):
    real = httpx.Client
    monkeypatch.setattr(
        chat_provider.httpx,
        "Client",
        lambda **kw: real(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200, json={"error": {"type": "upstream_error", "message": "sensitive upstream payload"}}
                )
            ),
            **kw,
        ),
    )
    config = SimpleNamespace(
        base_url=chat_provider.BYNARA_BASE, model="agnes-2.5-flash", protocol="chat_completions"
    )
    with pytest.raises(chat_provider.ProviderError, match="upstream error") as error:
        chat_provider.call_provider(config, "test-fixture", "Hello", "low", {}, [])
    assert "sensitive" not in str(error.value)
    assert "sensitive" not in json.dumps({"error": str(error.value)})


@pytest.mark.parametrize("change", ["acl", "revoke", "delete", "cycle"])
def test_derived_source_respects_parent_acl_after_permission_change(workspace, change):
    from app.security import can_read_source, visible_sources

    client, factory, _ = workspace
    _, people, base = start(client)
    with factory() as db:
        incoming = db.get(m.User, next(p["id"] for p in people if p["name"] == "Savinay"))
        admin_id = next(p["id"] for p in people if p["name"] == "Rudransh")
        pid = base.rsplit("/", 1)[1]
        parent = m.Source(org_id=incoming.org_id, project_id=pid, name="Original evidence", kind="markdown")
        db.add(parent)
        db.flush()
        derived = m.Source(
            org_id=incoming.org_id,
            project_id=pid,
            name="Derived ownership text",
            kind="ownership_transfer",
            source_metadata={"lineage_source_ids": [parent.id]},
        )
        db.add(derived)
        db.commit()
        assert can_read_source(db, incoming, derived)
        if change == "acl":
            parent.acl = [admin_id]
        elif change == "revoke":
            parent.status = "revoked"
        elif change == "delete":
            db.delete(parent)
        else:
            parent.source_metadata = {"lineage_source_ids": [derived.id]}
        db.commit()
        assert not can_read_source(db, incoming, derived)
        assert derived.id not in {source.id for source in visible_sources(db, incoming, pid)}


def test_parent_change_traces_and_invalidates_transitive_interview_evidence(workspace):
    from app.impact import source_impact
    from app.ingestion import invalidate_source

    client, factory, _ = workspace
    _, people, base = start(client)
    with factory() as db:
        actor = db.get(m.User, next(p["id"] for p in people if p["name"] == "Rudransh"))
        pid = base.rsplit("/", 1)[1]
        parent = m.Source(
            org_id=actor.org_id, project_id=pid, name="Primary recovery record", kind="markdown"
        )
        db.add(parent)
        db.flush()
        derived = m.Source(
            org_id=actor.org_id,
            project_id=pid,
            name="Interview detail",
            kind="interview",
            source_metadata={"lineage_source_ids": [parent.id]},
        )
        db.add(derived)
        db.flush()
        second = m.Source(
            org_id=actor.org_id,
            project_id=pid,
            name="Derived explanation",
            kind="interview",
            source_metadata={"lineage_source_ids": [derived.id]},
        )
        db.add(second)
        db.flush()
        quote = "Recovery explanation based on the primary record."
        chunk = m.Chunk(org_id=actor.org_id, project_id=pid, source_id=second.id, text=quote)
        claim = m.Claim(
            org_id=actor.org_id,
            project_id=pid,
            kind="procedure",
            title="Recovery explanation",
            summary=quote,
            status="verified",
            verified_by=actor.id,
        )
        db.add_all([chunk, claim])
        db.flush()
        db.add(
            m.Evidence(
                org_id=actor.org_id,
                project_id=pid,
                source_id=second.id,
                chunk_id=chunk.id,
                claim_id=claim.id,
                source_version=1,
                quote=quote,
            )
        )
        transition = m.Transition(
            org_id=actor.org_id,
            project_id=pid,
            departing_id=actor.id,
            successor_id=actor.id,
            departure_date="2026-12-01",
            title="Lineage fixture",
            report={"source_ids": [second.id]},
        )
        db.add(transition)
        db.flush()
        exercise = m.Exercise(
            org_id=actor.org_id,
            project_id=pid,
            transition_id=transition.id,
            title="Recovery review",
            prompt="Review recovery evidence",
            expected_source_ids=[second.id],
            status="passed",
        )
        db.add(exercise)
        db.commit()
        impact = source_impact(db, actor, pid, parent.id)
        assert claim.id in {c["id"] for c in impact["claims"]}
        assert transition.id in {t["id"] for t in impact["transitions"]}
        assert exercise.id in {e["id"] for e in impact["exercises"]}
        assert invalidate_source(db, parent) == 1
        db.commit()
        assert claim.status == "invalidated" and claim.verified_by is None
        assert exercise.status == "needs_revision"
        assert transition.report["requires_revalidation"]
