"""Production boundaries exercised without provider credentials or paid services."""

from pathlib import Path

import pytest

from app.config import Settings, settings


@pytest.mark.parametrize("prefix", ["postgres://", "postgresql://", "postgresql+psycopg://"])
def test_provider_postgres_urls_keep_ssl_and_use_installed_driver(prefix):
    config = Settings(_env_file=None, database_url=prefix + "user:placeholder@host/db?sslmode=require")
    assert config.database_url == "postgresql+psycopg://user:placeholder@host/db?sslmode=require"
    assert "placeholder" not in repr(config)


def production(**kwargs):
    return Settings(
        _env_file=None,
        environment="production",
        demo_mode=False,
        database_url="postgresql://user:placeholder@host/db?sslmode=require",
        **kwargs,
    )


def test_render_origin_is_exact_and_explicit_override_wins():
    config = production(RENDER_EXTERNAL_URL="https://inheria.onrender.com")
    assert config.allowed_origins == ["https://inheria.onrender.com"]
    overridden = production(
        RENDER_EXTERNAL_URL="https://inheria.onrender.com", allowed_origins=["https://continuity.example"]
    )
    assert overridden.allowed_origins == ["https://continuity.example"]


@pytest.mark.parametrize(
    "origin",
    ["http://inheria.example", "https://", "https://inheria.example/path", "https://user@inheria.example"],
)
def test_production_rejects_inexact_origins(origin):
    with pytest.raises(ValueError):
        production(allowed_origins=[origin])


def test_production_requires_origins():
    with pytest.raises(ValueError):
        production(allowed_origins=[])


def test_readiness_does_not_leak_database_errors(workspace, monkeypatch):
    client, _, _ = workspace
    assert client.get("/api/ready").json() == {"status": "ready"}

    class Unavailable:
        def connect(self):
            raise RuntimeError("credential-that-must-never-leak")

    monkeypatch.setattr("app.main.engine", Unavailable())
    response = client.get("/api/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "credential" not in response.text


def test_production_csp_and_secure_cookie_boundary(workspace, monkeypatch):
    client, _, _ = workspace
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "allowed_origins", ["https://inheria.example"])
    response = client.get("/api/health")
    csp = response.headers["content-security-policy"]
    assert "script-src 'self';" in csp
    assert "style-src 'self';" in csp
    assert "style-src-attr 'unsafe-inline';" in csp
    assert "max-age=" in response.headers["strict-transport-security"]
    assert client.get("/api/auth/demo-users").status_code == 404
    assert (
        client.post(
            "/api/auth/register",
            headers={"Origin": "https://attacker.example"},
            json={},
        ).status_code
        == 403
    )
    response = client.post(
        "/api/auth/register",
        headers={"Origin": "https://inheria.example"},
        json={
            "name": "Production Test",
            "email": "deployment-test@example.com",
            "password": "test-fixture-password-only",
            "organisation": "Production Fixture",
        },
    )
    assert response.status_code == 201
    cookie = response.headers["set-cookie"].lower()
    assert "secure" in cookie and "httponly" in cookie and "samesite=strict" in cookie


def test_built_frontend_is_served_at_same_origin(workspace):
    root = Path(__file__).resolve().parents[2]
    if not (root / "frontend/dist/index.html").exists():
        pytest.skip("Build frontend first to exercise actual deployment artifact")
    client, _, _ = workspace
    response = client.get("/workspace/projects")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'src="/theme-init.js"' in response.text
    assert "localStorage" not in response.text
    script = client.get("/theme-init.js")
    assert script.status_code == 200
    assert "inheria-theme" in script.text
    assert client.get("/api/nonexistent-route").status_code == 404
