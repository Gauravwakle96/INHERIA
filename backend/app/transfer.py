"""Handover state machine with distinct approval, acceptance and validation gates."""

from __future__ import annotations

import hashlib
import json

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models as m
from app.continuity import project_person
from app.intelligence import citations, current_claims, find_gaps, serialize_claim
from app.security import audit, project_access, require_role, visible_sources


def claim_signature(claim):
    return hashlib.sha256(
        json.dumps(
            {"title": claim.title, "summary": claim.summary, "data": claim.data},
            sort_keys=True,
            ensure_ascii=False,
        ).encode()
    ).hexdigest()


def require_current_handover(db, user, transition):
    claims = {c.id: c for c in current_claims(db, user, transition.project_id, verified=True)}
    successor = project_person(db, user, transition.project_id, transition.successor_id)
    allowed = {c.id for c in current_claims(db, successor, transition.project_id, verified=True)}
    signatures = (transition.report or {}).get("claim_signatures", {})
    if not signatures or any(
        cid not in claims or cid not in allowed or claim_signature(claims[cid]) != signature
        for cid, signature in signatures.items()
    ):
        raise HTTPException(
            409,
            "Handover evidence changed or is inaccessible to the incoming owner. Regenerate and review before approval.",
        )


def scenario_criteria(claim):
    text = (claim.title + " " + str(claim.data.get("component", ""))).lower()
    if "rollback" in text:
        return [
            "Identify the approved previous release and exact rollback source.",
            "Check schema compatibility and conditions requiring database-owner approval.",
            "Explain post-rollback health checks and stop conditions.",
            "Describe an isolated staging walkthrough and escalation; distinguish explanation from execution.",
        ]
    if any(word in text for word in ("recover", "backup", "restore")):
        return [
            "Locate backup evidence and identify missing restore-test records.",
            "Identify approved isolated environment, required access and recovery targets.",
            "Explain integrity checks and how actual test evidence would be reviewed.",
            "Escalate missing evidence; never equate backup-job success with successful recovery.",
        ]
    if any(word in text for word in ("deploy", "release", "pipeline")):
        return [
            "Identify the approved release commit, pipeline and target environment.",
            "Explain build/test/security checks and required release approval.",
            "Describe application health checks and rollback restrictions after schema changes.",
            "Describe safe staging validation and evidence-based escalation; execute no production changes.",
        ]
    return [
        "Locate current evidence for this responsibility or technical component.",
        "Explain the documented procedure and explicitly identify missing steps.",
        "Identify dependencies, prerequisites and unresolved risks.",
        "Describe safe test-environment validation and authorised escalation.",
    ]


def get_transition(db: Session, user: m.User, project_id: str, transition_id: str) -> m.Transition:
    project_access(db, user, project_id)
    transition = db.get(m.Transition, transition_id)
    if not transition or transition.project_id != project_id or transition.org_id != user.org_id:
        raise HTTPException(404, "Transition not found.")
    return transition


def readable_prerequisites(db, user, transition):
    sources = {s.id: s for s in visible_sources(db, user, transition.project_id) if s.status == "ready"}
    refs = {
        e["id"]
        for c in current_claims(db, user, transition.project_id, verified=True)
        for e in citations(db, user, c)
    }
    result = []
    for original in (transition.report or {}).get("prerequisites", []):
        item = dict(original)
        versions = item.get("source_versions", {})
        if not set(item.get("evidence_ids", [])).issubset(refs) or any(
            sid not in sources or sources[sid].version != version for sid, version in versions.items()
        ):
            item = {
                "id": item["id"],
                "title": "Readiness check requires authorised revalidation",
                "required": item.get("required", False),
                "status": "pending",
                "evidence_ids": [],
                "note": "Supporting information changed or is unavailable to your account.",
            }
        else:
            item.pop("source_versions", None)
            item.pop("history", None)
        result.append(item)
    return result


