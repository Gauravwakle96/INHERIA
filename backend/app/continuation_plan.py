"""Current role-specific next steps calculated from authorised workflow state."""

from sqlalchemy import select

from app import models as m
from app.intelligence import current_claims, serialize_claim
from app.security import project_access, visible_sources
from app.transfer import readiness


def continuation_plan(db, user, project_id, summary=False):
    project_access(db, user, project_id)
    claims = current_claims(db, user, project_id)
    sources = [s for s in visible_sources(db, user, project_id) if s.status == "ready"]
    transition = db.scalar(
        select(m.Transition)
        .where(m.Transition.project_id == project_id)
        .order_by(m.Transition.updated_at.desc())
    )
    reviewer = user.role in {"admin", "manager", "lead"}
    path = f"/handover?transition={transition.id}" if transition else "/handover"
    actor = "Project coordinator"
    stage, detail, action, target = (
        "Connect",
        "Add an authorised document or repository.",
        "Connect sources",
        "/sources",
    )
    report = readiness(db, user, transition) if transition else None
    if sources and not claims:
        stage, detail, action, target = (
            "Reconstruct",
            "Sources are ready. Investigate them to discover candidate knowledge.",
            "Investigate project",
            "/investigation",
        )
    elif claims and (not transition or transition.status in {"planned", "draft", "reopened"}):
        pending = sum(c.status == "pending" for c in claims)
        if pending:
            stage, detail, action, target = (
                "Verify & review",
                f"{pending} accessible candidates await review. Inspect citations before approval.",
                "Review evidence",
                "/memory",
            )
        else:
            stage, detail, action, target = (
                "Handover",
                "Generate a reviewed continuation plan for the selected incoming person.",
                "Prepare handover",
                path,
            )
    elif transition and transition.status == "generated":
        stage, detail, action, target = (
            "Approve",
            f"Version {transition.version} awaits review and approval.",
            "Inspect handover",
            path,
        )
    elif transition and transition.status in {"approved", "in_progress"}:
        transfers = list(
            db.scalars(
                select(m.Transfer).where(
                    m.Transfer.transition_id == transition.id, m.Transfer.status != "superseded"
                )
            )
        )
        exercises = list(
            db.scalars(
                select(m.Exercise).where(
                    m.Exercise.transition_id == transition.id, m.Exercise.status != "superseded"
                )
            )
        )
        if len(transfers) < report["total"]:
            stage, detail, action, target = (
                "Assign ownership",
                "Propose each reviewed responsibility to the incoming person before acceptance.",
                "Assign responsibilities",
                path,
            )
        elif not exercises:
            stage, detail, action, target = (
                "Prepare practical tasks",
                "Create responsibility-specific scenarios for the incoming person.",
                "Create practical tasks",
                path,
            )
        elif report["accepted"] < report["total"]:
            actor = db.get(m.User, transition.successor_id).name
            stage, detail, action, target = (
                "Accept ownership",
                "Review each assignment; accept it or explain missing information.",
                "Review assignments",
                f"/validation?transition={transition.id}",
            )
        elif report["validated"] < report["exercise_total"]:
            if any(e.status in {"pending", "needs_revision"} for e in exercises):
                actor = db.get(m.User, transition.successor_id).name
            stage, detail, action, target = (
                "Validate",
                "Submit cited practical explanations and obtain independent scenario review.",
                "Open practical tasks",
                f"/validation?transition={transition.id}",
            )
        else:
            stage, detail, action, target = (
                "Close required checks",
                "Resolve required checks and review remaining work before closing.",
                "Review readiness",
                path,
            )
    elif transition and transition.status == "closed":
        stage = "Continue" if report["ready"] else "Revalidate"
        detail = (
            "Ownership and reviewed knowledge have transferred. Open incidents and operational tests remain separate work."
            if report["ready"]
            else "Historical completion is preserved, but current evidence or access needs revalidation. Create a follow-up transition."
        )
        action, target = "Inspect completed handover", path
    if not reviewer and actor == "Project coordinator":
        detail += " An authorised coordinator performs this step."
    available = {c.id for c in claims}
    responsibilities = [
        c
        for c in claims
        if c.kind == "responsibility" and c.data.get("owner_id") == user.id and c.status == "verified"
    ]
    if transition and user.id == transition.successor_id:
        assigned = set(
            db.scalars(select(m.Transfer.claim_id).where(m.Transfer.transition_id == transition.id))
        )
        responsibilities = [
            c
            for c in claims
            if c.kind == "responsibility"
            and c.status == "verified"
            and (c.id in assigned or c.data.get("owner_id") == user.id)
        ]
    gaps = [
        g
        for g in db.scalars(select(m.Gap).where(m.Gap.project_id == project_id, m.Gap.status == "open"))
        if (not g.claim_id or g.claim_id in available) and set(g.source_ids).issubset({s.id for s in sources})
    ]
    result = {
        "stage": stage,
        "detail": detail,
        "next_action": {"label": action, "path": target, "actor": actor},
        "transition_id": transition.id if transition else None,
        "ready": bool(report and report["ready"]),
        "blockers": report["blockers"] if report else [],
        "source_count": len(sources),
        "candidate_count": len(claims),
        "critical_gaps": len([g for g in gaps if g.severity == "critical"]),
        "responsibilities": [] if summary else [serialize_claim(db, user, c) for c in responsibilities],
        "procedures": [
            serialize_claim(db, user, c)
            for c in claims
            if not summary and c.kind == "procedure" and c.status == "verified"
        ],
        "open_work": [
            serialize_claim(db, user, c)
            for c in claims
            if not summary and c.kind in {"task", "incident"} and c.status == "verified"
        ],
        "unknowns": [g.question for g in gaps[:12]],
        "scope": "This plan uses current accessible evidence. It grants no external access and certifies no production operation.",
    }
    return result
