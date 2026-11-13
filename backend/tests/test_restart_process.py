"""Actual worker process exits after a checkpoint; a new API process resumes it."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx


def test_process_restart_resumes_committed_checkpoint_without_duplicate_claims(tmp_path):
    env = {
        **os.environ,
        "INHERIA_DATABASE_URL": "sqlite:///" + str(tmp_path / "restart.db").replace("\\", "/"),
        "INHERIA_ENVIRONMENT": "development",
        "INHERIA_DEMO_MODE": "false",
        "INHERIA_LLM_ENABLED": "false",
        "INHERIA_SECURE_COOKIES": "false",
    }
    seed = r"""
import os
from app import models as m
from app.database import engine, SessionLocal
from app.ingestion import ingest_document
from app.intelligence import reconstruct_project
from app.security import hash_password
m.Base.metadata.create_all(engine)
with SessionLocal() as db:
    org=m.Organisation(name='Process restart QA');db.add(org);db.flush()
    user=m.User(id='restart-user',org_id=org.id,name='Restart Tester',email='restart@example.com',role='admin',password_hash=hash_password('restart-only-test-password'));db.add(user);db.flush()
    project=m.Project(id='restart-project',org_id=org.id,name='Restart test');db.add(project);db.flush()
    db.add(m.Membership(project_id=project.id,user_id=user.id,role='admin'));db.flush()
    first,_=ingest_document(db,user,project.id,filename='one.md',content=b'Decision: First release\nRationale: Test restart durability.')
    ingest_document(db,user,project.id,filename='two.md',content=b'Dependency: release-pipeline -> image-registry')
    reconstruct_project(db,user,project.id,source_ids={first.id})
    db.add(m.Investigation(id='restart-run',org_id=org.id,project_id=project.id,created_by=user.id,status='running',report={'checkpoint':{'sources':{first.id:first.version},'added_candidates':1}}))
    db.commit()
os._exit(23)
"""
    worker = subprocess.run(
        [sys.executable, "-c", seed],
        env=env,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        timeout=30,
    )
    assert worker.returncode == 23
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        env=env,
        cwd=Path(__file__).resolve().parents[1],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=30) as client:
            deadline = time.monotonic() + 20
            while True:
                try:
                    if client.get("/api/ready").status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                assert time.monotonic() < deadline, "Isolated QA API did not start."
                time.sleep(0.15)
            auth = client.post(
                "/api/auth/login",
                json={"email": "restart@example.com", "password": "restart-only-test-password"},
            )
            assert auth.status_code == 200
            client.headers["X-CSRF-Token"] = auth.json()["csrf_token"]
            base = "/api/projects/restart-project"
            runs = client.get(base + "/investigations").json()
            assert runs[0]["status"] == "interrupted"
            before = client.get(base + "/claims").json()
            assert len(before) == 1
            assert client.post(base + "/investigations/restart-run/resume").status_code == 202
            deadline = time.monotonic() + 20
            while client.get(base + "/investigations").json()[0]["status"] != "completed":
                assert time.monotonic() < deadline
                time.sleep(0.1)
            after = client.get(base + "/claims").json()
            assert len(after) == 2
            assert sum(c["id"] == before[0]["id"] for c in after) == 1
            assert client.post(base + "/investigations/restart-run/resume").status_code == 409
    finally:
        server.terminate()
        server.wait(timeout=10)
