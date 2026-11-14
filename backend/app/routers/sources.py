"""Source ingestion and integration administration API."""

from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import settings
from app.connectors import (
    ConnectorError,
    encrypt_token,
    run_sync_job,
    serialize_connection,
    serialize_job,
    validate_repository,
)
from app.database import get_db
from app.ingestion import DocumentError, ingest_document, invalidate_source, serialize_source, utcnow
from app.models import Chunk, Connection, Evidence, Job, Membership, Project, Source, User
from app.security import audit, can_read_source, current_user, project_access, require_role

router = APIRouter(prefix="/api/projects/{project_id}", tags=["sources"])
Db = Annotated[Session, Depends(get_db)]
Actor = Annotated[User, Depends(current_user)]
SOURCE_ADMIN_ROLES = {"admin", "manager", "lead"}


class GitHubConnectionRequest(BaseModel):
    repository: str = Field(min_length=3, max_length=240)
    token: str | None = Field(default=None, max_length=300)


class SourceAccessBody(BaseModel):
    allowed_user_ids: list[str] = Field(max_length=500)
    note: str = Field(min_length=10, max_length=2000)


@router.get("/sources/{source_id}/access")
def source_access(project_id: str, source_id: str, db: Db, user: Actor):
    project_access(db, user, project_id, write=True)
    require_role(user, SOURCE_ADMIN_ROLES)
    source = _source(db, user, project_id, source_id)
    return {
        "source_id": source.id,
        "allowed_user_ids": source.acl,
        "scope": "selected_members" if source.acl else "all_project_members",
    }


@router.post("/sources/{source_id}/access")
def update_source_access(project_id: str, source_id: str, body: SourceAccessBody, db: Db, user: Actor):
    project_access(db, user, project_id, write=True)
    require_role(user, SOURCE_ADMIN_ROLES)
    # Membership revocation uses the same project lock; a stale reader edit must
    # not restore a grant after the member has been removed.
    db.scalar(select(Project).where(Project.id == project_id).with_for_update())
    project_access(db, user, project_id, write=True)
    source = _source(db, user, project_id, source_id)
    from app.routers.workspace import safe_text

    safe_text(body.note)
    allowed = sorted(set(body.allowed_user_ids))
    members = set(db.scalars(select(Membership.user_id).where(Membership.project_id == project_id)))
    if allowed and (not set(allowed).issubset(members) or user.id not in allowed):
        raise HTTPException(
            422, "Select current project members and include yourself for a restricted source."
        )
    source.acl = allowed
    audit(
        db,
        user,
        project_id,
        "source.access_changed",
        "source",
        source.id,
        {"scope": "selected_members" if allowed else "all_project_members", "reader_count": len(allowed)},
    )
    db.commit()
    return {
        "source_id": source.id,
        "allowed_user_ids": allowed,
        "scope": "selected_members" if allowed else "all_project_members",
    }


def _source(db: Session, user: User, project_id: str, source_id: str) -> Source:
    project_access(db, user, project_id)
    source = db.get(Source, source_id)
    if (
        source is None
        or source.project_id != project_id
        or not can_read_source(db, user, source, include_inactive=True)
    ):
        raise HTTPException(404, "Source not found or access unavailable.")
    return source


def _connection(db: Session, user: User, project_id: str, connection_id: str) -> Connection:
    project_access(db, user, project_id)
    connection = db.get(Connection, connection_id)
    if connection is None or connection.org_id != user.org_id or connection.project_id != project_id:
        raise HTTPException(404, "Connection not found.")
    return connection


@router.get("/sources")
def list_sources(project_id: str, db: Db, user: Actor) -> list[dict[str, Any]]:
    project_access(db, user, project_id)
    sources = db.scalars(
        select(Source)
        .where(Source.project_id == project_id, Source.org_id == user.org_id)
        .order_by(Source.updated_at.desc())
    ).all()
    return [
        serialize_source(db, user, source)
        for source in sources
        if can_read_source(db, user, source, include_inactive=True)
    ]


