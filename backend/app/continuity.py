"""Hypothetical continuity analysis and measured readiness, without production actions."""

from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models as m
from app.intelligence import RESOLVED_STATUSES, citations, current_claims
from app.security import project_access, visible_sources


def project_person(db: Session, user: m.User, project_id: str, user_id: str) -> m.User:
    project_access(db, user, project_id)
    person = db.get(m.User, user_id)
    member = db.scalar(
        select(m.Membership).where(m.Membership.project_id == project_id, m.Membership.user_id == user_id)
    )
    if not person or person.org_id != user.org_id or not member or not person.active:
        raise HTTPException(422, "Select an active authorised project member.")
    return person


def simulation_report(
    db: Session, user: m.User, project_id: str, employee_id: str, scenario: str, component: str = ""
) -> dict:
    person = project_person(db, user, project_id, employee_id)
    if scenario == "dependency_failure" and not component.strip():
        raise HTTPException(422, "Choose the component to simulate a dependency failure.")
    claims = current_claims(db, user, project_id)
    responsibilities = [
        c for c in claims if c.kind == "responsibility" and c.data.get("owner_id") == employee_id
    ]
    if scenario == "dependency_failure" and component:
        responsibilities = [
            c
            for c in claims
            if c.kind == "responsibility" and component.casefold() in c.data.get("component", "").casefold()
        ]
    affected, recommendations, unknowns = [], [], []
    dependencies = [c for c in claims if c.kind == "dependency" and c.status == "verified"]
    affected_systems = {c.data.get("component", "") for c in responsibilities if c.data.get("component")}
    if component and scenario == "dependency_failure":
        affected_systems.add(component)
    changed = True
    while changed:
        changed = False
        for claim in dependencies:
            origin, target = claim.data.get("from_component"), claim.data.get("to_component")
            if origin and target in affected_systems and origin not in affected_systems:
                affected_systems.add(origin)
                changed = True
    for claim in claims:
        if (
            claim.kind == "responsibility"
            and claim.data.get("component") in affected_systems
            and claim not in responsibilities
        ):
            responsibilities.append(claim)
    sources = {s.id: s for s in visible_sources(db, user, project_id) if s.status == "ready"}
    for responsibility in responsibilities:
        data = responsibility.data
        backup = db.get(m.User, data.get("backup_id")) if data.get("backup_id") else None
        owner = db.get(m.User, data.get("owner_id")) if data.get("owner_id") else None
        valid_backup = (
            backup
            and backup.active
            and (backup.id != employee_id or scenario != "unavailability")
            and backup.org_id == user.org_id
        )
        component_name = data.get("component", "")
        procedures = [
            c
            for c in claims
            if c.kind == "procedure"
            and component_name
            and component_name.casefold() in (c.title + " " + c.summary).casefold()
        ]
        risks = []
        if not valid_backup:
            risks.append("No available backup owner is recorded in accessible evidence.")
            recommendations.append(f"Ask a manager to confirm and train a backup for {responsibility.title}.")
        else:
            recommendations.append(
                f"Confirm {backup.name} can safely cover {responsibility.title}; recorded ownership does not establish readiness."
            )
        if not procedures:
            risks.append("No matching operational procedure was found in the authorised sources.")
            recommendations.append(f"Capture and safely validate a playbook for {responsibility.title}.")
        if any(c.status != "verified" for c in procedures):
            risks.append("Related procedures remain unverified.")
        stale = any(
            sources[e["source_id"]].source_time
            and sources[e["source_id"]].source_time < m.utcnow() - timedelta(days=180)
            for c in procedures
            for e in citations(db, user, c)
        )
        if stale:
            risks.append("Related procedure evidence is older than 180 days and requires revalidation.")
        if (
            scenario == "outdated_procedure"
            and not stale
            and not any(c.status != "verified" for c in procedures)
        ):
            continue
        if scenario == "dependency_failure":
            risks.append(
                f"The scenario assumes {component} is unavailable; dependency effects are hypothetical."
            )
        if responsibility.status != "verified":
            risks.append("The ownership relationship is pending human verification; impact is uncertain.")
        refs = citations(db, user, responsibility)
        refs.extend(e for c in procedures for e in citations(db, user, c))
        refs.extend(
            e
            for c in dependencies
            if c.data.get("from_component") == component_name or c.data.get("to_component") == component_name
            for e in citations(db, user, c)
        )
        affected.append(
            {
                "responsibility_id": responsibility.id,
                "title": responsibility.title,
                "system": component_name or "System not established",
                "critical": bool(data.get("critical")),
                "owner": owner.name if owner else "Unknown",
                "backup": backup.name if valid_backup else None,
                "status": responsibility.status,
                "risks": risks,
                "evidence": refs,
            }
        )
    if not affected:
        unknowns.append(
            "No supported ownership relationship matched this scenario. A zero count does not imply continuity is safe."
        )
    unknowns.extend(
        [
            "No precise outage duration or financial impact can be inferred from this evidence.",
            "Unrecorded dependencies and operational access may change the outcome.",
            "This simulation makes no changes to production systems or ownership.",
        ]
    )
    summaries = {
        "unavailability": f"What if {person.name} were unavailable?",
        "dependency_failure": f"Hypothetical dependency failure: {component}.",
        "outdated_procedure": f"What if unverified or stale procedures for {person.name} could not be relied upon?",
    }
    return {
        "hypothetical": True,
        "summary": summaries[scenario] + f" {len(affected)} recorded responsibilities require assessment.",
        "affected": affected,
        "recommendations": list(dict.fromkeys(recommendations)),
        "unknowns": unknowns,
        "affected_systems": sorted(affected_systems),
        "source_ids": sorted({e["source_id"] for row in affected for e in row["evidence"]}),
    }


