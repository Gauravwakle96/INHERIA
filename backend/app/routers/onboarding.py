"""Expiring invitations and permission-scoped access readiness requests."""

import hashlib
import secrets
from datetime import timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models as m
from app.database import get_db
from app.security import (
    audit,
    can_read_source,
    create_session,
    current_user,
    hash_password,
    login_rate_limit,
    project_access,
    require_role,
)

router = APIRouter(prefix="/api", tags=["Team onboarding & access readiness"])
Db = Annotated[Session, Depends(get_db)]
Actor = Annotated[m.User, Depends(current_user)]


class InviteBody(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=100)
    title: str = Field(min_length=2, max_length=100)
    role: Literal["employee", "incoming", "lead", "manager"] = "incoming"
    expires_hours: int = Field(default=48, ge=1, le=168)


class JoinBody(BaseModel):
    token: str = Field(min_length=32, max_length=200)
    password: str | None = Field(default=None, min_length=12, max_length=1024)


class AccessBody(BaseModel):
    purpose: str = Field(min_length=10, max_length=2000)


class AccessDecision(BaseModel):
    action: Literal["approve", "reject"]
    source_id: str | None = Field(default=None, max_length=36)
    note: str = Field(min_length=10, max_length=2000)


class RevokeMemberBody(BaseModel):
    note: str = Field(min_length=10, max_length=2000)


@router.post("/projects/{project_id}/members/{member_id}/revoke")
def revoke_member(project_id: str, member_id: str, body: RevokeMemberBody, db: Db, user: Actor):
    project_access(db, user, project_id, write=True)
    require_role(user, {"admin"})
    clean(body.note)
    # Serialize membership changes with invitation acceptance on PostgreSQL.
    db.scalar(select(m.Project).where(m.Project.id == project_id).with_for_update())
    project_access(db, user, project_id, write=True)
    if member_id == user.id:
        raise HTTPException(409, "Ask another administrator to revoke your membership.")
    person = db.get(m.User, member_id)
    member = db.scalar(
        select(m.Membership).where(m.Membership.project_id == project_id, m.Membership.user_id == member_id)
    )
    if not person or person.org_id != user.org_id or not member:
        raise HTTPException(404, "Project member unavailable.")
    for invitation in db.scalars(
        select(m.Invitation).where(
            m.Invitation.project_id == project_id,
            m.Invitation.email == person.email,
            m.Invitation.status == "pending",
        )
    ):
        invitation.status = "revoked"
    for request in db.scalars(
        select(m.AccessRequest).where(
            m.AccessRequest.project_id == project_id,
            m.AccessRequest.requested_by == member_id,
            m.AccessRequest.status == "pending",
        )
    ):
        request.status, request.reviewed_by = "revoked", user.id
        request.note = "Project membership revoked. A new invitation and access review are required."
    for source in db.scalars(select(m.Source).where(m.Source.project_id == project_id)):
        if member_id in source.acl:
            source.acl = [reader for reader in source.acl if reader != member_id]
            if not source.acl:
                # An empty ACL means all members: never widen a last-reader source.
                source.acl = [member_id]
                source.status = "revoked"
                from app.ingestion import invalidate_source

                invalidate_source(db, source)
            audit(db, user, project_id, "source.reader_revoked", "source", source.id, {"user_id": member_id})
    db.delete(member)
    audit(db, user, project_id, "membership.revoked", "user", member_id, {})
    db.commit()
    return {
        "status": "revoked",
        "user_id": member_id,
        "scope": "Project access removed. Historical contributions and other project memberships remain.",
    }


@router.get("/projects/{project_id}/access-readiness")
def access_readiness(project_id: str, db: Db, user: Actor):
    project_access(db, user, project_id)
    from app.intelligence import current_claims

    reviewer = user.role in {"admin", "manager", "lead"}
    visible = {c.id for c in current_claims(db, user, project_id, verified=True)}
    results = []
    for transition in db.scalars(
        select(m.Transition)
        .where(m.Transition.project_id == project_id)
        .order_by(m.Transition.updated_at.desc())
        .limit(50)
    ):
        if not reviewer and transition.successor_id != user.id:
            continue
        person = db.get(m.User, transition.successor_id)
        member = db.scalar(
            select(m.Membership.id).where(
                m.Membership.project_id == project_id, m.Membership.user_id == transition.successor_id
            )
        )
        active = bool(person and person.active and member)
        allowed = {c.id for c in current_claims(db, person, project_id, verified=True)} if active else set()
        snapshot = (transition.report or {}).get("knowledge", [])
        # Reveal descriptions only when the requesting actor can read that claim.
        missing = [item for item in snapshot if item["id"] not in allowed]
        results.append(
            {
                "transition_id": transition.id,
                "title": transition.title,
                "successor_name": person.name if person and member else "Incoming participant unavailable",
                "membership_active": active,
                "required_items": len(snapshot),
                "accessible_items": len(snapshot) - len(missing),
                "missing_items": len(missing),
                "ready": active and bool(snapshot) and not missing,
                "missing_titles": [item["title"] for item in missing if item["id"] in visible],
                "next_step": "Generate a reviewed handover first."
                if not snapshot
                else "Request authorised knowledge access and revalidation."
                if missing or not active
                else "Knowledge access is ready; acceptance and practical review are separate checks.",
            }
        )
    return results


