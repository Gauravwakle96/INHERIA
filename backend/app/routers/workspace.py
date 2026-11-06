from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models as m
from app import schemas as s
from app.continuity import metrics, project_person, simulation_report
from app.database import get_db
from app.intelligence import (
    build_graph,
    citations,
    current_claims,
    run_investigation,
    serialize_claim,
    successor_answer,
    visible_findings,
)
from app.security import audit, can_read_source, current_user, project_access, require_role, visible_sources
from app.transfer import (
    assign_responsibility,
    generate_exercises,
    generate_handover,
    get_transition,
    readiness,
    record_ownership_transfer,
    serialize_exercise,
    serialize_transfer,
    serialize_transition,
)

router = APIRouter(prefix="/api", tags=["Knowledge continuity"])
Db = Annotated[Session, Depends(get_db)]
User = Annotated[m.User, Depends(current_user)]


def safe_text(value: str):
    # Even feedback and interview explanations must not become a secret bypass.
    from app.ingestion import privacy_filter

    _, detected, _ = privacy_filter(value)
    if detected:
        raise HTTPException(
            422,
            "Sensitive information detected. Remove secrets or personal contact details before submitting.",
        )


def entity(db, cls, user, project_id, entity_id):
    project_access(db, user, project_id)
    record = db.get(cls, entity_id)
    if not record or record.org_id != user.org_id or record.project_id != project_id:
        raise HTTPException(404, "Record not found.")
    return record


def project_json(project):
    return {k: getattr(project, k) for k in ["id", "name", "description", "status", "stack", "is_demo"]}


def user_json(user):
    return {k: getattr(user, k) for k in ["id", "org_id", "name", "email", "title", "role"]}


def audit_json(db, item):
    actor = db.get(m.User, item.actor_id) if item.actor_id else None
    return {
        "id": item.id,
        "action": item.action,
        "resource_type": item.resource_type,
        "resource_id": item.resource_id,
        "actor_name": actor.name if actor else "System",
        "details": item.details,
        "created_at": item.created_at,
    }


def filtered_audits(db, user, project_id):
    source_ids = {source.id for source in visible_sources(db, user, project_id)}
    claim_ids = {claim.id for claim in current_claims(db, user, project_id, include_rejected=True)}
    records = list(
        db.scalars(
            select(m.Audit)
            .where(m.Audit.project_id == project_id)
            .order_by(m.Audit.created_at.desc())
            .limit(100)
        )
    )
    visible = []
    for item in records:
        if item.resource_type == "source" and item.resource_id not in source_ids:
            continue
        if item.resource_type == "claim" and item.resource_id not in claim_ids:
            continue
        classes = {
            "transfer": m.Transfer,
            "exercise": m.Exercise,
            "transition": m.Transition,
            "simulation": m.Simulation,
            "gap": m.Gap,
        }
        if item.resource_type in classes:
            linked = db.get(classes[item.resource_type], item.resource_id)
            if not linked:
                continue
            if item.resource_type == "transfer" and linked.claim_id not in claim_ids:
                continue
            if item.resource_type == "exercise" and (
                not set(linked.expected_source_ids).issubset(source_ids)
                or linked.assessment.get("claim_id") not in claim_ids
            ):
                continue
            if item.resource_type in {"transition", "simulation"} and not set(
                (linked.report or {}).get("source_ids", [])
            ).issubset(source_ids):
                continue
            if item.resource_type == "gap" and (
                not set(linked.source_ids).issubset(source_ids)
                or linked.claim_id
                and linked.claim_id not in claim_ids
            ):
                continue
        # Aggregate job counts can derive from restricted sources; reveal only actor's own runs.
        if (
            item.resource_type in {"investigation", "project", "job", "connection"}
            and item.actor_id != user.id
        ):
            clean = audit_json(db, item)
            clean["details"] = {}
        else:
            clean = audit_json(db, item)
        visible.append(clean)
    return visible


@router.get("/projects", response_model=list[s.Record])
def list_projects(db: Db, user: User):
    ids = list(db.scalars(select(m.Membership.project_id).where(m.Membership.user_id == user.id)))
    projects = list(
        db.scalars(
            select(m.Project)
            .where(m.Project.org_id == user.org_id, m.Project.id.in_(ids))
            .order_by(m.Project.name)
        )
    )
    return [project_json(project) for project in projects]