def readable_report(db: Session, user: m.User, transition: m.Transition) -> dict:
    report = transition.report or {}
    current_ids = {c.id for c in current_claims(db, user, transition.project_id)}
    items = [item for item in report.get("knowledge", []) if item["id"] in current_ids]
    # Historical stored quotes can become invalid after source updates; never replay them.
    fresh = {c.id: c for c in current_claims(db, user, transition.project_id, verified=True)}
    knowledge = [serialize_claim(db, user, fresh[item["id"]]) for item in items if item["id"] in fresh]
    unknowns = ["Information without current accessible evidence must remain unverified."]
    if len(knowledge) < len(report.get("knowledge", [])):
        unknowns.append(
            "Some handover evidence changed or is inaccessible; this version requires revalidation."
        )
    return {
        "summary": f"{len(knowledge)} verified, accessible handover items."
        if report.get("knowledge")
        else "Generate a handover after verifying evidence.",
        "knowledge": knowledge,
        "unknowns": unknowns,
        "risks": find_gaps(db, user, transition.project_id),
        "generated_at": report.get("generated_at"),
        "prerequisites": readable_prerequisites(db, user, transition),
        "recovery_history": [
            {k: h[k] for k in ("version", "reopened_at") if k in h}
            for h in report.get("recovery_history", [])
        ],
        "version_history": [
            {k: h[k] for k in ["version", "generated_at"] if k in h} for h in report.get("history", [])
        ],
        "source_ids": sorted({e["source_id"] for c in knowledge for e in c["evidence"]}),
    }


def serialize_transfer(db: Session, transfer: m.Transfer) -> dict:
    claim = db.get(m.Claim, transfer.claim_id)
    return {
        "id": transfer.id,
        "claim_id": transfer.claim_id,
        "title": claim.title if claim else "Evidence unavailable",
        "successor_id": transfer.successor_id,
        "backup_id": transfer.backup_id,
        "status": transfer.status,
        "note": transfer.note,
    }


def serialize_exercise(exercise: m.Exercise) -> dict:
    return {
        "id": exercise.id,
        "transfer_id": exercise.transfer_id,
        "title": exercise.title,
        "prompt": exercise.prompt,
        "criteria": exercise.criteria,
        "expected_source_ids": exercise.expected_source_ids,
        "status": exercise.status,
        "answer": exercise.answer,
        "evidence_ids": exercise.evidence_ids,
        "escalation": exercise.escalation,
        "supervisor_note": exercise.supervisor_note,
        "assessment": exercise.assessment,
    }


def serialize_transition(db: Session, user: m.User, transition: m.Transition) -> dict:
    claims = {c.id for c in current_claims(db, user, transition.project_id)}
    transfers = list(
        db.scalars(
            select(m.Transfer)
            .where(m.Transfer.transition_id == transition.id)
            .order_by(m.Transfer.created_at)
        )
    )
    accessible = [t for t in transfers if t.claim_id in claims]
    exercises = list(
        db.scalars(
            select(m.Exercise)
            .where(m.Exercise.transition_id == transition.id)
            .order_by(m.Exercise.created_at)
        )
    )
    report = readable_report(db, user, transition)
    source_ids = set(report.get("source_ids", []))
    visible_ids = {s.id for s in visible_sources(db, user, transition.project_id) if s.status == "ready"}
    return {
        "id": transition.id,
        "title": transition.title,
        "departing_id": transition.departing_id,
        "successor_id": transition.successor_id,
        "departure_date": transition.departure_date,
        "status": transition.status,
        "version": transition.version,
        "report": report,
        "transfers": [serialize_transfer(db, t) for t in accessible],
        "exercises": [
            serialize_exercise(e)
            for e in exercises
            if set(e.expected_source_ids).issubset(source_ids)
            and set(e.assessment.get("staging_source_versions", {})).issubset(visible_ids)
        ],
    }