def clean(value):
    from app.routers.workspace import safe_text

    safe_text(value)


def invitation_json(item):
    return {
        k: getattr(item, k)
        for k in ("id", "email", "name", "title", "role", "status", "expires_at", "created_at")
    }


@router.post("/projects/{project_id}/invitations", status_code=201)
def invite(project_id: str, body: InviteBody, db: Db, user: Actor):
    project_access(db, user, project_id, write=True)
    require_role(user, {"admin"})
    clean(body.name)
    clean(body.title)
    email = str(body.email).lower()
    existing = db.scalar(select(m.User).where(m.User.email == email))
    if existing and existing.org_id != user.org_id:
        raise HTTPException(
            409, "This invitation cannot join the account to this organisation. Use a separate account."
        )
    if existing and db.scalar(
        select(m.Membership).where(m.Membership.project_id == project_id, m.Membership.user_id == existing.id)
    ):
        raise HTTPException(409, "This person already belongs to this project.")
    for old in db.scalars(
        select(m.Invitation).where(
            m.Invitation.project_id == project_id,
            m.Invitation.email == email,
            m.Invitation.status == "pending",
        )
    ):
        old.status = "revoked"
    token = secrets.token_urlsafe(48)
    item = m.Invitation(
        org_id=user.org_id,
        project_id=project_id,
        email=email,
        name=body.name.strip(),
        title=body.title.strip(),
        role=body.role,
        created_by=user.id,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        expires_at=m.utcnow() + timedelta(hours=body.expires_hours),
    )
    db.add(item)
    db.flush()
    audit(db, user, project_id, "invitation.created", "invitation", item.id, {"role": item.role})
    db.commit()
    return {
        **invitation_json(item),
        "join_path": "/join#token=" + token,
        "delivery": "Share this one-time link through an authorised channel. No email has been sent.",
    }


@router.get("/projects/{project_id}/invitations")
def invitations(project_id: str, db: Db, user: Actor):
    project_access(db, user, project_id, write=True)
    require_role(user, {"admin"})
    return [
        {
            **invitation_json(item),
            "status": "expired"
            if item.status == "pending" and item.expires_at <= m.utcnow()
            else item.status,
        }
        for item in db.scalars(
            select(m.Invitation)
            .where(m.Invitation.project_id == project_id)
            .order_by(m.Invitation.created_at.desc())
            .limit(50)
        )
    ]


@router.post("/projects/{project_id}/invitations/{invitation_id}/revoke")
def revoke(project_id: str, invitation_id: str, db: Db, user: Actor):
    project_access(db, user, project_id, write=True)
    require_role(user, {"admin"})
    item = db.get(m.Invitation, invitation_id)
    if not item or item.project_id != project_id or item.org_id != user.org_id:
        raise HTTPException(404, "Invitation unavailable.")
    if item.status != "pending":
        raise HTTPException(409, "Only pending invitations can be revoked.")
    item.status = "revoked"
    audit(db, user, project_id, "invitation.revoked", "invitation", item.id, {})
    db.commit()
    return invitation_json(item)