@router.post("/projects", response_model=s.Record, status_code=201)
def create_project(payload: s.ProjectCreate, db: Db, user: User):
    require_role(user, {"admin", "manager"})
    safe_text(payload.description)
    project = m.Project(
        org_id=user.org_id,
        name=payload.name,
        description=payload.description,
        stack=[],
        status="active",
        is_demo=False,
    )
    db.add(project)
    db.flush()
    db.add(m.Membership(project_id=project.id, user_id=user.id, role=user.role))
    audit(db, user, project.id, "project.created", "project", project.id, {})
    db.commit()
    return project_json(project)


@router.get("/team", response_model=list[s.Record])
def team(project_id: str, db: Db, user: User):
    project_access(db, user, project_id)
    ids = list(db.scalars(select(m.Membership.user_id).where(m.Membership.project_id == project_id)))
    return [
        user_json(person)
        for person in db.scalars(
            select(m.User).where(m.User.id.in_(ids), m.User.org_id == user.org_id).order_by(m.User.name)
        )
    ]


@router.post("/projects/{project_id}/members", response_model=s.Record, status_code=201)
def create_member(project_id: str, payload: s.MemberCreate, db: Db, user: User):
    project_access(db, user, project_id, write=True)
    require_role(user, {"admin"})
    from app.security import hash_password

    safe_text(payload.name)
    safe_text(payload.title)
    person = m.User(
        org_id=user.org_id,
        name=payload.name,
        email=payload.email.casefold(),
        title=payload.title,
        role=payload.role,
        password_hash=hash_password(payload.password),
        active=True,
    )
    db.add(person)
    try:
        db.flush()
        db.add(m.Membership(project_id=project_id, user_id=person.id, role=person.role))
        audit(db, user, project_id, "member.created", "user", person.id, {"role": person.role})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409, "This account already exists. Use a unique organisation account email."
        ) from None
    return user_json(person)


@router.get("/projects/{project_id}/overview", response_model=s.Overview)
def overview(project_id: str, db: Db, user: User):
    project = project_access(db, user, project_id)
    sources = visible_sources(db, user, project_id)
    claims = current_claims(db, user, project_id)
    verified = sum(c.status == "verified" for c in claims)
    approved = db.scalar(
        select(m.Transition.id).where(
            m.Transition.project_id == project_id,
            m.Transition.status.in_(["approved", "in_progress", "closed"]),
        )
    )
    transfers = list(db.scalars(select(m.Transfer).where(m.Transfer.project_id == project_id)))
    visible_ids = {c.id for c in claims}
    transfers = [t for t in transfers if t.claim_id in visible_ids]
    validated = db.scalar(
        select(m.Exercise.id).where(m.Exercise.project_id == project_id, m.Exercise.status == "passed")
    )
    pipeline = [
        {
            "stage": "Connect",
            "status": "complete" if any(s.status == "ready" for s in sources) else "pending",
            "count": sum(s.status == "ready" for s in sources),
        },
        {"stage": "Reconstruct", "status": "complete" if claims else "pending", "count": len(claims)},
        {
            "stage": "Verify",
            "status": "complete"
            if verified and verified == len(claims)
            else "in_progress"
            if verified
            else "pending",
            "count": verified,
        },
        {"stage": "Review", "status": "complete" if approved else "pending", "count": int(bool(approved))},
        {
            "stage": "Handover",
            "status": "complete"
            if transfers and all(t.status == "accepted" for t in transfers)
            else "in_progress"
            if transfers
            else "pending",
            "count": sum(t.status == "accepted" for t in transfers),
        },
        {
            "stage": "Validate",
            "status": "in_progress" if validated else "pending",
            "count": int(bool(validated)),
        },
    ]
    return {
        "metrics": metrics(db, user, project_id),
        "activity": filtered_audits(db, user, project_id)[:8],
        "pipeline": pipeline,
        "ai_mode": "deterministic-v1",
        "synthetic": project.is_demo,
        "source_health": {
            "ready": sum(s.status == "ready" for s in sources),
            "failed": sum(s.status in {"failed", "sync_failed"} for s in sources),
            "quarantined": sum(s.status == "quarantined" for s in sources),
        },
    }


