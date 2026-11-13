"""Execute an isolated toy service release, rollback and SQLite recovery exercise.

No cloud credentials, production commands or existing application databases are used.
"""

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import httpx


def run():
    run_id = "local-" + uuid.uuid4().hex[:12]
    events = []
    with tempfile.TemporaryDirectory(prefix="inheria-isolated-exercise-") as directory:
        root = Path(directory)
        database = root / "orders.db"
        with closing(sqlite3.connect(database)) as db, db:
            db.execute("CREATE TABLE orders(id INTEGER PRIMARY KEY, total INTEGER)")
            db.executemany("INSERT INTO orders VALUES(?,?)", [(1, 120), (2, 250), (3, 430)])
        server_file = root / "server.py"
        server_file.write_text(
            """import json,sys,sqlite3
from http.server import BaseHTTPRequestHandler,HTTPServer
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  with sqlite3.connect(sys.argv[2]) as db: count=db.execute('SELECT count(*) FROM orders').fetchone()[0]
  body=json.dumps({'version':sys.argv[1],'orders':count,'healthy':sys.argv[1]!='broken-v2'}).encode()
  self.send_response(200 if sys.argv[1]!='broken-v2' else 503);self.end_headers();self.wfile.write(body)
 def log_message(self,*args): pass
server=HTTPServer(('127.0.0.1',0),Handler);print(server.server_port,flush=True);server.serve_forever()
""",
            encoding="utf-8",
        )

        def release(version):
            process = subprocess.Popen(
                [sys.executable, str(server_file), version, str(database)],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            try:
                port = int(process.stdout.readline().strip())
                response = httpx.get(f"http://127.0.0.1:{port}", timeout=5)
                events.append(
                    {
                        "operation": "release_health",
                        "version": version,
                        "status": response.status_code,
                        "observed": response.json(),
                    }
                )
                return response.status_code
            finally:
                process.terminate()
                process.wait(timeout=5)

        assert release("v1") == 200
        assert release("broken-v2") == 503
        assert release("v1") == 200
        backup = root / "orders-backup.db"
        with closing(sqlite3.connect(database)) as live, closing(sqlite3.connect(backup)) as saved:
            live.backup(saved)
        digest = hashlib.sha256(backup.read_bytes()).hexdigest()
        wrong = root / "wrong-backup.db"
        with closing(sqlite3.connect(wrong)) as db, db:
            db.execute("CREATE TABLE orders(id INTEGER PRIMARY KEY, total INTEGER)")
        restore = root / "restored.db"

        def restore_check(path):
            shutil.copyfile(path, restore)
            with closing(sqlite3.connect(restore)) as db:
                count = db.execute("SELECT count(*) FROM orders").fetchone()[0]
                integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
                total = db.execute("SELECT coalesce(sum(total),0) FROM orders").fetchone()[0]
            passed = count == 3 and integrity == "ok" and total == 800
            events.append(
                {
                    "operation": "restore_integrity",
                    "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "orders": count,
                    "total": total,
                    "integrity": integrity,
                    "passed": passed,
                }
            )
            return passed

        assert not restore_check(wrong)
        assert restore_check(backup)
    return {
        "run_id": run_id,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "environment": "isolated local test environment",
        "artifact_sha256": digest,
        "events": events,
        "passed": True,
        "scope": "Actual local toy-service process and SQLite exercises executed by the coding agent. No Wipro, AWS, production or independent human competence claim. This does not test PostgreSQL or INHERIA disaster recovery.",
    }


if __name__ == "__main__":
    result = run()
    root = Path(__file__).resolve().parents[2]
    (root / "docs/local-operational-exercise.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    note = f"""# Executed isolated local operational exercise
Procedure: recovery test evidence
System: recovery
Test environment: isolated local staging (toy service and SQLite)
Run ID: {result["run_id"]}
Timestamp: {result["executed_at"]}
Artifact: sha256:{result["artifact_sha256"]}
Observation: version v1 returned HTTP 200 with three orders; broken-v2 returned
HTTP 503. Rollback to v1 restored HTTP 200. An empty backup failed restore
validation with zero orders. The correct backup restored three orders totaling
800, and SQLite integrity_check returned ok.
Result: passed after the incorrect backup was rejected and the correct backup selected.
Evidence file: docs/local-operational-exercise.json
Executed by: coding agent in an isolated local test environment.
This records actual local execution, not Wipro/AWS/production activity or a
qualified human supervisor's assessment. It does not prove INHERIA PostgreSQL
backup/restore readiness. A separate supervisor must review its relevance.
"""
    (root / "backend/app/data/local-operational-exercise.md").write_text(note, encoding="utf-8")
    print(json.dumps({"run_id": result["run_id"], "passed": result["passed"], "events": result["events"]}))