def generate_handover(db: Session, user: m.User, transition: m.Transition) -> m.Transition:
    project_access(db, user, transition.project_id, write=True)
    require_role(user, {"admin", "manager", "lead"})
    if transition.status in {"approved", "in_progress", "closed"}:
        raise HTTPException(
            409,
            "An approved handover is frozen. Create a new transition to revise transferred responsibilities.",
        )
    verified = current_claims(db, user, transition.project_id, verified=True)
    successor = project_person(db, user, transition.project_id, transition.successor_id)
    successor_ids = {c.id for c in current_claims(db, successor, transition.project_id, verified=True)}
    verified = [c for c in verified if c.id in successor_ids]
    if not verified:
        raise HTTPException(
            409,
            "Verify at least one claim that the incoming employee can access before generating a handover.",
        )
    knowledge = [serialize_claim(db, user, c) for c in verified]
    history = list((transition.report or {}).get("history", []))
    version = transition.version + 1
    now = m.utcnow().isoformat()
    history.append(
        {
            "version": version,
            "generated_at": now,
            "claim_count": len(knowledge),
            "claim_ids": [c.id for c in verified],
        }
    )
    selected_ids = {c.id for c in verified}
    # Changed-source candidates get new IDs. Preserve old records as historical,
    # while excluding them from the new version's completion requirements.
    for transfer in db.scalars(select(m.Transfer).where(m.Transfer.transition_id == transition.id)):
        if transfer.claim_id not in selected_ids:
            transfer.status = "superseded"
    for exercise in db.scalars(select(m.Exercise).where(m.Exercise.transition_id == transition.id)):
        if exercise.assessment.get("claim_id") not in selected_ids:
            exercise.status = "superseded"
    transition.report = jsonable_encoder(
        {
            "summary": f"Handover for {transition.title}: {len(knowledge)} verified, accessible knowledge items.",
            "prerequisites": (transition.report or {}).get("prerequisites", []),
            "recovery_history": (transition.report or {}).get("recovery_history", []),
            "knowledge": knowledge,
            "source_ids": sorted({e["source_id"] for c in knowledge for e in c["evidence"]}),
            "unknowns": [
                "Unverified, rejected, stale-version and inaccessible knowledge was excluded.",
                "Ownership acceptance and supervisor-reviewed practical validation are still required.",
            ],
            "generated_at": now,
            "history": history,
            "source_versions": {
                e["source_id"]: e["source_version"] for c in knowledge for e in c["evidence"]
            },
            "claim_signatures": {claim.id: claim_signature(claim) for claim in verified},
        }
    )
    transition.version, transition.status = version, "generated"
    audit(
        db,
        user,
        transition.project_id,
        "handover.generated",
        "transition",
        transition.id,
        {"version": version, "verified_claims": len(knowledge)},
    )
    return transition


def reopen_handover(db, user, transition, note):
    project_access(db, user, transition.project_id, write=True)
    if transition.status not in {"approved", "in_progress"}:
        raise HTTPException(
            409,
            "Reopen an approved active handover. Closed ownership requires a separate follow-up transition.",
        )
    recovery = list((transition.report or {}).get("recovery_history", []))
    recovery.append(
        {"version": transition.version, "reopened_at": m.utcnow().isoformat(), "actor_id": user.id}
    )
    for transfer in db.scalars(select(m.Transfer).where(m.Transfer.transition_id == transition.id)):
        audit(
            db,
            user,
            transition.project_id,
            "transfer.reopened",
            "transfer",
            transfer.id,
            {"previous_status": transfer.status, "version": transition.version},
        )
        transfer.status, transfer.accepted_at = "assigned", None
    for exercise in db.scalars(select(m.Exercise).where(m.Exercise.transition_id == transition.id)):
        prior = list(exercise.assessment.get("review_history", []))
        prior.append(
            {"status": exercise.status, "reviewed_by": exercise.reviewed_by, "version": transition.version}
        )
        exercise.assessment = {**exercise.assessment, "review_history": prior}
        exercise.status, exercise.reviewed_by = "needs_revision", None
    transition.report = {**transition.report, "recovery_history": recovery}
    transition.status = "reopened"
    audit(
        db,
        user,
        transition.project_id,
        "handover.reopened",
        "transition",
        transition.id,
        {"version": transition.version, "note": note},
    )
    return transition