@router.get("/projects/{project_id}/claims", response_model=list[s.Record])
def claims(project_id: str, db: Db, user: User, kind: str = "", status: str = ""):
    return [
        serialize_claim(db, user, claim)
        for claim in current_claims(db, user, project_id, include_rejected=True)
        if (not kind or claim.kind == kind) and (not status or claim.status == status)
    ]


@router.get("/projects/{project_id}/evidence/{source_id}", response_model=dict)
def evidence(project_id: str, source_id: str, db: Db, user: User):
    source = entity(db, m.Source, user, project_id, source_id)
    if not can_read_source(db, user, source):
        raise HTTPException(404, "Evidence is unavailable or restricted.")
    from app.ingestion import serialize_source

    chunks = list(
        db.scalars(
            select(m.Chunk)
            .where(m.Chunk.source_id == source.id, m.Chunk.source_version == source.version)
            .order_by(m.Chunk.ordinal)
        )
    )
    return {
        "source": serialize_source(db, user, source),
        "chunks": [{"id": c.id, "locator": c.locator, "text": c.text} for c in chunks],
    }


@router.post("/projects/{project_id}/claims/{claim_id}/review", response_model=s.Record)
def review_claim(project_id: str, claim_id: str, payload: s.Review, db: Db, user: User):
    project_access(db, user, project_id, write=True)
    require_role(user, {"admin", "manager", "lead"})
    claim = entity(db, m.Claim, user, project_id, claim_id)
    if claim_id not in {c.id for c in current_claims(db, user, project_id, include_rejected=True)}:
        raise HTTPException(404, "Claim evidence is unavailable or restricted.")
    safe_text(payload.note)
    if payload.summary:
        safe_text(payload.summary)
    if payload.component:
        safe_text(payload.component)
    if claim.created_by == user.id:
        raise HTTPException(403, "Another authorised reviewer must verify your own knowledge submission.")
    before = {"status": claim.status, "verified_by": claim.verified_by}
    if payload.action == "correct":
        if not payload.summary:
            raise HTTPException(422, "A corrected explanation is required.")
        claim.summary, claim.status = payload.summary, "pending"
        claim.created_by = user.id
        claim.verified_by, claim.verified_at = None, None
    elif payload.action == "reject":
        claim.status, claim.verified_by, claim.verified_at = "rejected", user.id, m.utcnow()
    else:
        if claim.status != "pending":
            raise HTTPException(409, "Only pending knowledge can be approved.")
        data = dict(claim.data)
        for field in ["owner_id", "backup_id"]:
            value = getattr(payload, field)
            if value is not None:
                if value:
                    project_person(db, user, project_id, value)
                data[field] = value or None
        for field in ["component", "critical"]:
            if getattr(payload, field) is not None:
                data[field] = getattr(payload, field)
        if data.get("owner_id") and data.get("owner_id") == data.get("backup_id"):
            raise HTTPException(422, "Owner and backup must be different project members.")
        claim.data = data
        claim.status, claim.verified_by, claim.verified_at = "verified", user.id, m.utcnow()
    # A significant correction invalidates any readiness based on the old claim.
    if payload.action in {"correct", "reject"}:
        for exercise in db.scalars(select(m.Exercise).where(m.Exercise.project_id == project_id)):
            if exercise.assessment.get("claim_id") == claim.id:
                exercise.status = "needs_revision"
    audit(
        db,
        user,
        project_id,
        "claim." + payload.action,
        "claim",
        claim.id,
        {
            "note": payload.note,
            "before": before,
            "after_status": claim.status,
            "evidence_ids": [e["id"] for e in citations(db, user, claim)],
        },
    )
    db.commit()
    return serialize_claim(db, user, claim)


