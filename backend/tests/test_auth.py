"""Authentication and source/project permission boundaries independent of domain services."""

from datetime import timedelta

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings, settings
from app.database import get_db
from app.models import Base, Membership, Organisation, Project, SessionRecord, Source, User, utcnow
from app.routers.auth import router
from app.security import (
    COOKIE_NAME,
    _login_attempts,
    can_read_source,
    current_user,
    hash_password,
    project_access,
    visible_sources,
)
from app.seed import seed_demo


@pytest.fixture
def fixture():
    _login_attempts.clear()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    db = factory()
    app = FastAPI()
    app.include_router(router)

    def override_db():
        yield db

    @app.post("/protected")
    def protected(user: User = Depends(current_user)):
        return {"name": user.name}

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, db
    db.close()
    engine.dispose()


def register(client, email="manager@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Manager One",
            "email": email,
            "password": "test-password-12345",
            "organisation": "Example Org",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_registration_hides_password_and_uses_http_only_session(fixture):
    client, db = fixture
    session = register(client)
    assert "password_hash" not in session["user"]
    assert session["user"]["role"] == "admin"
    assert client.cookies.get(COOKIE_NAME)
    record = db.scalar(select(SessionRecord))
    assert record.token_hash != client.cookies.get(COOKIE_NAME)
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["csrf_token"] == session["csrf_token"]


def test_csrf_required_for_authenticated_mutations_and_origin_checked(fixture):
    client, _ = fixture
    session = register(client)
    assert client.post("/protected").status_code == 403
    headers = {"X-CSRF-Token": session["csrf_token"]}
    assert client.post("/protected", headers=headers).status_code == 200
    assert (
        client.post("/protected", headers={**headers, "Origin": "https://untrusted.example"}).status_code
        == 403
    )
    assert client.post("/protected", headers={**headers, "Sec-Fetch-Site": "cross-site"}).status_code == 403


def test_duplicate_registration_rolls_back_new_organisation(fixture):
    client, db = fixture
    register(client)
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Other Manager",
            "email": "manager@example.com",
            "password": "test-password-12345",
            "organisation": "Orphan Org",
        },
    )
    assert response.status_code == 409
    assert len(db.scalars(select(Organisation)).all()) == 1


def test_login_rotation_logout_and_expiry(fixture):
    client, db = fixture
    register(client)
    old_cookie = client.cookies.get(COOKIE_NAME)
    assert (
        client.post("/api/auth/login", json={"email": "manager@example.com", "password": "bad"}).status_code
        == 401
    )
    response = client.post(
        "/api/auth/login", json={"email": "manager@example.com", "password": "test-password-12345"}
    )
    assert response.status_code == 200
    assert client.cookies.get(COOKIE_NAME) != old_cookie
    assert len(db.scalars(select(SessionRecord)).all()) == 1
    csrf = response.json()["csrf_token"]
    assert client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    client.post("/api/auth/login", json={"email": "manager@example.com", "password": "test-password-12345"})
    db.scalar(select(SessionRecord)).expires_at = utcnow() - timedelta(seconds=1)
    db.commit()
    assert client.get("/api/auth/me").status_code == 401


def test_demo_accounts_are_synthetic_and_disabled_outside_demo(fixture, monkeypatch):
    client, db = fixture
    project = seed_demo(db)
    response = client.get("/api/auth/demo-users")
    assert response.status_code == 200
    assert len(response.json()) == 5
    assert all(person["email"].endswith("@nexora.example") for person in response.json())
    assert client.post("/api/auth/demo-login", json={"user_id": response.json()[0]["id"]}).status_code == 200
    assert len(db.scalars(select(Source).where(Source.project_id == project.id)).all()) == 125
    monkeypatch.setattr(settings, "demo_mode", False)
    assert client.get("/api/auth/demo-users").status_code == 404
    assert client.post("/api/auth/demo-login", json={"user_id": response.json()[0]["id"]}).status_code == 404


def test_project_and_source_acl_deny_admin_bypass(fixture):
    client, db = fixture
    first = register(client)["user"]
    user = db.get(User, first["id"])
    project = Project(org_id=user.org_id, name="Private project")
    db.add(project)
    db.flush()
    with pytest.raises(Exception) as denied:
        project_access(db, user, project.id)
    assert denied.value.status_code == 404
    db.add(Membership(project_id=project.id, user_id=user.id, role="admin"))
    other = User(
        org_id=user.org_id,
        name="Source owner",
        email="owner@example.com",
        title="Lead",
        role="lead",
        password_hash=hash_password("test-password-12345"),
    )
    db.add(other)
    db.flush()
    db.add(Membership(project_id=project.id, user_id=other.id, role="lead"))
    source = Source(org_id=user.org_id, project_id=project.id, name="Restricted", kind="txt", acl=[other.id])
    db.add(source)
    db.commit()
    assert project_access(db, user, project.id).id == project.id
    assert not can_read_source(db, user, source)
    assert visible_sources(db, user, project.id) == []
    assert can_read_source(db, other, source)
    source.status = "revoked"
    db.commit()
    assert not can_read_source(db, other, source)
    assert visible_sources(db, other, project.id)[0].status == "revoked"


def test_cross_tenant_and_employee_write_denied(fixture):
    client, db = fixture
    first = register(client)["user"]
    project = Project(org_id=first["org_id"], name="Project A")
    db.add(project)
    db.flush()
    db.add(Membership(project_id=project.id, user_id=first["id"], role="admin"))
    second = register(client, "other@example.com")["user"]
    other = db.get(User, second["id"])
    with pytest.raises(Exception) as denied:
        project_access(db, other, project.id)
    assert denied.value.status_code == 404
    member = db.get(User, first["id"])
    member.role = "employee"
    db.commit()
    with pytest.raises(Exception) as forbidden:
        project_access(db, member, project.id, write=True)
    assert forbidden.value.status_code == 403


def test_settings_do_not_repr_credentials_and_reject_unsafe_production():
    configured = Settings(llm_api_key="not-a-real-key", token_encryption_key="not-a-real-token")
    assert "not-a-real" not in repr(configured)
    with pytest.raises(ValueError):
        Settings(environment="production", demo_mode=True)
    with pytest.raises(ValueError):
        Settings(environment="production", demo_mode=False, database_url="sqlite://")


def test_migrations_upgrade_and_downgrade_owned_test_database(tmp_path, monkeypatch):
    from pathlib import Path

    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect

    path = tmp_path / "migration-test.db"
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{path.as_posix()}")
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    engine = create_engine(settings.database_url)
    assert set(Base.metadata.tables).issubset(set(inspect(engine).get_table_names()))
    assert "source_version" in {column["name"] for column in inspect(engine).get_columns("chunks")}
    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    engine.dispose()


def test_source_inventory_queries_are_bounded_and_inactive_users_are_excluded(fixture):
    from sqlalchemy import event

    _, db = fixture
    project = seed_demo(db)
    manager = db.scalar(select(User).where(User.email == "maya@nexora.example"))
    queries = []

    def record_select(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    event.listen(db.bind, "before_cursor_execute", record_select)
    try:
        assert len(visible_sources(db, manager, project.id)) == 125
        assert len(queries) <= 3
        manager.active = False
        assert visible_sources(db, manager, project.id) == []
    finally:
        event.remove(db.bind, "before_cursor_execute", record_select)