def metrics(db: Session, user: m.User, project_id: str) -> list[dict]:
    claims = current_claims(db, user, project_id)
    sources = [s for s in visible_sources(db, user, project_id) if s.status == "ready"]
    source_ids = {s.id for s in sources}
    responsibilities = [c for c in claims if c.kind == "responsibility"]
    gaps = [
        g
        for g in db.scalars(select(m.Gap).where(m.Gap.project_id == project_id))
        if set(g.source_ids).issubset(source_ids) and (not g.claim_id or g.claim_id in {c.id for c in claims})
    ]
    transfers = [
        t
        for t in db.scalars(select(m.Transfer).where(m.Transfer.project_id == project_id))
        if t.claim_id in {c.id for c in claims}
    ]
    verified = current_claims(db, user, project_id, verified=True)
    stale = [s for s in sources if s.source_time and s.source_time < m.utcnow() - timedelta(days=180)]

    def count(key, label, value, description):
        return {
            "key": key,
            "label": label,
            "value": value,
            "numerator": value,
            "denominator": None,
            "description": description,
        }

    def ratio(key, label, numerator, denominator, description):
        return {
            "key": key,
            "label": label,
            "value": round(numerator / denominator * 100) if denominator else None,
            "numerator": numerator,
            "denominator": denominator,
            "description": description,
        }

    return [
        count(
            "knowledge_gaps",
            "Open knowledge gaps",
            sum(g.status in {"open", "in_progress"} for g in gaps),
            "Open or in-progress gaps supported by accessible sources.",
        ),
        count(
            "unverified_claims",
            "Unverified claims",
            sum(c.status == "pending" for c in claims),
            "Source-derived candidates awaiting authorised human review.",
        ),
        count(
            "single_person_dependencies",
            "Single-owner dependencies",
            sum(bool(c.data.get("owner_id")) and not c.data.get("backup_id") for c in responsibilities),
            "Recorded responsibility candidates with an owner and no backup; pending claims remain uncertain.",
        ),
        count(
            "missing_backup_owners",
            "Missing backup owners",
            sum(not c.data.get("backup_id") for c in responsibilities),
            "Accessible responsibilities without a recorded backup.",
        ),
        ratio(
            "evidence_coverage",
            "Verified evidence coverage",
            len(verified),
            len(claims),
            "Human-verified, currently cited claims divided by all accessible current claims. This is verification coverage, not extraction accuracy.",
        ),
        ratio(
            "responsibility_acceptance",
            "Responsibility acceptance",
            sum(t.status == "accepted" for t in transfers),
            len(transfers),
            "Accepted assignments divided by accessible responsibility assignments.",
        ),
        count(
            "stale_documentation",
            "Sources due for review",
            len(stale),
            "Ready sources older than the 180-day review interval. Age alone does not prove inaccuracy.",
        ),
        count(
            "unresolved_issues",
            "Unresolved work",
            sum(
                c.kind in {"incident", "task"}
                and c.data.get("source_status", "").lower() not in RESOLVED_STATUSES
                for c in claims
            ),
            "Incident and task excerpts without recorded resolution evidence.",
        ),
    ]
