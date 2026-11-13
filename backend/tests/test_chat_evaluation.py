import json

from cryptography.fernet import Fernet

from app.chat_evaluation import CORPUS_DIR, assess, run_case
from app.config import settings


def test_chat_assessment_does_not_count_a_citation_as_abstention_or_support():
    question = {"support": ["release"], "checks": ["pipeline"]}
    response = {
        "parts": [{"kind": "project"}],
        "answer": "A pipeline is recorded.",
        "unknowns": [],
        "citations": [{"source_id": "other"}],
    }
    checks = assess(question, response, {"other": "unrelated"})
    assert checks["citation_source_screen"] == [False]
    assert not checks["abstained"]


def test_fifty_question_corpus_and_actual_offline_persistence_do_not_use_application_db(monkeypatch):
    import app.database as database

    monkeypatch.setattr(
        database, "SessionLocal", lambda: (_ for _ in ()).throw(AssertionError("No application DB"))
    )
    monkeypatch.setattr(settings, "token_encryption_key", Fernet.generate_key().decode())
    corpus = json.loads((CORPUS_DIR / "chat-holdout.json").read_text())
    assert len(corpus["questions"]) == 50
    assert {q["category"] for q in corpus["questions"]} == {
        "supported",
        "missing",
        "stale",
        "conflicting",
        "restricted",
    }
    for category in ("supported", "missing", "stale", "conflicting", "restricted"):
        question = next(q for q in corpus["questions"] if q["category"] == category)
        result = run_case(corpus, question, "")
        assert result["error"] is None and result["persisted"]
        assert result["response"]["engine"] == "verified_retrieval"
        assert result["screen"]["restricted_canary_absent"]
    outage = run_case(corpus, corpus["questions"][0], "fixture-key", outage=True)
    assert outage["response"]["engine"] == "verified_retrieval"
    assert "Controlled provider outage" in outage["response"]["warning"]
    assert outage["persisted"]
