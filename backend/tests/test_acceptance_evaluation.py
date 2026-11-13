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
