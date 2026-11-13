"""Permission-filtered completion and contribution facts from persisted workflow records."""

from sqlalchemy import select

from app import models as m
from app.intelligence import current_claims
from app.security import project_access, visible_sources
from app.transfer import readiness, serialize_transition


def continuity_summary(db, user, project_id):
    project_access(db, user, project_id)
    claims = current_claims(db, user, project_id)
    claim_ids = {claim.id for claim in claims}
    sources = visible_sources(db, user, project_id)
    ready_source_ids = {source.id for source in sources if source.status == "ready"}
    exercises = [
        exercise
        for exercise in db.scalars(select(m.Exercise).where(m.Exercise.project_id == project_id))
        if exercise.status != "superseded"
        and exercise.assessment.get("claim_id") in claim_ids
        and set(exercise.expected_source_ids).issubset(ready_source_ids)
        and set(exercise.assessment.get("staging_source_versions", {})).issubset(ready_source_ids)
    ]
    transfers = [
        transfer
        for transfer in db.scalars(select(m.Transfer).where(m.Transfer.project_id == project_id))
        if transfer.status == "accepted" and transfer.claim_id in claim_ids
    ]
    member_ids = select(m.Membership.user_id).where(m.Membership.project_id == project_id)
    people = list(
        db.scalars(
            select(m.User)
            .where(m.User.id.in_(member_ids), m.User.org_id == user.org_id)
            .order_by(m.User.name)
        )
    )
    contributors = []
    for person in people:
        contributors.append(
            {
                "id": person.id,
                "name": person.name,
                "interviews": sum(
                    source.kind == "interview"
                    and source.status == "ready"
                    and source.source_metadata.get("author_id") == person.id
                    for source in sources
                ),
                "knowledge_reviewed": sum(claim.verified_by == person.id for claim in claims),
                "responsibilities_owned": sum(
                    claim.kind == "responsibility" and claim.data.get("owner_id") == person.id
                    for claim in claims
                ),
                "responsibilities_accepted": sum(
                    transfer.successor_id == person.id for transfer in transfers
                ),
                "responsibilities_transferred": sum(
                    claim.kind == "responsibility"
                    and claim.data.get("previous_owner_id") == person.id
                    and claim.data.get("ownership_provenance") in ready_source_ids
                    for claim in claims
                ),
                "backup_responsibilities": sum(
                    claim.kind == "responsibility" and claim.data.get("backup_id") == person.id
                    for claim in claims
                ),
                "walkthroughs_submitted": sum(
                    exercise.assessment.get("submitted_by") == person.id for exercise in exercises
                ),
                "walkthroughs_reviewed": sum(
                    exercise.reviewed_by == person.id and exercise.status == "passed"
                    for exercise in exercises
                ),
            }
        )
    closed_records = list(
        db.scalars(
            select(m.Transition)
            .where(m.Transition.project_id == project_id, m.Transition.status == "closed")
            .order_by(m.Transition.updated_at.desc())
        )
    )
    closed = [
        record
        for record in closed_records
        if set(item["id"] for item in (record.report or {}).get("knowledge", [])).issubset(claim_ids)
        and set((record.report or {}).get("source_ids", [])).issubset(ready_source_ids)
    ]
    latest = closed[0] if closed else None
    completion = None
    if latest:
        report = readiness(db, user, latest)
        visible = serialize_transition(db, user, latest)
        names = {person.id: person.name for person in people}
        completion = {
            "id": latest.id,
            "title": latest.title,
            "departing_name": names.get(latest.departing_id, "Departing participant"),
            "successor_name": names.get(latest.successor_id, "Incoming participant"),
            "version": latest.version,
            "closed_at": latest.updated_at,
            "accepted": report["accepted"],
            "total": report["total"],
            "validated": report["validated"],
            "exercise_total": report["exercise_total"],
            "current": report["ready"],
            "knowledge_items": len(visible["report"]["knowledge"]),
        }
    return {
        "completed_handovers": len(closed),
        "completion": completion,
        "contributors": contributors,
        "scope": "Completion records responsibility acceptance and reviewed knowledge walkthroughs. Open work, external access and real operational tests require separate follow-up.",
    }
