"""Opt-in real PostgreSQL transactions; isolated QA schema, never production data.

Set INHERIA_TEST_POSTGRES_URL to a loopback database whose name ends in _qa.
The ordinary SQLite suite skips these tests. No locks or timing are mocked.
"""

import hashlib
import os
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi import HTTPException, Response
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from app import models as m
from app import schemas as s
from app.ingestion import ingest_document, invalidate_source
from app.routers import onboarding, sources, workspace
from app.transfer import generate_exercises, generate_handover, get_transition


@pytest.fixture(scope="module")
def postgres_factory():
    url = os.environ.get("INHERIA_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Real PostgreSQL QA is opt-in; no database URL supplied.")
    parsed = make_url(url)
    assert parsed.get_backend_name() == "postgresql"
    assert parsed.host in {"localhost", "127.0.0.1", "::1"}
    assert parsed.database and parsed.database.endswith("_qa"), "Use an owned local QA database."
    schema = "qa_" + uuid4().hex
    administrative = create_engine(url, connect_args={"connect_timeout": 5})
    with administrative.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(
        url,
        pool_size=8,
        max_overflow=2,
        connect_args={
            "connect_timeout": 5,
            "options": f"-c search_path={schema} -c lock_timeout=10000 -c statement_timeout=15000",
        },
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    m.Base.metadata.create_all(engine)
    try:
        yield factory
    finally:
        engine.dispose()
        # The generated schema is the only target; never drop any existing table/schema.
        with administrative.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        administrative.dispose()


@pytest.fixture
def case(postgres_factory):
    factory = postgres_factory
    with factory() as db:
        org = m.Organisation(name="PostgreSQL transaction QA")
        db.add(org)
        db.flush()
        people = {}
        for name, role in (("Coordinator", "admin"), ("Departing", "employee"), ("Incoming", "incoming")):
            person = m.User(
                org_id=org.id,
                name=name,
                role=role,
                email=f"{uuid4().hex}@postgres-qa.example",
                password_hash="Unused direct-service test account; no login credential",
            )
            db.add(person)
            people[name] = person
        db.flush()
        project = m.Project(org_id=org.id, name="Isolated concurrency case")
        db.add(project)
        db.flush()
        for person in people.values():
            db.add(m.Membership(project_id=project.id, user_id=person.id, role=person.role))
        db.flush()
        claims = []
        for kind, title, body in (
            (
                "responsibility",
                "Release ownership",
                "Responsibility: Release ownership\nOwner: Departing\nSystem: release-pipeline\nBackup: Coordinator",
            ),
            (
                "procedure",
                "Staging release checks",
                "Procedure: Staging release checks\nSystem: release-pipeline\nCheck approval, schema compatibility, staging scope and application health before release.",
            ),
        ):
            source, _ = ingest_document(
                db, people["Coordinator"], project.id, filename=kind + ".md", content=body.encode()
            )
            chunk = db.scalar(select(m.Chunk).where(m.Chunk.source_id == source.id))
            claim = m.Claim(
                org_id=org.id,
                project_id=project.id,
                kind=kind,
                title=title,
                summary=body,
                status="verified",
                data={"owner_id": people["Departing"].id, "component": "release-pipeline"},
                created_by=people["Departing"].id,
                verified_by=people["Coordinator"].id,
                verified_at=m.utcnow(),
            )
            db.add(claim)
            db.flush()
            db.add(
                m.Evidence(
                    org_id=org.id,
                    project_id=project.id,
                    source_id=source.id,
                    source_version=source.version,
                    chunk_id=chunk.id,
                    claim_id=claim.id,
                    quote=chunk.text,
                )
            )
            claims.append((claim.id, source.id))
        transition = m.Transition(
            org_id=org.id,
            project_id=project.id,
            departing_id=people["Departing"].id,
            successor_id=people["Incoming"].id,
            title="Concurrent handover QA",
            departure_date=(m.utcnow() + timedelta(days=7)).date().isoformat(),
        )
        db.add(transition)
        db.flush()
        generate_handover(db, people["Coordinator"], transition)
        db.commit()
        result = {
            "factory": factory,
            "project": project.id,
            "transition": transition.id,
            "admin": people["Coordinator"].id,
            "incoming": people["Incoming"].id,
            "departing": people["Departing"].id,
            "claim": claims[0][0],
            "source": claims[0][1],
        }
        workspace.approve(
            project.id,
            transition.id,
            s.Note(note="Reviewed exact isolated test evidence."),
            db,
            people["Coordinator"],
        )
    yield result


def call(case, actor, function, *args):
    with case["factory"]() as db:
        try:
            result = function(*args, db, db.get(m.User, case[actor]))
            return {"status": 200, "result": result}
        except HTTPException as exc:
            db.rollback()
            return {"status": exc.status_code, "detail": exc.detail}


def assignment(case):
    result = call(
        case,
        "admin",
        workspace.assign,
        case["project"],
        case["transition"],
        s.Assignment(
            claim_id=case["claim"],
            successor_id=case["incoming"],
            backup_id=case["admin"],
        ),
    )
    assert result["status"] == 200
    return result["result"]["id"]


def ready_case(case):
    transfer = assignment(case)
    assert (
        call(
            case,
            "incoming",
            workspace.respond,
            case["project"],
            transfer,
            s.TransferResponse(
                action="accept",
                note="Reviewed the assigned evidence and accepted ownership.",
            ),
        )["status"]
        == 200
    )
    with case["factory"]() as db:
        t = get_transition(db, db.get(m.User, case["admin"]), case["project"], case["transition"], lock=True)
        generate_exercises(db, db.get(m.User, case["admin"]), t)
        db.commit()
        tasks = list(db.scalars(select(m.Exercise).where(m.Exercise.transition_id == t.id)))
        refs = list(db.scalars(select(m.Evidence.id).where(m.Evidence.project_id == case["project"])))
        for task in tasks:
            body = s.Submission(
                answer="Located current staging instructions, approval conditions and safe escalation checks.",
                evidence_ids=refs,
                escalation="Escalate incomplete recovery evidence to the authorised supervisor before execution.",
            )
            assert call(case, "incoming", workspace.submit, case["project"], task.id, body)["status"] == 200
            assert (
                call(
                    case,
                    "admin",
                    workspace.assess,
                    case["project"],
                    task.id,
                    s.Assessment(
                        action="pass",
                        note="Reviewed each cited staging walkthrough criterion.",
                        criteria_passed=[True] * len(task.criteria),
                    ),
                )["status"]
                == 200
            )


def simultaneous(case, *operations):
    """Hold the real project lock until both request transactions are waiting."""
    factory = case["factory"]
    barrier = Barrier(len(operations))
    with factory() as holder, ThreadPoolExecutor(max_workers=len(operations)) as pool:
        holder.execute(select(m.Project).where(m.Project.id == case["project"]).with_for_update())

        def execute(operation):
            barrier.wait(timeout=10)
            return operation()

        futures = [pool.submit(execute, operation) for operation in operations]
        deadline = time.monotonic() + 8
        waiting = 0
        while waiting < len(operations) and time.monotonic() < deadline:
            with factory() as monitor:
                waiting = monitor.scalar(
                    text(
                        "SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock'"
                    )
                )
            time.sleep(0.02)
        holder.commit()
        assert waiting >= len(operations), "Both real request transactions must overlap at the lock."
        return [future.result(timeout=20) for future in futures]


def audit_count(case, action):
    with case["factory"]() as db:
        return db.scalar(
            select(func.count())
            .select_from(m.Audit)
            .where(m.Audit.project_id == case["project"], m.Audit.action == action)
        )


def test_pg_duplicate_acceptance_is_one_record_and_one_audit(case):
    transfer = assignment(case)

    def respond():
        return call(
            case,
            "incoming",
            workspace.respond,
            case["project"],
            transfer,
            s.TransferResponse(action="accept", note="Reviewed this responsibility and accepted ownership."),
        )

    results = simultaneous(case, respond, respond)
    assert [r["status"] for r in results] == [200, 200]
    assert results[0]["result"] == results[1]["result"]
    assert audit_count(case, "responsibility.accepted") == 1


def test_pg_duplicate_assignment_preserves_single_transfer(case):
    body = s.Assignment(claim_id=case["claim"], successor_id=case["incoming"], backup_id=case["admin"])
    results = simultaneous(
        case, *[lambda: call(case, "admin", workspace.assign, case["project"], case["transition"], body)] * 2
    )
    assert [r["status"] for r in results] == [200, 200]
    assert results[0]["result"]["id"] == results[1]["result"]["id"]


def test_pg_duplicate_close_creates_ownership_once(case):
    ready_case(case)
    results = simultaneous(
        case, *[lambda: call(case, "admin", workspace.close, case["project"], case["transition"])] * 2
    )
    assert [r["status"] for r in results] == [200, 200]
    assert audit_count(case, "transition.closed") == 1
    assert audit_count(case, "ownership.transferred") == 1


def test_pg_duplicate_claim_approval_has_one_winner(case):
    with case["factory"]() as db:
        db.get(m.Claim, case["claim"]).status = "pending"
        db.commit()
    body = s.Review(action="approve", note="Reviewed the pending candidate's exact source.")
    results = simultaneous(
        case, *[lambda: call(case, "admin", workspace.review_claim, case["project"], case["claim"], body)] * 2
    )
    assert sorted(r["status"] for r in results) == [200, 409]
    assert audit_count(case, "claim.approve") == 1


def test_pg_concurrent_prerequisite_edits_do_not_lose_json_updates(case):
    with case["factory"]() as db:
        t = db.get(m.Transition, case["transition"])
        t.report = {
            **t.report,
            "prerequisites": [
                {"id": "first", "title": "First check", "required": False, "status": "pending"},
                {"id": "second", "title": "Second check", "required": False, "status": "pending"},
            ],
        }
        db.commit()
    body = workspace.PrerequisiteReview(
        status="pending", note="Independent readiness follow-up remains open."
    )
    operations = [
        lambda name=name: call(
            case, "admin", workspace.review_prerequisite, case["project"], case["transition"], name, body
        )
        for name in ("first", "second")
    ]
    assert [r["status"] for r in simultaneous(case, *operations)] == [200, 200]
    with case["factory"]() as db:
        checks = db.get(m.Transition, case["transition"]).report["prerequisites"]
        assert all(item["note"] == body.note for item in checks)
        assert all(len(item["history"]) == 1 for item in checks)


def blocked_then_change(case, operation, change):
    """Commit a source/access change while a preloaded request waits for its lock."""
    factory = case["factory"]
    with factory() as holder, ThreadPoolExecutor(max_workers=1) as pool:
        holder.execute(select(m.Project).where(m.Project.id == case["project"]).with_for_update())
        future = pool.submit(operation)
        deadline = time.monotonic() + 8
        waiting = False
        while not waiting and time.monotonic() < deadline:
            with factory() as monitor:
                waiting = bool(
                    monitor.scalar(
                        text(
                            "SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock'"
                        )
                    )
                )
            time.sleep(0.02)
        assert waiting, "Request must actually be blocked behind the project lock."
        change(holder)
        holder.commit()
        return future.result(timeout=20)


def test_pg_source_revocation_while_acceptance_waits_is_denied(case):
    transfer = assignment(case)

    def revoke(db):
        source = db.get(m.Source, case["source"])
        invalidate_source(db, source)
        source.status = "revoked"

    result = blocked_then_change(
        case,
        lambda: call(
            case,
            "incoming",
            workspace.respond,
            case["project"],
            transfer,
            s.TransferResponse(action="accept", note="Cannot accept revoked responsibility evidence."),
        ),
        revoke,
    )
    assert result["status"] in {404, 409}
    assert audit_count(case, "responsibility.accepted") == 0


def test_pg_source_change_while_closure_waits_blocks_ownership(case):
    ready_case(case)

    def replace(db):
        source = db.get(m.Source, case["source"])
        invalidate_source(db, source)
        source.version += 1

    result = blocked_then_change(
        case, lambda: call(case, "admin", workspace.close, case["project"], case["transition"]), replace
    )
    assert result["status"] == 409
    assert audit_count(case, "ownership.transferred") == 0


def test_pg_recipient_acl_loss_while_closure_waits_blocks_ownership(case):
    ready_case(case)
    result = blocked_then_change(
        case,
        lambda: call(case, "admin", workspace.close, case["project"], case["transition"]),
        lambda db: sources.update_source_access(
            case["project"],
            case["source"],
            sources.SourceAccessBody(
                allowed_user_ids=[case["admin"]], note="Remove incoming access while closure is waiting."
            ),
            db,
            db.get(m.User, case["admin"]),
        ),
    )
    assert result["status"] == 409
    assert audit_count(case, "ownership.transferred") == 0


def test_pg_membership_revocation_cannot_be_undone_by_waiting_acl_edit(case):
    body = sources.SourceAccessBody(
        allowed_user_ids=[case["admin"], case["incoming"]],
        note="Apply a stale edit to the document reader list.",
    )
    result = blocked_then_change(
        case,
        lambda: call(case, "admin", sources.update_source_access, case["project"], case["source"], body),
        lambda db: onboarding.revoke_member(
            case["project"],
            case["incoming"],
            onboarding.RevokeMemberBody(note="Revoke the incoming member before stale ACL edit."),
            db,
            db.get(m.User, case["admin"]),
        ),
    )
    assert result["status"] == 422
    with case["factory"]() as db:
        assert case["incoming"] not in db.get(m.Source, case["source"]).acl


def test_pg_simultaneous_handover_approvals_have_one_winner(case):
    with case["factory"]() as db:
        db.get(m.Transition, case["transition"]).status = "generated"
        db.commit()
    body = s.Note(note="Reviewed this exact generated handover version.", expected_version=1)
    results = simultaneous(
        case, *[lambda: call(case, "admin", workspace.approve, case["project"], case["transition"], body)] * 2
    )
    assert sorted(r["status"] for r in results) == [200, 409]
    assert audit_count(case, "handover.approved") == 2  # Setup approval plus one winning request.


def test_pg_simultaneous_exercise_generation_preserves_unique_tasks(case):
    assignment(case)
    results = simultaneous(
        case, *[lambda: call(case, "admin", workspace.exercises, case["project"], case["transition"])] * 2
    )
    assert [r["status"] for r in results] == [200, 200]
    with case["factory"]() as db:
        tasks = list(db.scalars(select(m.Exercise).where(m.Exercise.transition_id == case["transition"])))
        assert len(tasks) == 2
        assert len({task.assessment["claim_id"] for task in tasks}) == 2


def test_pg_simultaneous_supervisor_review_preserves_one_assessment(case):
    assignment(case)
    call(case, "admin", workspace.exercises, case["project"], case["transition"])
    with case["factory"]() as db:
        task = db.scalar(select(m.Exercise).where(m.Exercise.transition_id == case["transition"]))
        refs = list(db.scalars(select(m.Evidence.id).where(m.Evidence.project_id == case["project"])))
        task_id, criteria = task.id, task.criteria
    call(
        case,
        "incoming",
        workspace.submit,
        case["project"],
        task_id,
        s.Submission(
            answer="Located staging evidence, approval requirements and application health checks.",
            evidence_ids=refs,
            escalation="Request specialist review before any unsafe operation.",
        ),
    )
    body = s.Assessment(
        action="pass",
        note="Inspected each current cited scenario criterion.",
        criteria_passed=[True] * len(criteria),
    )
    results = simultaneous(
        case, *[lambda: call(case, "admin", workspace.assess, case["project"], task_id, body)] * 2
    )
    assert sorted(r["status"] for r in results) == [200, 409]
    with case["factory"]() as db:
        assert len(db.get(m.Exercise, task_id).assessment["review_history"]) == 1


def invitation(case):
    token = secrets.token_urlsafe(48)
    with case["factory"]() as db:
        item = m.Invitation(
            org_id=db.get(m.Project, case["project"]).org_id,
            project_id=case["project"],
            email=f"{uuid4().hex}@invitation-qa.example",
            name="Invited QA member",
            title="Test engineer",
            role="incoming",
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            created_by=case["admin"],
            expires_at=m.utcnow() + timedelta(hours=1),
        )
        db.add(item)
        db.commit()
        return item.id, item.email, token


def accept_invitation(case, token, client):
    with case["factory"]() as db:
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/auth/invitation/accept",
                "headers": [],
                "client": (client, 12345),
                "server": ("127.0.0.1", 8010),
                "scheme": "http",
            }
        )
        try:
            result = onboarding.accept(
                onboarding.JoinBody(token=token, password="isolated-qa-password-only"),
                request,
                Response(),
                db,
            )
            return {"status": 200, "result": result}
        except HTTPException as exc:
            db.rollback()
            return {"status": exc.status_code, "detail": exc.detail}


