"""Authentication endpoints with narrow response schemas and opaque cookie sessions."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Organisation, User
from app.security import (
    COOKIE_NAME,
    create_session,
    current_user,
    hash_password,
    login_rate_limit,
    user_payload,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
Db = Annotated[Session, Depends(get_db)]
Current = Annotated[User, Depends(current_user)]


class PublicUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    org_id: str
    name: str
    email: str
    title: str
    role: str


class SessionResponse(BaseModel):
    user: PublicUser
    csrf_token: str


class LoginBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)


class RegisterBody(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=12, max_length=1024)
    organisation: str = Field(min_length=2, max_length=150)

    @field_validator("name", "organisation")
    @classmethod
    def meaningful_label(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Use at least two visible characters")
        return value


class DemoBody(BaseModel):
    user_id: str = Field(min_length=1, max_length=36)


@router.get("/demo-users", response_model=list[PublicUser])
def demo_users(db: Db):
    if not settings.demo_mode:
        raise HTTPException(404, "Demonstration accounts are disabled")
    return db.scalars(
        select(User)
        .join(Organisation, Organisation.id == User.org_id)
        .where(Organisation.is_demo.is_(True), User.active.is_(True))
        .order_by(User.name)
    ).all()


@router.post("/demo-login", response_model=SessionResponse)
def demo_login(body: DemoBody, request: Request, response: Response, db: Db):
    login_rate_limit(request)
    if not settings.demo_mode:
        raise HTTPException(404, "Demonstration accounts are disabled")
    user = db.get(User, body.user_id)
    org = db.get(Organisation, user.org_id) if user else None
    if not user or not user.active or not org or not org.is_demo:
        raise HTTPException(403, "This account is not an authorised demonstration identity")
    return create_session(db, user, response, request)


@router.post("/login", response_model=SessionResponse)
def login(body: LoginBody, request: Request, response: Response, db: Db):
    login_rate_limit(request)
    user = db.scalar(select(User).where(User.email == str(body.email).lower()))
    # Use a dummy hash to avoid the fast missing-user branch exposing account existence.
    encoded = user.password_hash if user else _dummy_hash
    valid = verify_password(encoded, body.password)
    if not valid or not user or not user.active:
        raise HTTPException(401, "Email or password is incorrect")
    return create_session(db, user, response, request)


@router.post("/register", response_model=SessionResponse, status_code=201)
def register(body: RegisterBody, request: Request, response: Response, db: Db):
    login_rate_limit(request)
    org = Organisation(name=body.organisation.strip(), industry="technology", is_demo=False)
    db.add(org)
    db.flush()
    user = User(
        org_id=org.id,
        name=body.name.strip(),
        email=str(body.email).lower(),
        password_hash=hash_password(body.password),
        role="admin",
        title="Organisation Administrator",
    )
    db.add(user)
    try:
        db.flush()
        return create_session(db, user, response, request)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with that email already exists") from None


@router.get("/me", response_model=SessionResponse)
def me(request: Request, user: Current):
    return {"user": user_payload(user), "csrf_token": request.state.session_record.csrf_token}


@router.post("/logout")
def logout(request: Request, response: Response, db: Db, user: Current):
    db.delete(request.state.session_record)
    db.commit()
    response.delete_cookie(
        COOKIE_NAME, path="/", secure=settings.secure_cookies, httponly=True, samesite="strict"
    )
    return {"ok": True}


_dummy_hash = hash_password("timing-only-not-a-login-credential")