@router.post("/projects/{project_id}/investigations", response_model=s.Record, status_code=202)
def investigate(project_id: str, payload: s.InvestigationCreate, tasks: BackgroundTasks, db: Db, user: User):
    project = project_access(db, user, project_id, write=True)
    safe_text(payload.focus)
    if payload.employee_id:
        project_person(db, user, project_id, payload.employee_id)
    running = db.scalar(
        select(m.Investigation).where(
            m.Investigation.project_id == project_id, m.Investigation.status.in_(["queued", "running"])
        )
    )
    if running:
        raise HTTPException(
            409, "An investigation is already running. Wait for its result before starting another."
        )
    record = m.Investigation(
        org_id=project.org_id, project_id=project_id, created_by=user.id, status="queued", report={}
    )
    db.add(record)
    db.flush()
    audit(db, user, project_id, "investigation.queued", "investigation", record.id, {"focus": payload.focus})
    db.commit()
    tasks.add_task(run_investigation, record.id, payload.focus, payload.employee_id)
    return {
        "id": record.id,
        "status": record.status,
        "report": record.report,
        "created_at": record.created_at,
    }


@router.get("/projects/{project_id}/investigations", response_model=list[s.Record])
def investigations(project_id: str, db: Db, user: User):
    project_access(db, user, project_id)
    records = list(
        db.scalars(
            select(m.Investigation)
            .where(m.Investigation.project_id == project_id)
            .order_by(m.Investigation.created_at.desc())
            .limit(30)
        )
    )
    result = []
    for record in records:
        original = record.report or {}
        findings = visible_findings(db, user, project_id, original.get("findings", []))
        questions = [
            {"question": f["question"], "reason": f["details"], "source_ids": f["source_ids"]}
            for f in findings[:20]
        ]
        report = {k: original.get(k, []) for k in ["unknowns", "limitations"]}
        source_count = sum(source.status == "ready" for source in visible_sources(db, user, project_id))
        report.update(
            summary=f"{len(findings)} accessible findings from authorised evidence.",
            findings=findings,
            questions=questions,
            searched_sources=source_count,
            engine=original.get("engine", "deterministic-v1"),
        )
        result.append(
            {"id": record.id, "status": record.status, "report": report, "created_at": record.created_at}
        )
    return result


@router.get("/projects/{project_id}/gaps", response_model=list[s.Record])
def gaps(project_id: str, db: Db, user: User):
    project_access(db, user, project_id)
    result = []
    for gap in db.scalars(
        select(m.Gap).where(m.Gap.project_id == project_id).order_by(m.Gap.created_at.desc())
    ):
        data = {
            k: getattr(gap, k)
            for k in [
                "id",
                "title",
                "kind",
                "severity",
                "status",
                "details",
                "question",
                "source_ids",
                "claim_id",
            ]
        }
        if visible_findings(db, user, project_id, [data]):
            result.append(data)
    return result


@router.patch("/projects/{project_id}/gaps/{gap_id}", response_model=s.Record)
def update_gap(project_id: str, gap_id: str, payload: s.GapUpdate, db: Db, user: User):
    project_access(db, user, project_id, write=True)
    gap = entity(db, m.Gap, user, project_id, gap_id)
    if not visible_findings(db, user, project_id, [{"source_ids": gap.source_ids, "claim_id": gap.claim_id}]):
        raise HTTPException(404, "Gap evidence unavailable.")
    safe_text(payload.note)
    if payload.status == "resolved":
        require_role(user, {"admin", "manager", "lead"})
        claim = db.get(m.Claim, gap.claim_id) if gap.claim_id else None
        if claim and claim.status != "verified":
            raise HTTPException(409, "Verify the related knowledge before resolving this gap.")
    gap.status, gap.note = payload.status, payload.note
    audit(db, user, project_id, "gap.updated", "gap", gap.id, {"status": gap.status, "note": gap.note})
    db.commit()
    return {
        k: getattr(gap, k)
        for k in [
            "id",
            "title",
            "kind",
            "severity",
            "status",
            "details",
            "question",
            "source_ids",
            "claim_id",
        ]
    }