@router.post("/sources/upload", status_code=201)
def upload_source(
    project_id: str,
    db: Db,
    user: Actor,
    file: Annotated[UploadFile, File()],
    allowed_user_ids: Annotated[str | None, Form()] = None,
) -> dict[str, Any]:
    project_access(db, user, project_id, write=True)
    require_role(user, SOURCE_ADMIN_ROLES)
    acl: list[str] = []
    if allowed_user_ids is not None:
        try:
            value = json.loads(allowed_user_ids)
        except ValueError:
            raise HTTPException(422, "Source access must be a JSON list of project user IDs.") from None
        if (
            not isinstance(value, list)
            or not all(isinstance(item, str) for item in value)
            or len(value) > 500
        ):
            raise HTTPException(422, "Source access must be a JSON list of project user IDs.")
        acl = sorted(set(value))
        if acl:
            member_ids = set(
                db.scalars(select(Membership.user_id).where(Membership.project_id == project_id))
            )
            if not set(acl).issubset(member_ids) or user.id not in acl:
                raise HTTPException(
                    422, "Restricted source users must be project members and include the uploader."
                )
    content = file.file.read(settings.max_upload_bytes + 1)
    try:
        source, duplicate = ingest_document(
            db, user, project_id, filename=file.filename or "document.txt", content=content, acl=acl
        )
    except DocumentError as exc:
        raise HTTPException(422, str(exc)) from None
    db.commit()
    db.refresh(source)
    return {"source": serialize_source(db, user, source), "duplicate": duplicate}


@router.get("/sources/{source_id}/impact")
def impact(project_id: str, source_id: str, db: Db, user: Actor):
    from app.impact import source_impact

    return source_impact(db, user, project_id, source_id)


@router.post("/sources/{source_id}/replace")
def replace_source(project_id: str, source_id: str, db: Db, user: Actor, file: Annotated[UploadFile, File()]):
    import hashlib

    from app.ingestion import parse_document

    db.scalar(select(Project).where(Project.id == project_id).with_for_update())
    db.expire_all()
    project_access(db, user, project_id, write=True)
    source = _source(db, user, project_id, source_id)
    if (
        source.connection_id
        or source.kind in {"interview", "ownership_transfer"}
        or source.status == "revoked"
    ):
        raise HTTPException(
            409, "Replace an active uploaded document. Connected sources must be synchronised."
        )
    content = file.file.read(settings.max_upload_bytes + 1)
    try:
        parsed = parse_document(file.filename or source.name, content, max_bytes=settings.max_upload_bytes)
    except DocumentError as exc:
        raise HTTPException(422, str(exc)) from None
    checksum = hashlib.sha256(content).hexdigest()
    if checksum == source.checksum:
        return {"source": serialize_source(db, user, source), "duplicate": True}
    # A transaction invalidates downstream evidence before publishing the new version.
    invalidate_source(db, source)
    source.version += 1
    source.name = file.filename or source.name
    source.checksum, source.status = checksum, "quarantined" if parsed.quarantined else "ready"
    source.source_time = utcnow()
    source.source_metadata = parsed.metadata
    from app.ingestion import safe_metadata, safe_name

    source.name, source.source_metadata = safe_name(source.name), safe_metadata(parsed.metadata)
    for ordinal, segment in enumerate(parsed.segments):
        db.add(
            Chunk(
                org_id=user.org_id,
                project_id=project_id,
                source_id=source.id,
                source_version=source.version,
                ordinal=ordinal,
                locator=segment.locator,
                text=segment.text,
            )
        )
    audit(db, user, project_id, "source.replaced", "source", source.id, {"version": source.version})
    db.commit()
    return {"source": serialize_source(db, user, source), "duplicate": False}


@router.post("/sources/{source_id}/revoke")
def revoke_source(project_id: str, source_id: str, db: Db, user: Actor) -> dict[str, Any]:
    db.scalar(select(Project).where(Project.id == project_id).with_for_update())
    db.expire_all()
    project_access(db, user, project_id, write=True)
    require_role(user, SOURCE_ADMIN_ROLES)
    source = _source(db, user, project_id, source_id)
    invalidated = invalidate_source(db, source)
    source.status = "revoked"
    audit(db, user, project_id, "source.revoked", "source", source.id, {"invalidated_claims": invalidated})
    db.commit()
    return serialize_source(db, user, source)


@router.delete("/sources/{source_id}")
def delete_source(project_id: str, source_id: str, db: Db, user: Actor) -> dict[str, bool]:
    db.scalar(select(Project).where(Project.id == project_id).with_for_update())
    db.expire_all()
    project_access(db, user, project_id, write=True)
    require_role(user, SOURCE_ADMIN_ROLES)
    source = _source(db, user, project_id, source_id)
    invalidated = invalidate_source(db, source)
    source_id = source.id
    from app.privacy import purge_source_derivatives

    purge_source_derivatives(db, source)
    db.execute(delete(Evidence).where(Evidence.source_id == source_id))
    db.execute(delete(Chunk).where(Chunk.source_id == source_id))
    db.delete(source)
    audit(
        db,
        user,
        project_id,
        "source.deleted",
        "source",
        source_id,
        {"invalidated_claims": invalidated, "content_removed": True},
    )
    db.commit()
    return {"ok": True}


