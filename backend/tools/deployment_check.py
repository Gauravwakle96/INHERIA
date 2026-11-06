"""Validate deployment syntax without a daemon or real credentials; export OpenAPI."""

import json
import os
import subprocess
from pathlib import Path

from app.main import create_app


def main():
    root = Path(__file__).resolve().parents[2]
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    schema = create_app().openapi()
    (docs / "openapi.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    environment = os.environ.copy()
    environment.update(
        POSTGRES_PASSWORD="validation-placeholder-only",
        INHERIA_DATABASE_URL="postgresql+psycopg://inheria:validation-placeholder-only@db:5432/inheria",
        INHERIA_ALLOWED_ORIGINS='["https://inheria.example"]',
    )
    result = subprocess.run(
        ["docker", "compose", "-f", str(root / "compose.yaml"), "config", "--quiet"],
        env=environment,
        cwd=root,
        capture_output=True,
        text=True,
    )
    print(
        json.dumps(
            {
                "openapi_paths": len(schema["paths"]),
                "compose_syntax": "pass" if result.returncode == 0 else "failed",
                "daemon_build": "not_run_docker_daemon_unavailable",
            }
        )
    )
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