@router.post("/projects/{project_id}/gaps/{gap_id}/respond", response_model=s.Record, status_code=201)
def capture_answer(project_id: str, gap_id: str, payload: s.InterviewResponse, db: Db, user: User):
    project = project_access(db, user, project_id)
    gap = entity(db, m.Gap, user, project_id, gap_id)
    if not visible_findings(db, user, project_id, [{"source_ids": gap.source_ids, "claim_id": gap.claim_id}]):
        raise HTTPException(404, "Interview evidence is unavailable or restricted.")
    safe_text(payload.answer)
    source_ids = set(gap.source_ids)
    sources = {
        source.id: source for source in visible_sources(db, user, project_id) if source.id in source_ids
    }
    restricted = [set(source.acl) for source in sources.values() if source.acl]
    acl = sorted(set.intersection(*restricted)) if restricted else []
    body = "Interview question: " + gap.question + "\nEmployee explanation: " + payload.answer
    checksum = hashlib.sha256(body.encode()).hexdigest()
    source = db.scalar(
        select(m.Source).where(
            m.Source.project_id == project_id, m.Source.kind == "interview", m.Source.checksum == checksum
        )
    )
    if source and source.acl == acl:
        existing = db.scalar(
            select(m.Claim)
            .join(m.Evidence, m.Evidence.claim_id == m.Claim.id)
            .where(m.Evidence.source_id == source.id)
        )
        if existing:
            return serialize_claim(db, user, existing)
    source = m.Source(
        org_id=user.org_id,
        project_id=project_id,
        name="Interview: " + gap.title[:180],
        kind="interview",
        checksum=checksum,
        status="ready",
        acl=acl,
        version=1,
        synthetic=project.is_demo,
        source_metadata={"author_id": user.id, "gap_id": gap.id, "employee_explanation": True},
    )
    db.add(source)
    db.flush()
    chunk = m.Chunk(
        org_id=user.org_id,
        project_id=project_id,
        source_id=source.id,
        source_version=1,
        ordinal=0,
        locator="Interview response",
        text=body,
    )
    db.add(chunk)
    db.flush()
    related = db.get(m.Claim, gap.claim_id) if gap.claim_id else None
    kind = {
        "missing_procedure": "procedure",
        "unverified_procedure": "procedure",
        "missing_rationale": "decision",
        "single_owner": "responsibility",
        "unknown_ownership": "responsibility",
        "unfinished_work": "task",
    }.get(gap.kind, "lesson")
    data = (
        dict(related.data)
        if related
        else {"owner_id": None, "backup_id": None, "component": "", "critical": False}
    )
    data.update(engine="human-interview", employee_explanation=True, author_id=user.id, gap_id=gap.id)
    data.pop("fingerprint", None)
    claim = m.Claim(
        org_id=user.org_id,
        project_id=project_id,
        kind=kind,
        title="Interview: " + gap.title[:170],
        summary=payload.answer,
        status="pending",
        confidence="employee_statement",
        created_by=user.id,
        data=data,
        confidence_reason="Employee-provided explanation. Exact interview provenance is recorded; independent corroboration and another authorised reviewer are required.",
    )
    db.add(claim)
    db.flush()
    db.add(
        m.Evidence(
            org_id=user.org_id,
            project_id=project_id,
            claim_id=claim.id,
            chunk_id=chunk.id,
            source_id=source.id,
            source_version=1,
            quote=payload.answer,
        )
    )
    gap.status = "in_progress"
    audit(
        db,
        user,
        project_id,
        "interview.recorded",
        "claim",
        claim.id,
        {"gap_id": gap.id, "employee_explanation": True},
    )
    db.commit()
    return serialize_claim(db, user, claim)


@router.get("/projects/{project_id}/graph", response_model=dict)
def graph(project_id: str, db: Db, user: User):
    return build_graph(db, user, project_id)


@router.post("/projects/{project_id}/simulations", response_model=s.Record, status_code=201)
def simulate(project_id: str, payload: s.SimulationCreate, db: Db, user: User):
    project = project_access(db, user, project_id, write=True)
    for assumption in payload.assumptions:
        if len(assumption) > 500:
            raise HTTPException(422, "Each assumption must be under 500 characters.")
        safe_text(assumption)
    report = jsonable_encoder(
        simulation_report(db, user, project_id, payload.employee_id, payload.scenario, payload.component)
    )
    record = m.Simulation(
        org_id=project.org_id,
        project_id=project_id,
        created_by=user.id,
        employee_id=payload.employee_id,
        scenario=payload.scenario,
        assumptions=payload.assumptions,
        report=report,
    )
    db.add(record)
    db.flush()
    audit(db, user, project_id, "simulation.created", "simulation", record.id, {"hypothetical": True})
    db.commit()
    return {
        "id": record.id,
        "created_at": record.created_at,
        "employee_id": record.employee_id,
        "scenario": record.scenario,
        "assumptions": record.assumptions,
        "report": report,
    }


