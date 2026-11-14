from pathlib import Path

from app import models as m
from app.acceptance_evaluation import evaluate_extraction
from app.intelligence import parse_candidates


def people():
    return [
        m.User(id=name, name=name, email=name.replace(" ", "") + "@qa.example")
        for name in ("Ada Vale", "Quinn Reed")
    ]


def test_current_duty_survives_separate_proposed_updates_but_claim_disclaimer_does_not():
    valid = parse_candidates(
        "Ada Vale manages the alert schedule. Quinn Reed reviews proposed updates.", people()
    )
    assert valid[0]["data"]["owner_id"] == "Ada Vale"
    for text in (
        "Ada Vale manages the alert schedule. This claim has not been confirmed.",
        "Ada Vale manages the alert schedule. This statement is no longer current.",
        "Ada Vale manages the alert schedule. This assignment is proposed.",
        'The phrase "Ada Vale owns alerts" appears in a training example, not a current assignment.',
        "Ada Vale might oversee the alert schedule. No assignment is recorded.",
    ):
        assert parse_candidates(text, people()) == []


def test_explicit_service_dependency_endpoints_are_exact_and_exclude_instruction_clauses():
    text = "The artifact registry is used by the release worker before the staging approval."
    candidate = parse_candidates(text, people())[0]
    assert candidate["kind"] == "dependency"
    assert candidate["data"]["from_component"] == "release worker"
    assert candidate["data"]["to_component"] == "artifact registry"
    assert candidate["data"]["field_evidence"]["dependency"] in candidate["quote"]
    assert not parse_candidates(
        "The developer uses a workstation for meetings. No service dependency is stated.", people()
    )


def test_missing_decision_reason_remains_candidate_without_fabricated_rationale():
    text = "The team adopted a managed log archive. The rationale was not documented."
    candidate = parse_candidates(text, people())[0]
    assert candidate["kind"] == "decision"
    assert not candidate["data"].get("rationale")
    assert candidate["data"]["rationale_uncertainty"]
    assert candidate["quote"] == text


def test_frozen_judge_challenge_regression_retains_shared_unknown_and_exact_evidence():
    result = evaluate_extraction(Path("evaluation/judge-input-challenge.json"))
    assert result["targets_met"] and result["candidate"]["precision"]["rate"] >= 0.9
    assert result["counts"]["documents"] == 72
    assert not result["false_positives"]
    assert result["exact_quotes"]["rate"] == 1
    for document in result["details"]:
        for candidate in document["observed"]:
            assert all(span in candidate["quote"] for span in candidate["data"]["field_evidence"].values())
    shared = next(d for d in result["details"] if d["id"] == "judge-owner-09")["observed"][0]["data"]
    assert shared["owner_id"] is None and len(shared["candidate_owner_ids"]) == 2


def test_separate_postfix_holdout_keeps_new_identities_and_disclosed_misses():
    result = evaluate_extraction(Path("evaluation/postfix-internal-holdout.json"))
    assert result["counts"] == {"documents": 60, "prose_documents": 60}
    assert result["targets_met"] and result["exact_quotes"]["rate"] == 1
    assert result["candidate"]["false_negatives"] == 2
    owners = {
        candidate["data"]["owner_id"]
        for doc in result["details"]
        for candidate in doc["observed"]
        if candidate["data"].get("owner_id")
    }
    assert owners == {"Mira Shah", "Owen Cole"}