def assign_responsibility(
    db: Session,
    user: m.User,
    transition: m.Transition,
    claim_id: str,
    successor_id: str,
    backup_id: str | None,
) -> m.Transfer:
    project_access(db, user, transition.project_id, write=True)
    require_role(user, {"admin", "manager", "lead"})
    if transition.status not in {"approved", "in_progress"}:
        raise HTTPException(409, "Approve the handover before assigning responsibility.")
    successor = project_person(db, user, transition.project_id, successor_id)
    if successor_id != transition.successor_id:
        raise HTTPException(
            422, "This handover validates one incoming employee. Select the transition’s assigned successor."
        )
    if successor.id == transition.departing_id:
        raise HTTPException(422, "The departing employee cannot receive their own transfer.")
    if backup_id:
        project_person(db, user, transition.project_id, backup_id)
        if backup_id in {successor_id, transition.departing_id}:
            raise HTTPException(422, "Select a distinct available backup owner.")
    current = {c.id: c for c in current_claims(db, user, transition.project_id, verified=True)}
    allowed = {c.id for c in current_claims(db, successor, transition.project_id, verified=True)}
    snapshot = {c["id"] for c in (transition.report or {}).get("knowledge", [])}
    claim = current.get(claim_id)
    if not claim or claim.kind != "responsibility" or claim_id not in allowed or claim_id not in snapshot:
        raise HTTPException(
            422, "Assign only verified handover responsibilities accessible to the successor."
        )
    if claim.data.get("owner_id") != transition.departing_id:
        raise HTTPException(
            422, "This responsibility is not confirmed as belonging to the departing employee."
        )
    duplicate = db.scalar(
        select(m.Transfer).where(m.Transfer.transition_id == transition.id, m.Transfer.claim_id == claim_id)
    )
    if duplicate:
        if duplicate.status == "accepted":
            raise HTTPException(409, "Accepted ownership cannot be silently reassigned.")
        duplicate.successor_id, duplicate.backup_id, duplicate.status, duplicate.note = (
            successor_id,
            backup_id,
            "assigned",
            "",
        )
        transfer = duplicate
    else:
        transfer = m.Transfer(
            org_id=transition.org_id,
            project_id=transition.project_id,
            transition_id=transition.id,
            claim_id=claim_id,
            successor_id=successor_id,
            backup_id=backup_id,
            status="assigned",
            note="",
        )
        db.add(transfer)
        db.flush()
    transition.status = "in_progress"
    audit(
        db,
        user,
        transition.project_id,
        "responsibility.assigned",
        "transfer",
        transfer.id,
        {"successor_id": successor_id, "claim_id": claim_id},
    )
    return transfer


def generate_exercises(db: Session, user: m.User, transition: m.Transition) -> m.Transition:
    project_access(db, user, transition.project_id, write=True)
    require_role(user, {"admin", "manager", "lead"})
    if transition.status not in {"approved", "in_progress"}:
        raise HTTPException(409, "Approve the handover before generating practical validation tasks.")
    existing = list(db.scalars(select(m.Exercise).where(m.Exercise.transition_id == transition.id)))
    existing = [e for e in existing if e.status != "superseded"]
    existing_transfers = {exercise.transfer_id for exercise in existing if exercise.transfer_id}
    existing_claims = {
        exercise.assessment.get("claim_id") for exercise in existing if not exercise.transfer_id
    }
    report_ids = {c["id"] for c in (transition.report or {}).get("knowledge", [])}
    selected = [
        c
        for c in current_claims(db, user, transition.project_id, verified=True)
        if c.id in report_ids and c.kind in {"procedure", "dependency", "incident"}
    ]
    transfers = list(
        db.scalars(
            select(m.Transfer).where(
                m.Transfer.transition_id == transition.id, m.Transfer.status != "superseded"
            )
        )
    )
    if not selected and not transfers:
        raise HTTPException(
            409, "Verify a procedure, dependency or unresolved incident before creating practical exercises."
        )
    added = 0
    for transfer in transfers:
        if transfer.id in existing_transfers:
            continue
        claim = db.get(m.Claim, transfer.claim_id)
        refs = citations(db, user, claim)
        if claim.status != "verified" or not refs:
            continue
        component = claim.data.get("component", "")
        related = [
            item
            for item in selected
            if item.kind == "procedure"
            and component
            and component.casefold() in (item.title + " " + item.summary).casefold()
        ]
        related_refs = [ref for item in related[:1] for ref in citations(db, user, item)]
        db.add(
            m.Exercise(
                org_id=transition.org_id,
                project_id=transition.project_id,
                transition_id=transition.id,
                transfer_id=transfer.id,
                title="Validate responsibility: " + claim.title,
                prompt=f"Explain how you would safely continue “{claim.title}”. Locate its responsibility and operational evidence, identify missing procedures and prerequisites, describe a test-environment walkthrough, and explain when you must request human help. Do not execute production operations.",
                criteria=scenario_criteria(claim),
                expected_source_ids=sorted({ref["source_id"] for ref in refs + related_refs}),
                status="pending",
                answer="",
                evidence_ids=[],
                escalation="",
                supervisor_note="",
                assessment={
                    "claim_id": claim.id,
                    "transfer_id": transfer.id,
                    "type": "human_review_required",
                    "rubric_version": "scenario-v2",
                },
            )
        )
        added += 1
    for claim in selected[:3]:
        if claim.id in existing_claims:
            continue
        refs = citations(db, user, claim)
        prompt = f"Using the handover sources, explain “{claim.title}”. Locate the cited evidence, identify prerequisites and unresolved risks, and describe when you would escalate. Describe a safe test-environment walkthrough. Do not run production operations."
        db.add(
            m.Exercise(
                org_id=transition.org_id,
                project_id=transition.project_id,
                transition_id=transition.id,
                title=f"Validate: {claim.title}",
                prompt=prompt,
                criteria=scenario_criteria(claim),
                expected_source_ids=sorted({e["source_id"] for e in refs}),
                status="pending",
                answer="",
                evidence_ids=[],
                escalation="",
                supervisor_note="",
                assessment={
                    "claim_id": claim.id,
                    "type": "human_review_required",
                    "rubric_version": "scenario-v2",
                },
            )
        )
    audit(
        db,
        user,
        transition.project_id,
        "validation.exercises_created",
        "transition",
        transition.id,
        {"count": added + sum(claim.id not in existing_claims for claim in selected[:3])},
    )
    return transition