@router.get("/projects/{project_id}/simulations", response_model=list[s.Record])
def simulations(project_id: str, db: Db, user: User):
    project_access(db, user, project_id)
    source_ids = {s.id for s in visible_sources(db, user, project_id) if s.status == "ready"}
    current = current_claims(db, user, project_id)
    claim_ids = {c.id for c in current}
    current_citations = {e["id"]: e for c in current for e in citations(db, user, c)}
    result = []
    for record in db.scalars(
        select(m.Simulation)
        .where(m.Simulation.project_id == project_id)
        .order_by(m.Simulation.created_at.desc())
        .limit(30)
    ):
        report = record.report or {}
        if not set(report.get("source_ids", [])).issubset(source_ids):
            continue
        if any(row.get("responsibility_id") not in claim_ids for row in report.get("affected", [])):
            continue
        refs = [ref for row in report.get("affected", []) for ref in row.get("evidence", [])]
        if any(
            ref.get("id") not in current_citations
            or ref.get("source_version") != current_citations[ref["id"]]["source_version"]
            or ref.get("quote") != current_citations[ref["id"]]["quote"]
            for ref in refs
        ):
            continue
        result.append(
            {
                "id": record.id,
                "created_at": record.created_at,
                "employee_id": record.employee_id,
                "scenario": record.scenario,
                "assumptions": record.assumptions,
                "report": report,
            }
        )
    return result


@router.get("/projects/{project_id}/transitions", response_model=list[s.Record])
def transitions(project_id: str, db: Db, user: User):
    project_access(db, user, project_id)
    return [
        serialize_transition(db, user, t)
        for t in db.scalars(
            select(m.Transition)
            .where(m.Transition.project_id == project_id)
            .order_by(m.Transition.created_at.desc())
        )
    ]


@router.post("/projects/{project_id}/transitions", response_model=s.Record, status_code=201)
def create_transition(project_id: str, payload: s.TransitionCreate, db: Db, user: User):
    project = project_access(db, user, project_id, write=True)
    project_person(db, user, project_id, payload.departing_id)
    project_person(db, user, project_id, payload.successor_id)
    if payload.departing_id == payload.successor_id:
        raise HTTPException(422, "Select a different incoming employee.")
    safe_text(payload.title)
    transition = m.Transition(
        org_id=project.org_id,
        project_id=project_id,
        title=payload.title,
        departing_id=payload.departing_id,
        successor_id=payload.successor_id,
        departure_date=payload.departure_date.isoformat(),
        status="planned",
        version=0,
        report={},
    )
    db.add(transition)
    db.flush()
    audit(db, user, project_id, "transition.created", "transition", transition.id, {})
    db.commit()
    return serialize_transition(db, user, transition)


@router.post("/projects/{project_id}/transitions/{transition_id}/generate", response_model=s.Record)
def generate(project_id: str, transition_id: str, db: Db, user: User):
    transition = get_transition(db, user, project_id, transition_id)
    generate_handover(db, user, transition)
    db.commit()
    return serialize_transition(db, user, transition)


@router.post("/projects/{project_id}/transitions/{transition_id}/approve", response_model=s.Record)
def approve(project_id: str, transition_id: str, payload: s.Note, db: Db, user: User):
    project_access(db, user, project_id, write=True)
    require_role(user, {"admin", "manager", "lead"})
    transition = get_transition(db, user, project_id, transition_id)
    if transition.status != "generated":
        raise HTTPException(409, "Generate the evidence-backed handover before approval.")
    safe_text(payload.note)
    transition.status = "approved"
    audit(
        db,
        user,
        project_id,
        "handover.approved",
        "transition",
        transition.id,
        {"note": payload.note, "version": transition.version},
    )
    db.commit()
    return serialize_transition(db, user, transition)


