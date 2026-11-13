"""Run the confirmed three commitments' existing, distinct acceptance journeys.

Uses only owned pytest fixtures and mocked GitHub; no paid model calls or live data.
"""

import hashlib
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    "onboarding": [
        (
            "single-use invitation and revocation",
            "tests/test_round3.py::test_invitation_is_hashed_single_use_and_revocable",
        ),
        ("expired invitation", "tests/test_round3.py::test_expired_invitation_cannot_be_accepted"),
        (
            "independent source-access review",
            "tests/test_round3.py::test_access_grant_requires_independent_authorised_reviewer",
        ),
        (
            "missing access and authorised restoration",
            "tests/test_onboarding_completion.py::test_access_readiness_withholds_hidden_titles_and_recovers_after_authorised_grant",
        ),
        (
            "member revocation across knowledge boundaries",
            "tests/test_onboarding_completion.py::test_membership_revocation_denies_all_project_boundaries_and_is_audited",
        ),
        (
            "document reader changes and readiness",
            "tests/test_source_access_completion.py::test_document_access_changes_update_readiness_without_erasing_knowledge",
        ),
        (
            "last-reader removal never widens access",
            "tests/test_source_access_completion.py::test_member_revocation_never_widens_a_last_reader_acl",
        ),
    ],
    "source_change_revocation": [
        (
            "uploaded document replacement and reviewed recovery",
            "tests/test_round3.py::test_source_change_invalidates_tasks_and_can_recover_without_duplicates[Check schema compatibility]",
        ),
        (
            "explicit source revocation",
            "tests/test_ingestion.py::test_revocation_invalidates_all_dependent_claims",
        ),
        (
            "source deletion purges persisted derivatives",
            "tests/test_ingestion.py::test_delete_api_removes_persisted_derived_quotes",
        ),
        (
            "successor loses document access before closure",
            "tests/test_round3_boundaries.py::test_manager_cannot_close_when_successor_loses_source_access",
        ),
        (
            "parent change invalidates transitive interview evidence",
            "tests/test_source_access_completion.py::test_parent_change_traces_and_invalidates_transitive_interview_evidence",
        ),
        (
            "GitHub credential revocation and reauthorisation",
            "tests/test_connector_permissions.py::test_permission_loss_invalidates_cached_knowledge_but_transient_failures_preserve_it[401-failure_headers0-Invalid authorization-True]",
        ),
        (
            "GitHub repository permission revoked",
            "tests/test_connector_permissions.py::test_permission_loss_invalidates_cached_knowledge_but_transient_failures_preserve_it[403-failure_headers1-Repository permission denied-True]",
        ),
        (
            "GitHub repository becomes inaccessible",
            "tests/test_connector_permissions.py::test_permission_loss_invalidates_cached_knowledge_but_transient_failures_preserve_it[404-failure_headers2-Repository not found-True]",
        ),
        (
            "complete repository tree proves document removal",
            "tests/test_connector_permissions.py::test_definitive_file_disappearance_invalidates_cache_but_partial_trees_do_not[complete_tree]",
        ),
        (
            "README removal and source revalidation",
            "tests/test_connector_permissions.py::test_definitive_file_disappearance_invalidates_cache_but_partial_trees_do_not[readme_404]",
        ),
    ],
    "interrupted_jobs": [
        (
            f"interruption at source {position}",
            f"tests/test_round3.py::test_interrupted_investigation_has_durable_idempotent_resume[{position}]",
        )
        for position in (2, 3, 4, 7, 11)
    ],
    "transfer_roles": [
        (
            scenario,
            f"tests/test_transfer_acceptance.py::test_transfer_role_and_recovery_scenarios[{scenario}]",
        )
        for scenario in (
            "incoming_accepts",
            "wrong_owner_rejected",
            "missing_evidence_rejected",
            "supervisor_cannot_submit",
            "incoming_cannot_self_assess",
            "rejection_blocks_closure",
            "partial_rubric_rejected",
            "revision_then_reassessment",
            "critical_prerequisite_blocks",
            "reopen_requires_reapproval",
            "staging_citation_recorded",
            "staging_revocation_blocks",
        )
    ],
}


def main():
    cases = [case for group in GROUPS.values() for case in group]
    with tempfile.TemporaryDirectory(prefix="inheria-submission-") as temporary:
        xml_path = Path(temporary) / "results.xml"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", *[node for _, node in cases], f"--junitxml={xml_path}"],
            cwd=ROOT,
            check=False,
        )
        parsed = ET.parse(xml_path).getroot() if xml_path.exists() else None
        outcomes = {}
        for case in parsed.iter("testcase") if parsed is not None else []:
            node = case.attrib["classname"].replace(".", "/") + ".py::" + case.attrib["name"]
            status = (
                "failed"
                if case.find("failure") is not None or case.find("error") is not None
                else "skipped"
                if case.find("skipped") is not None
                else "passed"
            )
            outcomes[node] = status
    groups = {
        name: [
            {"scenario": label, "test": node, "status": outcomes.get(node, "not_run")}
            for label, node in cases
        ]
        for name, cases in GROUPS.items()
    }
    extraction = json.loads((ROOT.parent / "docs/extraction-holdout-report.json").read_text(encoding="utf-8"))
    report = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "working_tree_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        ),
        "commit_under_test": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "scope": "Confirmed submitted improvements: onboarding, investigation/change intelligence, practical transfer. Existing fixture/API tests; no chatbot/provider benchmark or live production data.",
        "groups": groups,
        "total": len(cases),
        "passed": sum(status == "passed" for status in outcomes.values()),
        "pytest_exit_code": result.returncode,
        "test_file_sha256": {
            node.split("::")[0]: hashlib.sha256((ROOT / node.split("::")[0]).read_bytes()).hexdigest()
            for _, node in cases
        },
        "extraction_first_run": {
            key: extraction[key]
            for key in ("corpus_sha256", "methodology", "counts", "candidate", "fields", "targets_met")
        },
        "limits": [
            "These are distinct source-change inputs; the earlier ten replacement-text variants alone do not establish ten different failure scenarios.",
            "Interrupted jobs use five positions in the same checkpoint algorithm, as promised; not a distributed-worker durability test.",
            "Extraction labels are internal and implementation-informed; targets met on the bounded initial holdout, not independently proven enterprise accuracy.",
            "Staging records are authored fixtures and supervisor assessments; no external deployment, restore or operational competence is certified.",
        ],
    }
    (ROOT.parent / "docs/three-improvements-tests.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "total": report["total"],
                "passed": report["passed"],
                "groups": {name: len(cases) for name, cases in groups.items()},
            }
        )
    )
    return result.returncode or int(report["passed"] != len(cases))


if __name__ == "__main__":
    raise SystemExit(main())
