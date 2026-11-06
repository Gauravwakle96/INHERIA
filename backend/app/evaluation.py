"""Reproducible evaluation of deterministic knowledge rules on labelled fixtures.

This module never connects to the configured application database or a model.
Its labels are authored independently of parse_candidates. Passing citation
checks does not establish that a source statement is true or well classified.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app import models as m
from app.intelligence import (
    citations,
    current_claims,
    find_gaps,
    parse_candidates,
    reconstruct_project,
    successor_answer,
)

FIXTURE_VERSION = "labelled-continuity-v1"
REFERENCE_TIME = datetime(2026, 11, 6, 12, 0, 0)


@dataclass(frozen=True)
class GoldCandidate:
    kind: str
    title: str
    fields: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Case:
    key: str
    text: str
    expected: tuple[GoldCandidate, ...]
    age_days: int = 7
    note: str = ""


CASES = (
    Case(
        "responsibility_explicit",
        "Responsibility: Deploy billing-api\nOwner: Ada Vale\nBackup: Quinn Reed\nSystem: billing-api\nCritical: yes\nDocumented: yes",
        (
            GoldCandidate(
                "responsibility", "Deploy billing-api", {"owner": "Ada Vale", "backup": "Quinn Reed"}
            ),
        ),
    ),
    Case(
        "responsibility_no_backup",
        "Responsibility: Recover billing database\nOwner: Ada Vale\nBackup: none\nSystem: ledger-db\nCritical: yes\nDocumented: no",
        (GoldCandidate("responsibility", "Recover billing database", {"owner": "Ada Vale", "backup": None}),),
    ),
    Case(
        "responsibility_unknown",
        "Responsibility: Rotate signing keys\nOwner: Unknown\nBackup: none\nSystem: signing-service\nDocumented: no",
        (GoldCandidate("responsibility", "Rotate signing keys", {"owner": None, "backup": None}),),
    ),
    Case(
        "responsibility_unmapped",
        "Responsibility: Archive incident notes\nOwner: Departed Contractor\nSystem: archive-service",
        (GoldCandidate("responsibility", "Archive incident notes", {"owner": None}),),
        note="An unknown person must remain unmapped; no fictional employee is created.",
    ),
    Case(
        "decision_current",
        "Decision: Storage engine\nTopic: ledger storage\nRationale: Use PostgreSQL transactions for atomic invoice writes.\nAlternative: Document store rejected for transactional workload.\nStatus: current",
        (
            GoldCandidate(
                "decision",
                "Storage engine",
                {"rationale": "Use PostgreSQL transactions for atomic invoice writes."},
            ),
        ),
    ),
    Case(
        "decision_conflict",
        "Decision: Storage engine\nTopic: ledger storage\nRationale: Use only MongoDB documents for invoice writes; do not use PostgreSQL.\nStatus: current",
        (
            GoldCandidate(
                "decision",
                "Storage engine",
                {"rationale": "Use only MongoDB documents for invoice writes; do not use PostgreSQL."},
            ),
        ),
        note="Same exact topic and title, conflicting source rationales; human conflict review is required.",
    ),
    Case(
        "decision_missing_rationale",
        "Decision: Adopt event queues\nTopic: asynchronous work\nStatus: current",
        (GoldCandidate("decision", "Adopt event queues", {"rationale": ""}),),
    ),
    Case(
        "decision_superseded",
        "Decision: Adopt sync webhook handlers\nTopic: asynchronous work\nRationale: Simpler request paths.\nStatus: superseded",
        (GoldCandidate("decision", "Adopt sync webhook handlers", {"rationale": "Simpler request paths."}),),
        note="A superseded alternative does not constitute an unresolved current conflict.",
    ),
    Case(
        "procedure_current",
        "Procedure: Deploy billing-api in staging\nSystem: billing-api\nStatus: current\n1. Locate .github/workflows/staging.yml.\n2. Confirm the test environment and obtain approval.\n3. Monitor health checks; escalate before production.",
        (GoldCandidate("procedure", "Deploy billing-api in staging"),),
    ),
    Case(
        "procedure_stale",
        "Procedure: Restore ledger-db backup\nSystem: ledger-db\nStatus: current\n1. Select an isolated test database.\n2. Restore a backup into that test database.\n3. Verify checksums and ask the database owner to review.",
        (GoldCandidate("procedure", "Restore ledger-db backup"),),
        age_days=200,
        note="Age crosses the 180-day review threshold; this does not establish inaccuracy.",
    ),
    Case(
        "dependency_arrow",
        "Dependency: billing-api -> ledger-db\nStatus: current",
        (
            GoldCandidate(
                "dependency",
                "billing-api -> ledger-db",
                {"from_component": "billing-api", "to_component": "ledger-db"},
            ),
        ),
    ),
    Case(
        "dependency_fields",
        "Dependency: Customer dashboard storage\nSystem: web-dashboard\nDepends on: billing-api\nStatus: current",
        (
            GoldCandidate(
                "dependency",
                "Customer dashboard storage",
                {"from_component": "web-dashboard", "to_component": "billing-api"},
            ),
        ),
    ),
    Case(
        "incident_open",
        "Incident: Invoice retry backlog\nOwner: Ada Vale\nSystem: billing-api\nStatus: open\nRetries are failing after the last migration.",
        (GoldCandidate("incident", "Invoice retry backlog"),),
    ),
    Case(
        "task_completed",
        "Task: Database migration verification\nOwner: Quinn Reed\nSystem: ledger-db\nStatus: completed\nThe staging test passed and was reviewed.",
        (GoldCandidate("task", "Database migration verification"),),
        note="Completed work must not be counted as an open commitment.",
    ),
    Case(
        "task_open",
        "Task: Prepare rollback runbook\nOwner: Ada Vale\nSystem: billing-api\nStatus: open\nThe latest rollback steps are not documented.",
        (GoldCandidate("task", "Prepare rollback runbook"),),
    ),
    Case(
        "lesson",
        "Lesson: Validate migration lock duration\nTest the migration against a representative staging dataset before scheduling maintenance.",
        (GoldCandidate("lesson", "Validate migration lock duration"),),
    ),
    Case(
        "architecture",
        "Architecture: Billing service topology\nComponent: billing-api\nThe API receives dashboard requests and stores invoices in ledger-db.",
        (GoldCandidate("architecture", "Billing service topology"),),
    ),
    Case(
        "prose_responsibility",
        "Ada Vale maintains the billing-api rotation. The role requires weekly database backup checks.",
        (
            GoldCandidate(
                "responsibility",
                "Ada Vale maintains the billing-api rotation. The role requires weekly database backup checks.",
                {"owner": "Ada Vale"},
            ),
        ),
        note="Explicit prose names the maintainer; conservative field-only owner extraction may miss it.",
    ),
    Case(
        "prose_decision",
        "The platform team decided to use Redis caching because the traffic pattern includes repeated lookups.",
        (
            GoldCandidate(
                "decision",
                "The platform team decided to use Redis caching because the traffic pattern includes repeated lookups.",
                {"rationale": "the traffic pattern includes repeated lookups"},
            ),
        ),
        note="A quoted rationale can exist even when it is not populated into a structured field.",
    ),
    Case(
        "prose_dependency",
        "billing-api depends on PostgreSQL to persist invoices safely.",
        (
            GoldCandidate(
                "dependency",
                "billing-api depends on PostgreSQL to persist invoices safely.",
                {"from_component": "billing-api", "to_component": "PostgreSQL"},
            ),
        ),
        note="Free-prose dependency extraction is a deliberate difficult positive.",
    ),
    Case(
        "commit_only",
        "Commit c001 by Ada Vale: update billing-api configuration. Contributor activity is not independently verified ownership.",
        (),
        note="Authorship alone is not evidence of an assigned responsibility.",
    ),
    Case(
        "negated_knowledge",
        "No source establishes who owns the billing-api deployment pipeline. Commit counts alone do not prove responsibility.",
        (),
        note="A statement that knowledge is missing is not an operational procedure.",
    ),
    Case(
        "unrelated",
        "Lunch planning is unrelated personal information and must not be used to establish technical responsibilities.",
        (),
    ),
    Case(
        "missing_information",
        "Repository documentation is currently unavailable; no system relationships have been verified.",
        (),
    ),
)


def fixture_id(key: str) -> str:
    return str(uuid5(NAMESPACE_URL, "inheria-evaluation:" + key))


def fraction(numerator: int, denominator: int) -> dict:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": round(numerator / denominator, 6) if denominator else None,
    }


def classification(expected: list[tuple], predicted: list[tuple]) -> dict:
    gold, actual = Counter(expected), Counter(predicted)
    matched = sum((gold & actual).values())
    return {
        "true_positives": matched,
        "false_positives": sum((actual - gold).values()),
        "false_negatives": sum((gold - actual).values()),
        "precision": fraction(matched, sum(actual.values())),
        "recall": fraction(matched, sum(gold.values())),
    }


def _initialise(db: Session):
    org = m.Organisation(
        id=fixture_id("org"), name="LABELLED EVALUATION ONLY", industry="technology", is_demo=True
    )
    db.add(org)
    db.flush()
    users = []
    for name, role in [("Ada Vale", "employee"), ("Quinn Reed", "incoming"), ("Mira Chen", "manager")]:
        user = m.User(
            id=fixture_id(name),
            org_id=org.id,
            name=name,
            email=name.lower().replace(" ", ".") + "@evaluation.example",
            title=role,
            role=role,
            active=True,
            password_hash="not-a-login-fixture",
        )
        db.add(user)
        users.append(user)
    project = m.Project(
        id=fixture_id("project"),
        org_id=org.id,
        name="Controlled continuity corpus",
        description="Isolated labelled fixtures",
        stack=["synthetic"],
        is_demo=True,
    )
    db.add(project)
    db.flush()
    for user in users:
        db.add(m.Membership(project_id=project.id, user_id=user.id, role=user.role))
    source_keys = {}
    for case in CASES:
        source = m.Source(
            id=fixture_id(case.key),
            org_id=org.id,
            project_id=project.id,
            name=case.key,
            kind="markdown",
            status="ready",
            version=1,
            acl=[],
            synthetic=True,
            source_time=REFERENCE_TIME - timedelta(days=case.age_days),
            checksum=hashlib.sha256(case.text.encode()).hexdigest(),
            source_metadata={"fixture": case.key},
        )
        db.add(source)
        db.flush()
        db.add(
            m.Chunk(
                id=fixture_id(case.key + ":chunk"),
                org_id=org.id,
                project_id=project.id,
                source_id=source.id,
                source_version=1,
                ordinal=0,
                locator=f"Labelled fixture {case.key}",
                text=case.text,
            )
        )
        source_keys[source.id] = case.key
    # An actually restricted document is never sent to a model or to the actor's
    # reconstruction. This fixture is excluded from extraction scoring.
    restricted = m.Source(
        id=fixture_id("restricted"),
        org_id=org.id,
        project_id=project.id,
        name="Restricted supervisor-only runbook",
        kind="markdown",
        status="ready",
        version=1,
        acl=[users[0].id],
        synthetic=True,
        source_time=REFERENCE_TIME,
    )
    db.add(restricted)
    db.flush()
    db.add(
        m.Chunk(
            org_id=org.id,
            project_id=project.id,
            source_id=restricted.id,
            source_version=1,
            locator="Restricted fixture",
            text="Procedure: Restricted recovery\nSystem: confidential-vault\nNever disclose this source outside its ACL.",
        )
    )
    db.commit()
    return project, users, users[-1], source_keys, restricted


def run_evaluation() -> dict:
    """Return measured results from a fresh in-memory database and fixed clock."""
    engine = create_engine("sqlite:///:memory:")
    m.Base.metadata.create_all(engine)
    with Session(engine) as db, patch("app.models.utcnow", return_value=REFERENCE_TIME):
        project, users, actor, source_keys, restricted = _initialise(db)
        expected_keys, actual_keys, case_results = [], [], []
        owner_results, rationale_results, dependency_results, activity_results = [], [], [], []
        name_by_id = {user.id: user.name for user in users}
        for case in CASES:
            actual = parse_candidates(case.text, users)
            gold = {(candidate.kind, candidate.title): candidate for candidate in case.expected}
            for expected in case.expected:
                expected_keys.append((case.key, expected.kind, expected.title))
            for candidate in actual:
                actual_keys.append((case.key, candidate["kind"], candidate["title"]))
            local = []
            for candidate in actual:
                key = (candidate["kind"], candidate["title"])
                expected = gold.get(key)
                observed_fields = {
                    **candidate["data"],
                    "owner": name_by_id.get(candidate["data"].get("owner_id")),
                    "backup": name_by_id.get(candidate["data"].get("backup_id")),
                }
                local.append(
                    {
                        "kind": candidate["kind"],
                        "title": candidate["title"],
                        "label_match": expected is not None,
                        "fields": {k: observed_fields.get(k) for k in (expected.fields if expected else [])},
                        "exact_quote": candidate["quote"] in case.text,
                    }
                )
            for expected in case.expected:
                candidate = next(
                    (c for c in actual if (c["kind"], c["title"]) == (expected.kind, expected.title)), None
                )
                data = candidate["data"] if candidate else {}
                if "owner" in expected.fields:
                    owner_results.append(
                        {
                            "case": case.key,
                            "expected": expected.fields["owner"],
                            "observed": name_by_id.get(data.get("owner_id")),
                            "correct": candidate is not None
                            and name_by_id.get(data.get("owner_id")) == expected.fields["owner"],
                        }
                    )
                if "rationale" in expected.fields:
                    rationale_results.append(
                        {
                            "case": case.key,
                            "expected": expected.fields["rationale"],
                            "observed": data.get("rationale", ""),
                            "correct": candidate is not None
                            and data.get("rationale", "") == expected.fields["rationale"],
                        }
                    )
                if "from_component" in expected.fields:
                    correct = candidate is not None and all(
                        data.get(key) == expected.fields[key] for key in ("from_component", "to_component")
                    )
                    dependency_results.append(
                        {
                            "case": case.key,
                            "expected": {k: expected.fields[k] for k in ("from_component", "to_component")},
                            "observed": {k: data.get(k) for k in ("from_component", "to_component")},
                            "correct": correct,
                        }
                    )
            if case.key == "commit_only":
                activity_results.append(
                    not any(c["kind"] == "responsibility" or c["data"].get("owner_id") for c in actual)
                )
            case_results.append(
                {
                    "case": case.key,
                    "expected": [asdict(x) for x in case.expected],
                    "observed": local,
                    "note": case.note,
                }
            )
        stats = reconstruct_project(db, actor, project.id)
        db.commit()
        claims = current_claims(db, actor, project.id)
        pending = sum(claim.status == "pending" for claim in claims)
        citation_checks, quoted_claims = [], 0
        claim_cases = {}
        for claim in claims:
            refs = citations(db, actor, claim)
            if refs:
                quoted_claims += 1
                claim_cases[claim.id] = source_keys[refs[0]["source_id"]]
            for ref in refs:
                chunk = db.get(m.Chunk, ref["chunk_id"])
                source = db.get(m.Source, ref["source_id"])
                citation_checks.append(
                    bool(
                        chunk
                        and source
                        and ref["quote"] in chunk.text
                        and ref["source_version"] == source.version == chunk.source_version
                        and ref["locator"] == chunk.locator
                        and ref["synthetic"]
                    )
                )
        findings = find_gaps(db, actor, project.id)

        def finding_cases(kind):
            return [(claim_cases.get(f["claim_id"], "unmapped"),) for f in findings if f["kind"] == kind]

        actual_conflicts = [
            tuple(sorted(source_keys[sid] for sid in f["source_ids"]))
            for f in findings
            if f["kind"] == "contradiction"
        ]
        gold_conflicts = [tuple(sorted(["decision_current", "decision_conflict"]))]
        gap_metrics = {
            "potential_decision_conflict": classification(gold_conflicts, actual_conflicts),
            "stale_source_review": classification([("procedure_stale",)], finding_cases("stale_source")),
            "unfinished_work": classification(
                [("incident_open",), ("task_open",)], finding_cases("unfinished_work")
            ),
            "missing_decision_rationale": classification(
                [("decision_missing_rationale",)], finding_cases("missing_rationale")
            ),
            "unknown_responsibility_owner": classification(
                [("responsibility_unknown",), ("responsibility_unmapped",)],
                finding_cases("unknown_ownership"),
            ),
        }
        # Nothing is authoritative before review, including contradictory records.
        before_review = successor_answer(db, actor, project.id, "How do I deploy billing-api in staging?")
        for claim in claims:
            if claim_cases.get(claim.id) in {"procedure_current", "responsibility_explicit"}:
                claim.status = "verified"
                claim.verified_by = actor.id
                claim.verified_at = REFERENCE_TIME
        db.flush()
        supported = successor_answer(db, actor, project.id, "How do I deploy billing-api in staging?")
        questions = [
            "What is the annual company revenue?",
            "Who owns the Kubernetes firewall?",
            "What exact financial impact does deployment have?",
            "What is the confidential-vault recovery procedure?",
        ]
        unknown_results = []
        for question in questions:
            answer = successor_answer(db, actor, project.id, question)
            unknown_results.append(
                {
                    "question": question,
                    "expected_known": False,
                    "observed_known": answer["known"],
                    "citation_count": len(answer["citations"]),
                    "correct_abstention": not answer["known"] and not answer["citations"],
                }
            )
        restricted_claims = list(db.scalars(select(m.Evidence).where(m.Evidence.source_id == restricted.id)))
        kinds_expected = {candidate.kind for case in CASES for candidate in case.expected}
        kinds_seen = {claim.kind for claim in claims}
        fingerprint = hashlib.sha256(
            json.dumps([asdict(case) for case in CASES], sort_keys=True).encode()
        ).hexdigest()
        report = {
            "fixture_version": FIXTURE_VERSION,
            "fixture_sha256": fingerprint,
            "reference_time": REFERENCE_TIME.isoformat(),
            "engine": "deterministic-v1",
            "scope": "24 hand-labelled synthetic documents plus one source-ACL negative; isolated in-memory SQLite; no live LLM calls.",
            "counts": {
                "documents": len(CASES),
                "gold_candidates": len(expected_keys),
                "predicted_candidates": len(actual_keys),
                "persisted_visible_claims": len(claims),
                "restricted_sources": 1,
            },
            "metrics": {
                "candidate_kind_and_title": classification(expected_keys, actual_keys),
                "owner_mapping": fraction(sum(x["correct"] for x in owner_results), len(owner_results)),
                "decision_rationale_field": fraction(
                    sum(x["correct"] for x in rationale_results), len(rationale_results)
                ),
                "dependency_endpoints": fraction(
                    sum(x["correct"] for x in dependency_results), len(dependency_results)
                ),
                "project_state_kind_coverage": fraction(
                    len(kinds_expected & kinds_seen), len(kinds_expected)
                ),
                "exact_source_citations": fraction(sum(citation_checks), len(citation_checks)),
                "claims_with_citations": fraction(quoted_claims, len(claims)),
                "pending_before_human_review": fraction(pending, len(claims)),
                "commit_authorship_ownership_abstention": fraction(
                    sum(activity_results), len(activity_results)
                ),
                "unverified_answer_abstention": fraction(int(not before_review["known"]), 1),
                "supported_retrieval_after_review": fraction(
                    int(supported["known"] and bool(supported["citations"])), 1
                ),
                "unsupported_answer_abstention": fraction(
                    sum(x["correct_abstention"] for x in unknown_results), len(unknown_results)
                ),
                "restricted_source_excluded_from_reconstruction": fraction(int(not restricted_claims), 1),
                **gap_metrics,
            },
            "details": {
                "cases": case_results,
                "owner_mapping": owner_results,
                "decision_rationale": rationale_results,
                "dependency_endpoints": dependency_results,
                "unsupported_questions": unknown_results,
                "conflict_pairs": actual_conflicts,
                "reconstruction": stats,
            },
            "limitations": [
                "This controlled synthetic corpus is small and intentionally includes the supported structured syntax. It is not a representative organisational dataset.",
                "Labels were written for these fixtures; this is deterministic rule evaluation, not an independently validated real employee handover benchmark.",
                "Exact citation checks establish attribution only, not source truth, semantic entailment, completeness, operational competence or business continuity.",
                "The potential-conflict metric measures requests for human review, not reliable semantic contradiction resolution.",
                "Only one source-ACL negative is counted here; comprehensive tenant/project/source enforcement is exercised in separate API tests.",
                "No model accuracy, onboarding-time reduction, production readiness or financial benefit is claimed.",
            ],
        }
    engine.dispose()
    return report


def render_markdown(report: dict) -> str:
    lines = [
        "# INHERIA controlled synthetic evaluation",
        "",
        report["scope"],
        "",
        f"Fixture `{report['fixture_version']}`; SHA-256 `{report['fixture_sha256']}`.",
        "",
        "Run from `backend`: `uv run python -m app.evaluation`. The command uses an isolated in-memory database and makes no external AI requests.",
        "",
        "| Measure | Numerator / denominator | Rate |",
        "| --- | ---: | ---: |",
    ]
    for key, metric in report["metrics"].items():
        if "precision" in metric:
            for name in ("precision", "recall"):
                value = metric[name]
                rate = f"{value['rate'] * 100:.1f}%" if value["rate"] is not None else "Not measured"
                lines.append(
                    f"| {key.replace('_', ' ')}: {name} | {value['numerator']} / {value['denominator']} | {rate} |"
                )
        else:
            rate = f"{metric['rate'] * 100:.1f}%" if metric["rate"] is not None else "Not measured"
            lines.append(
                f"| {key.replace('_', ' ')} | {metric['numerator']} / {metric['denominator']} | {rate} |"
            )
    lines.extend(["", "## Observed errors and limits", ""])
    errors = []
    for key in ("owner_mapping", "decision_rationale", "dependency_endpoints"):
        for item in report["details"][key]:
            if not item["correct"]:
                errors.append(
                    f"- `{item['case']}`: {key.replace('_', ' ')} expected `{item['expected']}`, observed `{item['observed']}`."
                )
    for item in report["details"]["unsupported_questions"]:
        if not item["correct_abstention"]:
            errors.append(
                f"- Unsupported question **{item['question']}** returned matching excerpts (`known=true`) instead of complete abstention. Matching words do not establish the requested fact."
            )
    for case in report["details"]["cases"]:
        expected = {(x["kind"], x["title"]) for x in case["expected"]}
        observed = {(x["kind"], x["title"]) for x in case["observed"]}
        if expected != observed:
            errors.append(
                f"- `{case['case']}`: candidate labels differed from the hand-authored reference. See the JSON case results."
            )
    lines.extend(errors or ["No counted errors in this fixture; the scope limitations below still apply."])
    lines.extend(["", "## Interpretation", ""])
    lines.extend("- " + limitation for limitation in report["limitations"])
    lines.extend(
        [
            "",
            "Precision = matched labelled candidates / all predicted candidates. Recall = matched labelled candidates / all gold candidates. Field accuracy includes missed candidates in its denominator. Kind coverage is the presence of eight labelled entity types, not project reconstruction correctness.",
            "",
            "The JSON report retains every fixture label, predicted field, missed positive, false positive and unsupported question. Evaluation gaps are not concealed by the test suite: tests check reproducibility and measurement consistency, rather than forcing every metric to 100%.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    report = run_evaluation()
    root = Path(__file__).resolve().parents[2]
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    json_path, md_path = docs / "evaluation-report.json", docs / "evaluation-report.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "report": str(json_path),
                "documents": report["counts"]["documents"],
                "candidate_metrics": report["metrics"]["candidate_kind_and_title"],
                "unsupported_answer_abstention": report["metrics"]["unsupported_answer_abstention"],
            }
        )
    )


if __name__ == "__main__":
    main()
