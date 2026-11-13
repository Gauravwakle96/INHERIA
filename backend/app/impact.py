"""Permission-filtered source → claim → transition/exercise change lineage."""

from sqlalchemy import select

from app import models as m
from app.security import can_read_source, project_access, source_descendant_ids


def source_impact(db, user, project_id, source_id):
    from fastapi import HTTPException

    project_access(db, user, project_id)
    source = db.get(m.Source, source_id)
    if (
        not source
        or source.project_id != project_id
        or not can_read_source(db, user, source, include_inactive=True)
    ):
        raise HTTPException(404, "Source impact unavailable.")
    related_ids = source_descendant_ids(db, source)
    refs = list(db.scalars(select(m.Evidence).where(m.Evidence.source_id.in_(related_ids))))
    claim_ids = {e.claim_id for e in refs}
    claims = []
    for claim in db.scalars(select(m.Claim).where(m.Claim.id.in_(claim_ids))):
        other_ids = set(db.scalars(select(m.Evidence.source_id).where(m.Evidence.claim_id == claim.id)))
        if any(
            not can_read_source(db, user, db.get(m.Source, sid), include_inactive=True) for sid in other_ids
        ):
            continue
        claims.append(
            {
                "id": claim.id,
                "title": claim.title,
                "status": claim.status,
                "evidence_versions": sorted({e.source_version for e in refs if e.claim_id == claim.id}),
            }
        )
    visible_claim_ids = {c["id"] for c in claims}
    transitions = []
    exercises = []
    for transition in db.scalars(select(m.Transition).where(m.Transition.project_id == project_id)):
        report = transition.report or {}
        all_sources = report.get("source_ids", [])
        if not related_ids.intersection(all_sources) or any(
            not can_read_source(db, user, db.get(m.Source, sid), include_inactive=True) for sid in all_sources
        ):
            continue
        transitions.append(
            {
                "id": transition.id,
                "title": transition.title,
                "status": transition.status,
                "version": transition.version,
                "requires_revalidation": bool(report.get("requires_revalidation")),
            }
        )
    for exercise in db.scalars(select(m.Exercise).where(m.Exercise.project_id == project_id)):
        if (
            exercise.assessment.get("claim_id") in visible_claim_ids
            or related_ids.intersection(exercise.expected_source_ids)
            or related_ids.intersection(exercise.assessment.get("staging_source_versions", {}))
        ):
            if all(
                can_read_source(db, user, db.get(m.Source, sid), include_inactive=True)
                for sid in set(exercise.expected_source_ids)
                | set(exercise.assessment.get("staging_source_versions", {}))
            ):
                exercises.append({"id": exercise.id, "title": exercise.title, "status": exercise.status})
    return {
        "source_id": source.id,
        "source_name": source.name,
        "version": source.version,
        "claims": claims,
        "transitions": transitions,
        "exercises": exercises,
        "next_action": "Investigate the current source, independently review new claims, then reopen affected handovers for reapproval and practical reassessment.",
    }