@router.post("/auth/invitation/accept")
def accept(body: JoinBody, request: Request, response: Response, db: Db):
    login_rate_limit(request)
    item = db.scalar(
        select(m.Invitation).where(
            m.Invitation.token_hash == hashlib.sha256(body.token.encode()).hexdigest(),
            m.Invitation.status == "pending",
            m.Invitation.expires_at > m.utcnow(),
        )
    )
    if not item:
        raise HTTPException(
            404, "Invitation expired, revoked or already used. Ask your administrator for a new link."
        )
    db.scalar(select(m.Project).where(m.Project.id == item.project_id).with_for_update())
    consumed = db.execute(
        update(m.Invitation)
        .where(
            m.Invitation.id == item.id, m.Invitation.status == "pending", m.Invitation.expires_at > m.utcnow()
        )
        .values(status="accepted")
    )
    if consumed.rowcount != 1:
        raise HTTPException(409, "Invitation was already used or revoked.")
    existing = db.scalar(select(m.User).where(m.User.email == item.email))
    if existing:
        person = current_user(request, db)
        if person.id != existing.id or person.org_id != item.org_id or not person.active:
            raise HTTPException(403, "Sign in with the invited account before joining this project.")
        # Existing identity roles are never elevated through an invitation.
        member_role = (
            "employee"
            if person.role == "employee"
            else "incoming"
            if person.role == "incoming"
            else item.role
        )
    else:
        if not body.password:
            raise HTTPException(422, "Set your own password of at least 12 characters to accept.")
        person = m.User(
            org_id=item.org_id,
            email=item.email,
            name=item.name,
            title=item.title,
            role=item.role,
            password_hash=hash_password(body.password),
        )
        db.add(person)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                409, "Account changed while joining. Sign in and request a new invitation."
            ) from None
        member_role = item.role
    if not db.scalar(
        select(m.Membership).where(
            m.Membership.project_id == item.project_id, m.Membership.user_id == person.id
        )
    ):
        db.add(m.Membership(project_id=item.project_id, user_id=person.id, role=member_role))
    audit(db, person, item.project_id, "invitation.accepted", "invitation", item.id, {})
    try:
        db.flush()
        return create_session(db, person, response, request)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409, "The account or membership changed. Sign in and request a new invitation."
        ) from None


def access_json(item):
    return {
        k: getattr(item, k)
        for k in ("id", "requested_by", "purpose", "status", "note", "reviewed_by", "created_at")
    }


@router.post("/projects/{project_id}/access-requests", status_code=201)
def request_access(project_id: str, body: AccessBody, db: Db, user: Actor):
    project_access(db, user, project_id)
    clean(body.purpose)
    item = m.AccessRequest(
        org_id=user.org_id, project_id=project_id, requested_by=user.id, purpose=body.purpose
    )
    db.add(item)
    db.flush()
    audit(db, user, project_id, "access.requested", "access_request", item.id, {})
    db.commit()
    return access_json(item)


@router.get("/projects/{project_id}/access-requests")
def access_requests(project_id: str, db: Db, user: Actor):
    project_access(db, user, project_id)
    query = select(m.AccessRequest).where(m.AccessRequest.project_id == project_id)
    if user.role not in {"admin", "manager", "lead"}:
        query = query.where(m.AccessRequest.requested_by == user.id)
    return [
        access_json(item) for item in db.scalars(query.order_by(m.AccessRequest.created_at.desc()).limit(50))
    ]


@router.post("/projects/{project_id}/access-requests/{request_id}/review")
def access_review(project_id: str, request_id: str, body: AccessDecision, db: Db, user: Actor):
    project_access(db, user, project_id, write=True)
    db.scalar(select(m.Project).where(m.Project.id == project_id).with_for_update())
    project_access(db, user, project_id, write=True)
    clean(body.note)
    item = db.get(m.AccessRequest, request_id)
    if not item or item.org_id != user.org_id or item.project_id != project_id:
        raise HTTPException(404, "Access request unavailable.")
    if item.requested_by == user.id:
        raise HTTPException(403, "Another authorised reviewer must decide your access request.")
    if item.status != "pending":
        raise HTTPException(409, "This request was already reviewed.")
    person = db.get(m.User, item.requested_by)
    project_access(db, person, project_id)
    if body.action == "approve":
        source = db.get(m.Source, body.source_id) if body.source_id else None
        if not source or source.project_id != project_id or not can_read_source(db, user, source):
            raise HTTPException(404, "Select an active source you are authorised to share.")
        if source.acl:
            source.acl = sorted(set(source.acl) | {person.id})
        item.source_id = source.id
        audit(db, user, project_id, "source.access_granted", "source", source.id, {"user_id": person.id})
    item.status = "approved" if body.action == "approve" else "rejected"
    # Do not include hidden source titles, content, or system credentials in the decision.
    item.note, item.reviewed_by = body.note, user.id
    audit(db, user, project_id, "access." + item.status, "access_request", item.id, {})
    db.commit()
    return access_json(item)