def readiness(db: Session, user: m.User, transition: m.Transition) -> dict:
    claims = {c.id: c for c in current_claims(db, user, transition.project_id, verified=True)}
    snapshot = (transition.report or {}).get("knowledge", [])
    expected = {
        c["id"]
        for c in snapshot
        if c["kind"] == "responsibility" and c["data"].get("owner_id") == transition.departing_id
    }
    transfers = list(db.scalars(select(m.Transfer).where(m.Transfer.transition_id == transition.id)))
    exercises = list(db.scalars(select(m.Exercise).where(m.Exercise.transition_id == transition.id)))
    transfers = [t for t in transfers if t.status != "superseded"]
    exercises = [e for e in exercises if e.status != "superseded"]
    visible_transfer_ids = {t.id for t in transfers if t.claim_id in claims}
    accepted = [t for t in transfers if t.status == "accepted" and t.id in visible_transfer_ids]
    validated = [e for e in exercises if e.status == "passed" and e.assessment.get("claim_id") in claims]
    blockers = []
    try:
        successor = project_person(db, user, transition.project_id, transition.successor_id)
        successor_ids = {c.id for c in current_claims(db, successor, transition.project_id, verified=True)}
    except HTTPException:
        successor_ids = set()
    if any(item["id"] not in successor_ids for item in snapshot):
        blockers.append(
            "The incoming owner cannot access all current handover evidence; restore authorised access and revalidate."
        )
    prerequisites = (transition.report or {}).get("prerequisites", [])
    public_checks = {i["id"]: i for i in readable_prerequisites(db, user, transition)}
    for item in prerequisites:
        if item.get("required") and item.get("status") != "confirmed":
            blockers.append("Required prerequisite incomplete: " + public_checks[item["id"]]["title"])
    if not snapshot:
        blockers.append("A verified handover has not been generated.")
    if transition.status not in {"approved", "in_progress", "closed"}:
        blockers.append("Manager approval is required.")
    if not expected:
        blockers.append("No verified departing-employee responsibilities have been included.")
    if expected - {t.claim_id for t in accepted}:
        blockers.append(
            "Every departing-employee responsibility requires assignment and successor acceptance."
        )
    if not exercises:
        blockers.append("Practical validation tasks have not been created.")
    if len(validated) < len(exercises):
        blockers.append("Every practical validation task requires supervisor approval.")
    if {transfer.id for transfer in accepted} - {
        exercise.transfer_id for exercise in validated if exercise.transfer_id
    }:
        blockers.append(
            "Every accepted responsibility requires its own supervisor-validated practical exercise."
        )
    source_versions = (transition.report or {}).get("source_versions", {})
    evidence = [e for c in claims.values() for e in citations(db, user, c)]
    current_versions = {e["source_id"]: e["source_version"] for e in evidence}
    if any(current_versions.get(sid) != version for sid, version in source_versions.items()):
        blockers.append(
            "Handover sources changed, were revoked or are inaccessible; revalidation is required."
        )
    valid_refs = {e["id"] for e in evidence}
    for exercise in validated:
        if not set(exercise.assessment.get("staging_evidence_ids", [])).issubset(valid_refs) or any(
            current_versions.get(sid) != version
            for sid, version in exercise.assessment.get("staging_source_versions", {}).items()
        ):
            blockers.append(
                "Staging observation evidence changed or is unavailable; repeat supervisor review."
            )
    for item in prerequisites:
        if (
            item.get("required")
            and item.get("status") == "confirmed"
            and (
                not item.get("evidence_ids")
                or not set(item["evidence_ids"]).issubset(valid_refs)
                or any(
                    current_versions.get(sid) != version
                    for sid, version in item.get("source_versions", {}).items()
                )
            )
        ):
            blockers.append(
                "Prerequisite evidence requires revalidation: " + public_checks[item["id"]]["title"]
            )
    if any(item["id"] not in claims for item in snapshot):
        blockers.append("Some handover claims are no longer verified or accessible.")
    if transition.status != "closed" and any(
        claim_id not in claims or claim_signature(claims[claim_id]) != signature
        for claim_id, signature in (transition.report or {}).get("claim_signatures", {}).items()
    ):
        blockers.append("Approved knowledge was corrected; generate a new reviewed handover before closure.")
    return {
        "accepted": len(accepted),
        "total": len(expected),
        "validated": len(validated),
        "exercise_total": len(exercises),
        "ready": not blockers,
        "blockers": blockers,
        "prerequisites": list(public_checks.values()),
        "evidence_coverage": {
            "numerator": sum(item["id"] in claims for item in snapshot),
            "denominator": len(snapshot),
        },
        "limitations": [
            "Readiness measures acceptance and evidence-based supervisor review; it does not prove independent real-world competence."
        ],
    }


