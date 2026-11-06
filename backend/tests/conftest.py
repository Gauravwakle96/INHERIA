import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import database
from app import models as m
from app.config import settings
from app.intelligence import reconstruct_project
from app.main import create_app
from app.security import _login_attempts
from app.seed import seed_demo


@pytest.fixture
def workspace(monkeypatch):
    _login_attempts.clear()
    monkeypatch.setattr(settings, "demo_mode", True)
    monkeypatch.setattr(settings, "llm_enabled", False)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    m.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(database, "SessionLocal", factory)
    monkeypatch.setattr(database, "engine", engine)
    import app.main as main

    monkeypatch.setattr(main, "SessionLocal", factory)
    monkeypatch.setattr(main, "engine", engine)
    with factory() as db:
        project = seed_demo(db)
        actor = db.scalar(select(m.User).where(m.User.email == "alex@nexora.example"))
        reconstruct_project(db, actor, project.id)
        db.commit()
        project_id = project.id
    app = create_app()

    def override_db():
        with factory() as db:
            yield db

    app.dependency_overrides[database.get_db] = override_db
    with TestClient(app) as client:
        yield client, factory, project_id
    engine.dispose()


def login(client, name="Maya Chen"):
    users = client.get("/api/auth/demo-users").json()
    user = next(u for u in users if u["name"] == name)
    response = client.post("/api/auth/demo-login", json={"user_id": user["id"]})
    assert response.status_code == 200, response.text
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return user