@router.get("/connections")
def list_connections(project_id: str, db: Db, user: Actor) -> list[dict[str, Any]]:
    project_access(db, user, project_id)
    connections = db.scalars(
        select(Connection)
        .where(Connection.project_id == project_id, Connection.org_id == user.org_id)
        .order_by(Connection.created_at.desc())
    ).all()
    return [serialize_connection(connection) for connection in connections]


@router.post("/connections/github", status_code=201)
def connect_github(project_id: str, payload: GitHubConnectionRequest, db: Db, user: Actor) -> dict[str, Any]:
    project_access(db, user, project_id, write=True)
    require_role(user, SOURCE_ADMIN_ROLES)
    try:
        repository = validate_repository(payload.repository)
        encrypted = encrypt_token(payload.token or "", settings.token_encryption_key)
    except ConnectorError as exc:
        raise HTTPException(422, str(exc)) from None
    connection = db.scalar(
        select(Connection).where(
            Connection.project_id == project_id,
            Connection.org_id == user.org_id,
            Connection.provider == "github",
            Connection.repository == repository,
        )
    )
    if connection and connection.status != "revoked":
        raise HTTPException(
            409, "This repository is already connected. Synchronize or revoke the existing connection."
        )
    if connection is None:
        connection = Connection(
            org_id=user.org_id, project_id=project_id, provider="github", repository=repository
        )
        db.add(connection)
    connection.name = repository
    connection.status = "available"
    connection.encrypted_token = encrypted or None
    connection.config = {}
    connection.last_sync_at = None
    db.flush()
    audit(
        db,
        user,
        project_id,
        "integration.connected",
        "connection",
        connection.id,
        {"provider": "github", "repository": repository, "authorization_configured": bool(encrypted)},
    )
    db.commit()
    return serialize_connection(connection)


@router.post("/connections/{connection_id}/sync", status_code=202)
def sync_connection(
    project_id: str, connection_id: str, background_tasks: BackgroundTasks, db: Db, user: Actor
) -> dict[str, Any]:
    project_access(db, user, project_id, write=True)
    require_role(user, SOURCE_ADMIN_ROLES)
    connection = _connection(db, user, project_id, connection_id)
    if connection.provider != "github":
        raise HTTPException(422, "This connector is not implemented.")
    if connection.status == "revoked":
        raise HTTPException(409, "Reconnect the repository before synchronizing.")
    pending = db.scalar(
        select(Job).where(Job.connection_id == connection.id, Job.status.in_(["queued", "running"]))
    )
    if pending:
        raise HTTPException(409, "Synchronization is already queued or running.")
    job = Job(
        org_id=user.org_id,
        project_id=project_id,
        connection_id=connection.id,
        requested_by=user.id,
        kind="github_sync",
        status="queued",
        stats={},
    )
    db.add(job)
    db.flush()
    audit(db, user, project_id, "integration.sync_requested", "job", job.id, {"connection_id": connection.id})
    db.commit()
    background_tasks.add_task(run_sync_job, job.id)
    return serialize_job(job)


@router.post("/connections/{connection_id}/revoke")
def revoke_connection(project_id: str, connection_id: str, db: Db, user: Actor) -> dict[str, Any]:
    db.scalar(select(Project).where(Project.id == project_id).with_for_update())
    db.expire_all()
    db.info.pop("inheria_evidence_context", None)
    db.info.pop("inheria_claim_rows", None)
    project_access(db, user, project_id, write=True)
    require_role(user, SOURCE_ADMIN_ROLES)
    connection = _connection(db, user, project_id, connection_id)
    # Revocation applies to the connection's complete permitted source set; admins
    # cannot use this route to learn the names of individually restricted files.
    sources = list(db.scalars(select(Source).where(Source.connection_id == connection.id)))
    for source in sources:
        invalidate_source(db, source)
        source.status = "revoked"
        source.source_metadata = {**(source.source_metadata or {}), "revoked_by_connection": True}
    for job in db.scalars(
        select(Job).where(Job.connection_id == connection.id, Job.status.in_(["queued", "running"]))
    ):
        job.status = "failed"
        job.error = "The integration was revoked."
        job.finished_at = utcnow()
    connection.status = "revoked"
    connection.encrypted_token = None
    connection.config = {}
    audit(db, user, project_id, "integration.revoked", "connection", connection.id, {"tokens_removed": True})
    db.commit()
    return serialize_connection(connection)


@router.get("/jobs")
def list_jobs(project_id: str, db: Db, user: Actor) -> list[dict[str, Any]]:
    project_access(db, user, project_id)
    require_role(user, SOURCE_ADMIN_ROLES | {"security"})
    jobs = db.scalars(
        select(Job)
        .where(Job.project_id == project_id, Job.org_id == user.org_id)
        .order_by(Job.created_at.desc())
        .limit(100)
    ).all()
    return [serialize_job(job) for job in jobs]