def record_ownership_transfer(db, user, transition):
    """Manager closure records already accepted and supervisor-validated ownership."""
    sources = {source.id: source for source in visible_sources(db, user, transition.project_id)}
    for transfer in db.scalars(
        select(m.Transfer).where(m.Transfer.transition_id == transition.id, m.Transfer.status == "accepted")
    ):
        claim = db.get(m.Claim, transfer.claim_id)
        successor = db.get(m.User, transfer.successor_id)
        previous_owner = db.get(m.User, claim.data.get("owner_id"))
        backup = db.get(m.User, transfer.backup_id) if transfer.backup_id else None
        refs = citations(db, user, claim)
        restricted = [set(sources[ref["source_id"]].acl) for ref in refs if sources[ref["source_id"]].acl]
        acl = sorted(set.intersection(*restricted)) if restricted else []
        body = (
            f"Responsibility ownership transfer: {claim.title}\n"
            f"Previous owner: {previous_owner.name if previous_owner else 'Unknown'}\n"
            f"Accepted incoming owner: {successor.name}\n"
            f"Backup: {backup.name if backup else 'No backup assigned'}\n"
            f"Transition: {transition.id}\nTransfer acceptance: {transfer.id}\n"
            f"Manager closure: {user.name}\n"
            "All practical exercises were separately validated by an authorised supervisor. "
            "This record establishes accepted responsibility; it does not guarantee operational competence."
        )
        source = m.Source(
            org_id=user.org_id,
            project_id=transition.project_id,
            name="Accepted ownership: " + claim.title[:180],
            kind="ownership_transfer",
            status="ready",
            acl=acl,
            version=1,
            synthetic=db.get(m.Project, transition.project_id).is_demo,
            checksum=hashlib.sha256(body.encode()).hexdigest(),
            source_metadata={
                "transition_id": transition.id,
                "transfer_id": transfer.id,
                "recorded_by": user.id,
                "lineage_source_ids": [ref["source_id"] for ref in refs],
            },
        )
        db.add(source)
        db.flush()
        chunk = m.Chunk(
            org_id=user.org_id,
            project_id=transition.project_id,
            source_id=source.id,
            source_version=1,
            ordinal=0,
            locator="Human acceptance and supervisor validation record",
            text=body,
        )
        db.add(chunk)
        db.flush()
        db.add(
            m.Evidence(
                org_id=user.org_id,
                project_id=transition.project_id,
                claim_id=claim.id,
                source_id=source.id,
                source_version=1,
                chunk_id=chunk.id,
                quote=body,
            )
        )
        claim.data = {
            **claim.data,
            "previous_owner_id": claim.data.get("owner_id"),
            "owner_id": successor.id,
            "backup_id": transfer.backup_id,
            "ownership_provenance": source.id,
            "ownership_effective_at": m.utcnow().isoformat(),
        }
        claim.summary += (
            "\n\nCurrent accepted ownership: "
            + successor.name
            + ". See the human transfer record; original source statements remain historical evidence."
        )
        audit(
            db,
            user,
            transition.project_id,
            "ownership.transferred",
            "claim",
            claim.id,
            {
                "transfer_id": transfer.id,
                "previous_owner_id": previous_owner.id if previous_owner else None,
                "current_owner_id": successor.id,
                "provenance_source_id": source.id,
            },
        )
