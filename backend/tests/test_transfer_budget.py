"""Transfer reductions preserve exact evidence, tenant boundaries and freshness."""

from uuid import uuid4

from conftest import login
from sqlalchemy import event, select
from test_postgres_concurrency import postgres_factory as postgres_factory

from app import models as m
from app.intelligence import citations, current_claims


def check_evidence_transfer(factory):
    with factory() as db:
        org = m.Organisation(name="Transfer QA")
        db.add(org)
        db.flush()
        user = m.User(
            org_id=org.id,
            name="Reviewer",
            role="admin",
            email=f"{uuid4().hex}@qa.example",
            password_hash="Unused test fixture",
        )
        project = m.Project(org_id=org.id, name="Evidence transfer QA")
        db.add_all([user, project])
        db.flush()
        db.add(m.Membership(project_id=project.id, user_id=user.id, role="admin"))
        source = m.Source(org_id=org.id, project_id=project.id, name="Large source", kind="txt")
        db.add(source)
        db.flush()
        quote = "Recovery owner: Savinay — 100% integrity; literal _ and % are required."
        chunk = m.Chunk(
            org_id=org.id,
            project_id=project.id,
            source_id=source.id,
            text=("Unrelated background.\n" * 10_000) + quote,
            locator="Recovery section",
        )
        claim = m.Claim(
            org_id=org.id,
            project_id=project.id,
            kind="responsibility",
            title="Recovery ownership",
            summary=quote,
        )
        db.add_all([chunk, claim])
        db.flush()
        ref = m.Evidence(
            org_id=org.id,
            project_id=project.id,
            source_id=source.id,
            source_version=1,
            chunk_id=chunk.id,
            claim_id=claim.id,
            quote=quote,
        )
        db.add(ref)
        db.commit()
        uid, pid, cid, rid = user.id, project.id, claim.id, ref.id
        original_bytes = len(chunk.text.encode())

    with factory() as db:
        user = db.get(m.User, uid)
        statements = []

        def record(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)

        event.listen(db.get_bind(), "before_cursor_execute", record)
        try:
            claims = current_claims(db, user, pid)
            assert [c.id for c in claims] == [cid]
            assert citations(db, user, claims[0])[0]["quote"] == quote
            assert citations(db, user, claims[0])[0]["locator"] == "Recovery section"
            assert not any(isinstance(item, m.Chunk) for item in db.identity_map.values())
            assert original_bytes > 200_000
            # Metadata and the exact citation remain available; no full text is
            # selected into the result set. Quote validation executes in SQL.
            assert any("strpos(" in statement or "instr(" in statement for statement in statements)
            before = len(statements)
            current_claims(db, user, pid)
            assert not any("FROM claims" in statement for statement in statements[before:])
            ref = db.get(m.Evidence, rid)
            ref.quote = "Recovery owner: Savinay — 100X integrity; literal _ and % are required."
            db.flush()
            assert current_claims(db, user, pid) == []  # percent is literal, never SQL wildcard
            ref.quote = quote
            db.flush()
            assert current_claims(db, user, pid)
            source = db.get(m.Source, ref.source_id)
            source.version = 2
            db.flush()
            assert current_claims(db, user, pid) == []
        finally:
            event.remove(db.get_bind(), "before_cursor_execute", record)


def test_sqlite_checks_quotes_without_returning_source_text(workspace):
    check_evidence_transfer(workspace[1])


def test_pg_checks_quotes_without_returning_source_text(postgres_factory):
    check_evidence_transfer(postgres_factory)


def test_activity_status_is_small_role_scoped_and_project_authorised(workspace):
    client, factory, pid = workspace
    user = login(client)
    with factory() as db:
        db.add(
            m.Investigation(
                org_id=user["org_id"],
                project_id=pid,
                created_by=user["id"],
                status="running",
                report={"findings": ["large historical report"]},
            )
        )
        db.add(
            m.Investigation(org_id=user["org_id"], project_id=pid, created_by=user["id"], status="completed")
        )
        db.add(
            m.Job(
                org_id=user["org_id"], project_id=pid, requested_by=user["id"], kind="sync", status="queued"
            )
        )
        db.commit()
    response = client.get(f"/api/projects/{pid}/activity-status")
    assert response.status_code == 200
    assert {item["kind"] for item in response.json()} == {"investigation", "sync"}
    assert all(set(item) == {"id", "kind", "status"} for item in response.json())
    login(client, "Jordan Lee")
    assert {item["kind"] for item in client.get(f"/api/projects/{pid}/activity-status").json()} == {
        "investigation"
    }
    with factory() as db:
        other = m.Project(org_id=user["org_id"], name="Another project")
        db.add(other)
        db.commit()
        other_id = other.id
    assert client.get(f"/api/projects/{other_id}/activity-status").status_code == 404
    with factory() as db:
        for job in db.scalars(select(m.Investigation).where(m.Investigation.project_id == pid)):
            job.status = "failed"
        db.commit()
    assert client.get(f"/api/projects/{pid}/activity-status").json() == []
