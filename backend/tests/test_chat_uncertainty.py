from datetime import timedelta

from sqlalchemy import select
from test_chat import setup, verify_all

from app import chat
from app import models as m


def test_context_marks_old_evidence_and_explains_accessible_conflicts(workspace, monkeypatch):
    client, factory, pid, actor, base, _, _ = setup(workspace, monkeypatch)
    verify_all(client, base)
    with factory() as db:
        source = db.scalar(select(m.Source).where(m.Source.project_id == pid, m.Source.acl == []))
        source.source_time = m.utcnow() - timedelta(days=200)
        db.commit()
        context, _, _, _ = chat.prepare_context(
            db, db.get(m.User, actor["id"]), pid, "deployment architecture", "high"
        )
        assert all("source_time" in e and "freshness" in e for e in context["evidence"])
        assert any(e["freshness"] == "review_required" for e in context["evidence"])
        assert context["uncertainty"]
        assert all("human resolution" in item["reason"] for item in context["uncertainty"])


def test_historical_and_negated_prose_does_not_assign_current_ownership():
    from app.intelligence import parse_candidates

    user = m.User(id="gaurav", name="Gaurav")
    for text in (
        "Gaurav no longer maintains deployment pipelines.",
        "Gaurav does not own infrastructure maintenance.",
        "Gaurav formerly owns service deployments.",
        "A proposed decision selected a cloud provider.",
    ):
        assert not parse_candidates(text, [user])
    for text in ("Gaurav handles deployment coordination.", "Gaurav looks after monitoring dashboards."):
        candidates = parse_candidates(text, [user])
        assert candidates[0]["data"]["owner_id"] == "gaurav"
