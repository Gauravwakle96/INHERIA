"""Erase source-derived text when deletion is requested, including report snapshots."""

from sqlalchemy import delete, select

from app import models as m
from app.security import source_descendant_ids


def purge_source_derivatives(db, source):
    related_ids = source_descendant_ids(db, source)
    descendants = list(db.scalars(select(m.Source).where(m.Source.project_id == source.project_id)))
    claim_ids = set(db.scalars(select(m.Evidence.claim_id).where(m.Evidence.source_id.in_(related_ids))))
    affected_resources = set(claim_ids) | related_ids
    # Conversation follow-ups inherit cumulative provenance so source deletion
    # erases both the original answer and text derived through later turns.
    for turn in db.scalars(select(m.ChatTurn).where(m.ChatTurn.project_id == source.project_id)):
        if related_ids.intersection(turn.provenance.get("sources", {})):
            turn.question = "Source evidence deleted"
            turn.response = {
                "answer": "Source evidence was deleted. Ask again using current sources.",
                "parts": [],
                "citation_ids": [],
                "known": False,
                "engine": "evidence_deleted",
                "unknowns": [],
            }
            turn.provenance = {}
            db.execute(delete(m.ChatAction).where(m.ChatAction.turn_id == turn.id))
    for child in descendants:
        if child.id in related_ids and child.id != source.id:
            db.execute(delete(m.Evidence).where(m.Evidence.source_id == child.id))
            db.execute(delete(m.Chunk).where(m.Chunk.source_id == child.id))
            child.name, child.status, child.source_metadata = (
                "Source lineage removed",
                "revoked",
                {"source_content_removed": True},
            )
    for claim in db.scalars(select(m.Claim).where(m.Claim.id.in_(claim_ids))):
        claim.title, claim.summary, claim.data, claim.status = (
            "Source removed",
            "Source evidence was deleted.",
            {},
            "invalidated",
        )
        claim.verified_by, claim.verified_at = None, None
    for gap in db.scalars(select(m.Gap).where(m.Gap.project_id == source.project_id)):
        if related_ids.intersection(gap.source_ids) or gap.claim_id in claim_ids:
            affected_resources.add(gap.id)
            gap.title, gap.details, gap.question, gap.note = (
                "Source removed",
                "Supporting source was deleted.",
                "",
                "",
            )
            gap.source_ids, gap.status = [], "invalidated"
    for run in db.scalars(select(m.Investigation).where(m.Investigation.project_id == source.project_id)):
        report = run.report or {}
        if any(related_ids.intersection(f.get("source_ids", [])) for f in report.get("findings", [])):
            affected_resources.add(run.id)
            run.report = {
                "summary": "Investigation evidence was removed. Run a new authorised investigation.",
                "findings": [],
                "questions": [],
                "unknowns": ["Source deletion invalidated this report."],
                "engine": report.get("engine", "deterministic-v1"),
                "limitations": [],
            }
    for transition in db.scalars(select(m.Transition).where(m.Transition.project_id == source.project_id)):
        report = transition.report or {}
        if related_ids.intersection(report.get("source_ids", [])) or any(
            item["id"] in claim_ids for item in report.get("knowledge", [])
        ):
            affected_resources.add(transition.id)
            transition.report = {
                **report,
                "knowledge": [item for item in report.get("knowledge", []) if item["id"] not in claim_ids],
                "unknowns": ["Source deletion invalidated handover evidence; regenerate and revalidate."],
            }
            if transition.status != "closed":
                transition.status = "needs_review"
    for simulation in db.scalars(select(m.Simulation).where(m.Simulation.project_id == source.project_id)):
        if related_ids.intersection((simulation.report or {}).get("source_ids", [])):
            affected_resources.add(simulation.id)
            simulation.report = {
                "hypothetical": True,
                "summary": "Simulation evidence was deleted. Re-run with available sources.",
                "affected": [],
                "recommendations": [],
                "unknowns": ["Prior evidence was removed."],
                "source_ids": [],
            }
    for exercise in db.scalars(select(m.Exercise).where(m.Exercise.project_id == source.project_id)):
        if (
            related_ids.intersection(exercise.expected_source_ids)
            or related_ids.intersection(exercise.assessment.get("staging_source_versions", {}))
            or exercise.assessment.get("claim_id") in claim_ids
        ):
            affected_resources.add(exercise.id)
            exercise.title, exercise.prompt = (
                "Source removed",
                "Regenerate validation using current evidence.",
            )
            exercise.answer, exercise.escalation, exercise.supervisor_note = "", "", ""
            exercise.evidence_ids, exercise.assessment, exercise.status = [], {}, "needs_revision"
    # Comments may repeat source text; discard details for directly derived audit events.
    for event in db.scalars(select(m.Audit).where(m.Audit.project_id == source.project_id)):
        if event.resource_id in affected_resources:
            event.details = {"source_content_removed": True}
    db.flush()