@router.post("/projects/{project_id}/transitions/{transition_id}/assign", response_model=s.Record)
def assign(project_id: str, transition_id: str, payload: s.Assignment, db: Db, user: User):
    transition = get_transition(db, user, project_id, transition_id)
    transfer = assign_responsibility(
        db, user, transition, payload.claim_id, payload.successor_id, payload.backup_id
    )
    db.commit()
    return serialize_transfer(db, transfer)


@router.post("/projects/{project_id}/transfers/{transfer_id}/respond", response_model=s.Record)
def respond(project_id: str, transfer_id: str, payload: s.TransferResponse, db: Db, user: User):
    transfer = entity(db, m.Transfer, user, project_id, transfer_id)
    if transfer.successor_id != user.id:
        raise HTTPException(403, "Only the assigned incoming owner may accept or reject this responsibility.")
    if transfer.claim_id not in {c.id for c in current_claims(db, user, project_id, verified=True)}:
        raise HTTPException(409, "Responsibility evidence must be current, verified and accessible.")
    transition = get_transition(db, user, project_id, transfer.transition_id)
    if transition.status not in {"approved", "in_progress"}:
        raise HTTPException(409, "This transition cannot accept ownership responses.")
    safe_text(payload.note)
    transfer.status = "accepted" if payload.action == "accept" else "rejected"
    transfer.note = payload.note
    transfer.accepted_at = m.utcnow() if payload.action == "accept" else None
    audit(
        db,
        user,
        project_id,
        "responsibility." + transfer.status,
        "transfer",
        transfer.id,
        {"note": payload.note},
    )
    db.commit()
    return serialize_transfer(db, transfer)


@router.post("/projects/{project_id}/transitions/{transition_id}/exercises", response_model=s.Record)
def exercises(project_id: str, transition_id: str, db: Db, user: User):
    transition = get_transition(db, user, project_id, transition_id)
    generate_exercises(db, user, transition)
    db.commit()
    return serialize_transition(db, user, transition)


@router.post("/projects/{project_id}/exercises/{exercise_id}/submit", response_model=s.Record)
def submit(project_id: str, exercise_id: str, payload: s.Submission, db: Db, user: User):
    exercise = entity(db, m.Exercise, user, project_id, exercise_id)
    transition = get_transition(db, user, project_id, exercise.transition_id)
    if transition.successor_id != user.id:
        raise HTTPException(403, "Only the assigned incoming employee may submit this exercise.")
    if transition.status not in {"approved", "in_progress"}:
        raise HTTPException(409, "This transition is not open for validation.")
    safe_text(payload.answer)
    safe_text(payload.escalation)
    claims = current_claims(db, user, project_id, verified=True)
    refs = {e["id"]: e for c in claims for e in citations(db, user, c)}
    if not set(payload.evidence_ids).issubset(refs):
        raise HTTPException(422, "Use current authorised evidence citations.")
    linked_sources = {refs[e]["source_id"] for e in payload.evidence_ids}
    if not set(exercise.expected_source_ids).issubset(linked_sources):
        raise HTTPException(422, "Locate the exercise’s relevant source evidence before submitting.")
    exercise.answer, exercise.evidence_ids, exercise.escalation = (
        payload.answer,
        payload.evidence_ids,
        payload.escalation,
    )
    exercise.status = "submitted"
    exercise.assessment = {
        **exercise.assessment,
        "evidence_located": True,
        "requires_human_review": True,
        "submitted_by": user.id,
    }
    exercise.reviewed_by, exercise.supervisor_note = None, ""
    audit(
        db,
        user,
        project_id,
        "validation.submitted",
        "exercise",
        exercise.id,
        {"evidence_ids": payload.evidence_ids},
    )
    db.commit()
    return serialize_exercise(exercise)


