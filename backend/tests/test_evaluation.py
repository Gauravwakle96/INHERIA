import hashlib
import json

from app.evaluation import CASES, classification, fraction, render_markdown, run_evaluation


def test_evaluation_is_reproducible_and_never_uses_application_database(monkeypatch):
    import app.database as database

    def forbidden_database(*args, **kwargs):
        raise AssertionError("Evaluation must not touch the live application database")

    monkeypatch.setattr(database, "SessionLocal", forbidden_database)
    first, second = run_evaluation(), run_evaluation()
    assert first == second
    assert first["counts"]["documents"] == len(CASES)
    assert len(first["details"]["cases"]) == len(CASES)
    assert first["counts"]["gold_candidates"] > 0
    assert first["engine"] == "deterministic-v1"
    assert len(first["fixture_sha256"]) == 64


def test_labels_are_counted_with_false_positives_and_missed_positives():
    results = classification([("gold",), ("missed",)], [("gold",), ("extra",)])
    assert results["true_positives"] == 1
    assert results["false_positives"] == 1
    assert results["false_negatives"] == 1
    assert results["precision"] == fraction(1, 2)
    assert results["recall"] == fraction(1, 2)
    assert fraction(0, 0)["rate"] is None


def test_evaluation_keeps_quote_accuracy_distinct_from_semantic_accuracy():
    report = run_evaluation()
    metrics = report["metrics"]
    assert metrics["exact_source_citations"]["numerator"] == metrics["exact_source_citations"]["denominator"]
    assert metrics["pending_before_human_review"]["rate"] == 1
    assert metrics["restricted_source_excluded_from_reconstruction"]["rate"] == 1
    assert metrics["commit_authorship_ownership_abstention"]["rate"] == 1
    # The purpose of this assertion is to ensure difficult free-prose cases and
    # their independent field labels remain in the report, not to lock in a bug.
    assert any(item["case"] == "prose_responsibility" for item in report["details"]["owner_mapping"])
    assert any(item["case"] == "prose_dependency" for item in report["details"]["dependency_endpoints"])
    assert len(report["details"]["unsupported_questions"]) >= 4
    assert "not a representative" in " ".join(report["limitations"])


def test_markdown_preserves_measured_denominators_and_discloses_errors():
    report = run_evaluation()
    markdown = render_markdown(report)
    assert "Numerator / denominator" in markdown
    assert "no external AI requests" in markdown
    assert "not source truth" in markdown
    assert "rather than forcing every metric to 100%" in markdown
    serialised = json.dumps(report, sort_keys=True).encode()
    assert (
        hashlib.sha256(serialised).hexdigest()
        == hashlib.sha256(json.dumps(run_evaluation(), sort_keys=True).encode()).hexdigest()
    )
