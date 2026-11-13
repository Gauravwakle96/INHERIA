from app.acceptance_evaluation import evaluate_extraction


def test_frozen_holdout_reproduces_counts_and_discloses_misses(monkeypatch):
    import app.database as database

    monkeypatch.setattr(database, "SessionLocal", lambda: (_ for _ in ()).throw(AssertionError("No app DB")))
    first = evaluate_extraction()
    assert first == evaluate_extraction()
    assert first["counts"]["documents"] == 60
    assert first["counts"]["prose_documents"] >= 20
    assert len(first["details"]) == 60
    assert len(first["false_negatives"]) == first["candidate"]["false_negatives"]
    assert len(first["false_positives"]) == first["candidate"]["false_positives"]
    assert all(metric["denominator"] > 0 for metric in first["fields"].values())


def test_diverse_prose_regression_keeps_joint_ownership_uncertain():
    from pathlib import Path

    result = evaluate_extraction(Path("evaluation/diverse-prose-challenge.json"))
    assert result["counts"]["documents"] == 24
    joint = next(c for c in result["details"] if c["id"] == "owner-team")["observed"][0]
    assert joint["data"]["owner_id"] is None
    assert len(joint["data"]["candidate_owner_ids"]) == 2
    assert result["exact_quotes"]["rate"] == 1