@router.post("/projects/{project_id}/exercises/{exercise_id}/review", response_model=s.Record)
def assess(project_id: str, exercise_id: str, payload: s.Assessment, db: Db, user: User):
    project_access(db, user, project_id, write=True)
    require_role(user, {"admin", "manager", "lead"})
    exercise = entity(db, m.Exercise, user, project_id, exercise_id)
    transition = get_transition(db, user, project_id, exercise.transition_id)
    if transition.successor_id == user.id or exercise.assessment.get("submitted_by") == user.id:
        raise HTTPException(403, "A different authorised supervisor must validate this exercise.")
    if exercise.status != "submitted":
        raise HTTPException(409, "A submitted practical explanation is required before assessment.")
    valid = {
        e["id"] for c in current_claims(db, user, project_id, verified=True) for e in citations(db, user, c)
    }
    if not set(exercise.evidence_ids).issubset(valid):
        raise HTTPException(409, "Submitted evidence is no longer current or accessible.")
    safe_text(payload.note)
    exercise.status = "passed" if payload.action == "pass" else "needs_revision"
    exercise.reviewed_by, exercise.supervisor_note = user.id, payload.note
    exercise.assessment = {
        **exercise.assessment,
        "requires_human_review": False,
        "criteria": exercise.criteria,
        "reviewed_at": m.utcnow().isoformat(),
        "evidence_ids": exercise.evidence_ids,
    }
    audit(
        db,
        user,
        project_id,
        "validation." + exercise.status,
        "exercise",
        exercise.id,
        {"note": payload.note, "evidence_ids": exercise.evidence_ids, "criteria": exercise.criteria},
    )
    db.commit()
    return serialize_exercise(exercise)


@router.get("/projects/{project_id}/transitions/{transition_id}/readiness", response_model=dict)
def readiness_report(project_id: str, transition_id: str, db: Db, user: User):
    return readiness(db, user, get_transition(db, user, project_id, transition_id))


@router.post("/projects/{project_id}/transitions/{transition_id}/close", response_model=s.Record)
def close(project_id: str, transition_id: str, db: Db, user: User):
    project_access(db, user, project_id, write=True)
    require_role(user, {"admin", "manager", "lead"})
    transition = get_transition(db, user, project_id, transition_id)
    report = readiness(db, user, transition)
    if not report["ready"]:
        raise HTTPException(409, "Transition remains incomplete: " + " ".join(report["blockers"]))
    if transition.status != "closed":
        record_ownership_transfer(db, user, transition)
    transition.status = "closed"
    audit(
        db,
        user,
        project_id,
        "transition.closed",
        "transition",
        transition.id,
        {"version": transition.version},
    )
    db.commit()
    return serialize_transition(db, user, transition)


@router.post("/projects/{project_id}/successor/ask", response_model=s.SuccessorAnswer)
def ask(project_id: str, payload: s.Question, db: Db, user: User):
    safe_text(payload.question)
    result = successor_answer(db, user, project_id, payload.question)
    audit(db, user, project_id, "successor.queried", "project", project_id, {"supported": result["known"]})
    db.commit()
    return result


@router.get("/projects/{project_id}/audit", response_model=list[s.Record])
def audit_log(project_id: str, db: Db, user: User):
    project_access(db, user, project_id)
    require_role(user, {"admin", "manager", "lead", "security"})
    return filtered_audits(db, user, project_id)


@router.get("/projects/{project_id}/privacy", response_model=dict)
def privacy(project_id: str, db: Db, user: User):
    project_access(db, user, project_id)
    from app.config import settings
    from app.ingestion import serialize_source

    sources = visible_sources(db, user, project_id)
    return {
        "sources": [serialize_source(db, user, source) for source in sources],
        "quarantined_count": sum(s.status == "quarantined" for s in sources),
        "retention_days": settings.retention_days,
        "controls": [
            "Source ACLs before extraction and retrieval.",
            "Likely secrets are quarantined; personal contact details are redacted before indexing.",
            "Opaque HttpOnly sessions and CSRF checks.",
            "Revocation invalidates derived evidence.",
            "No production execution.",
        ],
        "limitations": [
            "Demo personas are available only in explicitly enabled demo mode.",
            "Automated retention deletion, enterprise SSO/MFA and legal holds are not implemented.",
            "Encryption at rest depends on deployment; private connector tokens require an encryption key.",
        ],
    }