def test_pg_single_use_invitation_accepts_only_one_concurrent_recipient(case):
    item_id, email, token = invitation(case)
    results = simultaneous(
        case,
        lambda: accept_invitation(case, token, "qa-one"),
        lambda: accept_invitation(case, token, "qa-two"),
    )
    assert sorted(r["status"] for r in results) == [200, 409]
    with case["factory"]() as db:
        assert db.get(m.Invitation, item_id).status == "accepted"
        assert db.scalar(select(func.count()).select_from(m.User).where(m.User.email == email)) == 1
    assert audit_count(case, "invitation.accepted") == 1


def test_pg_invitation_accept_and_revoke_cannot_both_succeed(case):
    item_id, email, token = invitation(case)
    results = simultaneous(
        case,
        lambda: accept_invitation(case, token, "qa-join"),
        lambda: call(case, "admin", onboarding.revoke, case["project"], item_id),
    )
    assert sorted(r["status"] for r in results) == [200, 409]
    with case["factory"]() as db:
        status = db.get(m.Invitation, item_id).status
        member_count = db.scalar(select(func.count()).select_from(m.User).where(m.User.email == email))
        assert (status == "accepted" and member_count == 1) or (status == "revoked" and member_count == 0)


def test_pg_revocation_rechecks_invitation_consumed_by_overlapping_transaction(case):
    item_id, _, token = invitation(case)
    with case["factory"]() as stale_reviewer, ThreadPoolExecutor(max_workers=1) as pool:
        # A READ COMMITTED request can retain an ORM object loaded before another commit.
        stale_item = stale_reviewer.get(m.Invitation, item_id)
        assert stale_item.status == "pending"
        result = pool.submit(accept_invitation, case, token, "qa-stale-revoke").result(timeout=15)
        assert result["status"] == 200
        with pytest.raises(HTTPException) as error:
            onboarding.revoke(
                case["project"], item_id, stale_reviewer, stale_reviewer.get(m.User, case["admin"])
            )
        assert error.value.status_code == 409
        stale_reviewer.rollback()
    with case["factory"]() as db:
        assert db.get(m.Invitation, item_id).status == "accepted"
