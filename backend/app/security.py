"""Cookie sessions, CSRF checks, project/source authorisation and safe audit records."""

import hashlib
import secrets
import time
from collections import defaultdict, deque
from datetime import timedelta
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Audit, Membership, Project, SessionRecord, Source, User, utcnow

password_hasher = PasswordHasher()
COOKIE_NAME = "inheria_session"
_login_attempts: dict[str, deque] = defaultdict(deque)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(encoded: str, password: str) -> bool:
    try:
        return password_hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def user_payload(user: User) -> dict:
    return {key: getattr(user, key) for key in ("id", "org_id", "name", "email", "title", "role")}


def require_origin(request: Request):
    origin = request.headers.get("origin")
    if origin is not None and origin not in settings.allowed_origins:
        raise HTTPException(403, "Request origin is not authorised")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Cross-site requests are not permitted")


def verify_csrf(request: Request, session: SessionRecord):
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    require_origin(request)
    supplied = request.headers.get("x-csrf-token", "")
    if not supplied or not secrets.compare_digest(supplied, session.csrf_token):
        raise HTTPException(403, "Session security token is missing or invalid; refresh and retry")


def login_rate_limit(request: Request):
    require_origin(request)
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    records = _login_attempts[key]
    while records and records[0] < now - 60:
        records.popleft()
    if len(records) >= 15:
        raise HTTPException(429, "Too many sign-in attempts. Try again in one minute")
    records.append(now)
    # Keep this single-process local limiter bounded. Distributed deployments need a shared limiter.
    if len(_login_attempts) > 10_000:
        expired = [
            item for item, attempts in _login_attempts.items() if not attempts or attempts[-1] < now - 60
        ]
        for item in expired:
            _login_attempts.pop(item, None)


def create_session(db: Session, user: User, response: Response, request: Request | None = None):
    if request:
        old = request.cookies.get(COOKIE_NAME)
        if old:
            record = db.scalar(
                select(SessionRecord).where(
                    SessionRecord.token_hash == hashlib.sha256(old.encode()).hexdigest()
                )
            )
            if record:
                db.delete(record)
    token = secrets.token_urlsafe(48)
    record = SessionRecord(
        user_id=user.id,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        csrf_token=secrets.token_urlsafe(32),
        expires_at=utcnow() + timedelta(hours=settings.session_hours),
    )
    db.add(record)
    audit(db, user, None, "session.created", "user", user.id, {})
    db.commit()
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="strict",
        path="/",
        max_age=settings.session_hours * 3600,
    )
    return {"user": user_payload(user), "csrf_token": record.csrf_token}


def current_user(request: Request, db: Annotated[Session, Depends(get_db)]) -> User:
    token = request.cookies.get(COOKIE_NAME, "")
    if not token or len(token) > 200:
        raise HTTPException(401, "Sign in to access this workspace")
    record = db.scalar(
        select(SessionRecord).where(
            SessionRecord.token_hash == hashlib.sha256(token.encode()).hexdigest(),
            SessionRecord.expires_at > utcnow(),
        )
    )
    if not record:
        raise HTTPException(401, "Session expired. Please sign in again")
    user = db.get(User, record.user_id)
    if not user or not user.active:
        raise HTTPException(401, "This account is unavailable")
    verify_csrf(request, record)
    request.state.session_record = record
    return user


def require_role(user: User, roles: set | list | tuple):
    if user.role not in roles:
        raise HTTPException(403, "Your role does not permit this action")


def project_access(db: Session, user: User, project_id: str, write: bool = False) -> Project:
    project = db.get(Project, project_id)
    if not project or project.org_id != user.org_id:
        raise HTTPException(404, "Project not found or access is unavailable")
    member = db.scalar(
        select(Membership).where(Membership.project_id == project_id, Membership.user_id == user.id)
    )
    if not member:
        raise HTTPException(404, "Project not found or access is unavailable")
    if write and user.role not in {"admin", "manager", "lead"}:
        raise HTTPException(403, "A project administrator, manager or technical lead is required")
    if write and member.role not in {"admin", "manager", "lead"}:
        raise HTTPException(403, "Your project membership does not permit this action")
    return project


def can_read_source(db: Session, user: User, source: Source, include_inactive: bool = False) -> bool:
    if not user.active or source.org_id != user.org_id or (not include_inactive and source.status != "ready"):
        return False
    member = db.scalar(
        select(Membership.id).where(Membership.project_id == source.project_id, Membership.user_id == user.id)
    )
    if not member:
        return False
    return not source.acl or user.id in source.acl


def visible_sources(db: Session, user: User, project_id: str) -> list[Source]:
    project_access(db, user, project_id)
    if not user.active:
        return []
    sources = db.scalars(
        select(Source)
        .where(Source.org_id == user.org_id, Source.project_id == project_id)
        .order_by(Source.created_at, Source.id)
    ).all()
    # All rows share the tenant/project just authorised above. Only the source ACL
    # remains to filter; repeating membership queries per source creates an N+1.
    return [source for source in sources if not source.acl or user.id in source.acl]


def audit(
    db: Session,
    user: User,
    project_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict | None = None,
) -> Audit:
    # Audit details must be structural metadata only. Never pass file contents, tokens, or passwords.
    record = Audit(
        org_id=user.org_id,
        project_id=project_id,
        actor_id=user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
    )
    db.add(record)
    return record
