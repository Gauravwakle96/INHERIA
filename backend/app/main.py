from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, text

from app import models as m
from app.config import settings
from app.database import SessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.environment != "production":
        m.Base.metadata.create_all(engine)
    with SessionLocal() as db:
        # In-process jobs cannot survive restart; expose interruption instead of fake progress.
        for job in db.scalars(select(m.Job).where(m.Job.status.in_(["queued", "running", "syncing"]))):
            job.status, job.error = "failed", "Interrupted by server restart. Retry synchronisation."
        for run in db.scalars(
            select(m.Investigation).where(m.Investigation.status.in_(["queued", "running"]))
        ):
            run.status, run.report = (
                "failed",
                {"summary": "Interrupted by server restart. Retry investigation."},
            )
        for turn in db.scalars(select(m.ChatTurn).where(m.ChatTurn.status == "running")):
            turn.status = "failed"
            turn.response = {
                "answer": "Reply interrupted by server restart. Send the message again.",
                "engine": "failed",
                "known": False,
                "parts": [],
                "unknowns": [],
                "actions": [],
            }
        if settings.demo_mode:
            from app.seed import seed_demo

            seed_demo(db)
            from app.intelligence import reconstruct_project

            demo_project = db.scalar(select(m.Project).where(m.Project.is_demo.is_(True)))
            actor = db.scalar(select(m.User).where(m.User.email == "alex@nexora.example"))
            if demo_project and actor:
                reconstruct_project(db, actor, demo_project.id)
        db.commit()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="INHERIA Knowledge Continuity API", version="0.1.0", lifespan=lifespan)
    windows: dict[tuple, deque] = defaultdict(deque)

    @app.middleware("http")
    async def trust_boundary(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            if origin and origin not in settings.allowed_origins:
                return JSONResponse(
                    {"detail": "Request origin is not permitted.", "request_id": request_id}, status_code=403
                )
        path = request.url.path
        if path.startswith("/api/") and path not in {"/api/health", "/api/ready"}:
            category = (
                "auth"
                if path.startswith("/api/auth/") and request.method == "POST"
                else "expensive"
                if request.method == "POST"
                and any(
                    x in path
                    for x in ["/sync", "/investigations", "/successor/ask", "/messages", "/ai-settings/test"]
                )
                else "api"
            )
            limit = {"auth": 20, "expensive": 15, "api": 400}[category]
            key = ((request.client.host if request.client else "local"), category)
            now = time.monotonic()
            values = windows[key]
            while values and values[0] < now - 60:
                values.popleft()
            if len(values) >= limit:
                return JSONResponse(
                    {"detail": "Request limit reached. Retry in one minute.", "request_id": request_id},
                    status_code=429,
                    headers={"Retry-After": "60"},
                )
            values.append(now)
            if len(windows) > 10000:
                stale_keys = [k for k, q in windows.items() if not q or q[-1] < now - 60]
                for stale in stale_keys:
                    windows.pop(stale, None)
        try:
            response = await call_next(request)
        except Exception as exc:
            logging.getLogger("inheria").error(
                "request_failed request_id=%s error_type=%s method=%s",
                request_id,
                type(exc).__name__,
                request.method,
            )
            return JSONResponse(
                {
                    "detail": "An internal error occurred. Retry or contact an administrator with the request ID.",
                    "request_id": request_id,
                },
                status_code=500,
            )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        if settings.environment == "production":
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "style-src-attr 'unsafe-inline'; img-src 'self' data:; font-src 'self'; "
                "connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
            )
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Default errors may echo passwords/tokens/source payloads in `input`.
        errors = [
            {"location": ".".join(str(x) for x in error["loc"]), "message": error["msg"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            {
                "detail": "; ".join(f"{e['location']}: {e['message']}" for e in errors),
                "request_id": getattr(request.state, "request_id", None),
            },
            status_code=422,
        )

    from app.routers.auth import router as auth_router
    from app.routers.chat import router as chat_router
    from app.routers.sources import router as sources_router
    from app.routers.workspace import router as workspace_router

    app.include_router(auth_router)
    app.include_router(sources_router)
    app.include_router(workspace_router)
    app.include_router(chat_router)

    @app.get("/api/health", tags=["Health"])
    def health():
        return {
            "status": "ok",
            "version": "0.1.0",
            "demo_mode": settings.demo_mode,
            "ai_mode": "llm-optional" if settings.llm_enabled else "deterministic-v1",
        }

    @app.get("/api/ready", tags=["Health"])
    def ready():
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception:
            return JSONResponse({"status": "unavailable"}, status_code=503)
        return {"status": "ready"}

    frontend = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend.exists():
        assets = frontend / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str):
            if path.startswith("api/"):
                return JSONResponse({"detail": "API route not found."}, status_code=404)
            safe_path = (frontend / path).resolve()
            if safe_path.is_relative_to(frontend.resolve()) and safe_path.is_file():
                return FileResponse(safe_path)
            return FileResponse(frontend / "index.html")

    return app


app = create_app()
