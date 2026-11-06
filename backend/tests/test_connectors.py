from __future__ import annotations

import base64
from datetime import datetime

import httpx
import pytest
from cryptography.fernet import Fernet

from app.connectors import ConnectorError, GitHubConnector, decrypt_token, encrypt_token, validate_repository


def response(request, payload, status=200, headers=None):
    return httpx.Response(status, json=payload, headers=headers or {}, request=request)


def test_repository_selection_never_accepts_arbitrary_hosts_or_paths():
    assert validate_repository("https://github.com/fastapi/fastapi") == "fastapi/fastapi"
    assert validate_repository("django/django") == "django/django"
    for value in [
        "https://evil.example/repo",
        "../../private",
        "owner/repo?token=secret",
        "owner/repo/tree/main",
        "owner/../repo",
    ]:
        with pytest.raises(ConnectorError):
            validate_repository(value)


def test_tree_without_explicit_completeness_never_invalidates_known_files():
    def handler(request):
        if request.url.path == "/repos/test/repo":
            return response(request, {"default_branch": "main", "topics": []})
        if "/git/trees/" in request.url.path:
            return response(request, {"tree": []})
        return response(request, [], 200)

    with GitHubConnector(
        "test/repo", known_file_ids=["github:file:docs/runbook.md"], transport=httpx.MockTransport(handler)
    ) as connector:
        snapshot = connector.fetch()
    assert "github:file:docs/runbook.md" not in snapshot.deleted_file_ids


def test_private_authorization_is_encrypted_and_bad_configuration_fails():
    key = Fernet.generate_key().decode()
    token = "fake-test-authorization"
    encrypted = encrypt_token(token, key)
    assert token not in encrypted and decrypt_token(encrypted, key) == token
    assert encrypt_token("", "") == ""
    with pytest.raises(ConnectorError, match="INHERIA_TOKEN_ENCRYPTION_KEY"):
        encrypt_token(token, "")
    with pytest.raises(ConnectorError, match="decrypt"):
        decrypt_token(encrypted, Fernet.generate_key().decode())


def test_gitHub_fetches_real_endpoint_shapes_and_does_not_retain_commit_email():
    paths = []

    def handler(request):
        paths.append(request.url.path)
        path = request.url.path
        if path == "/repos/test/repo":
            return response(
                request,
                {
                    "default_branch": "main",
                    "description": "Service",
                    "updated_at": "2026-01-01T00:00:00Z",
                    "topics": [],
                },
            )
        if path.endswith("/readme"):
            return response(
                request,
                {
                    "content": base64.b64encode(b"# Project\nArchitecture uses PostgreSQL.").decode(),
                    "path": "README.md",
                },
            )
        if "/git/trees/" in path:
            return response(
                request, {"tree": [{"type": "blob", "path": "docs/deploy.md"}], "truncated": False}
            )
        if "/contents/" in path:
            return response(
                request,
                {"content": base64.b64encode(b"# Deploy\nUse staging approval.").decode(), "size": 30},
            )
        if path.endswith("/commits"):
            return response(
                request,
                [
                    {
                        "sha": "abc123",
                        "author": {"login": "example-contributor"},
                        "commit": {
                            "message": "Improve deployment",
                            "author": {"email": "private@example.com"},
                            "committer": {"date": "2026-01-01T00:00:00Z"},
                        },
                    }
                ],
            )
        if path.endswith("/pulls"):
            return response(
                request,
                [
                    {
                        "number": 1,
                        "title": "Deployment",
                        "body": "Staging approval required",
                        "user": {"login": "example-contributor"},
                        "state": "closed",
                    }
                ],
            )
        if path.endswith("/issues"):
            return response(
                request,
                [
                    {
                        "number": 2,
                        "title": "Recovery undocumented",
                        "body": "Add recovery procedure",
                        "state": "open",
                    }
                ],
            )
        if path.endswith("/releases"):
            return response(request, [{"tag_name": "v1", "body": "First release"}])
        return response(request, {}, 404)

    with GitHubConnector("test/repo", transport=httpx.MockTransport(handler)) as connector:
        snapshot = connector.fetch()
    assert {x.kind for x in snapshot.documents} == {
        "repository",
        "markdown",
        "commit",
        "pull_request",
        "issue",
        "release",
    }
    assert any("/contents/docs/deploy.md" in path for path in paths)
    assert "private@example.com" not in "\n".join(document.text for document in snapshot.documents)
    assert not snapshot.partial


def test_pagination_and_budget_are_bounded_and_partial_is_explicit():
    def handler(request):
        if request.url.path.endswith("/issues"):
            page = int(request.url.params.get("page", "1"))
            return response(
                request,
                [{"number": page}],
                headers={
                    "link": f'<https://api.github.com/repos/test/repo/issues?page={page + 1}>; rel="next"'
                },
            )
        return response(request, {}, 404)

    with GitHubConnector("test/repo", request_limit=6, transport=httpx.MockTransport(handler)) as connector:
        items = connector._list("issues", max_pages=2)
        assert len(items) == 2
        assert connector.snapshot.partial
        assert connector.snapshot.requests == 2


def test_unsafe_pagination_links_never_receive_authorization():
    called = []

    def handler(request):
        called.append(str(request.url))
        return response(
            request, [{"number": 1}], headers={"link": '<https://attacker.example/steal>; rel="next"'}
        )

    with GitHubConnector(
        "test/repo", token="fake-test-token", transport=httpx.MockTransport(handler)
    ) as connector:
        with pytest.raises(ConnectorError, match="unsafe"):
            connector._list("issues")
    assert len(called) == 1 and called[0].startswith("https://api.github.com/")


@pytest.mark.parametrize(
    "status,headers,message",
    [
        (401, {}, "authorization"),
        (403, {}, "denied access"),
        (404, {}, "not found"),
        (429, {}, "rate limit"),
        (403, {"x-ratelimit-remaining": "0"}, "rate limit"),
        (302, {"location": "https://attacker.example/"}, "redirects"),
    ],
)
def test_authentication_rate_limit_and_redirect_failures_have_safe_errors(status, headers, message):
    with GitHubConnector(
        "test/repo",
        transport=httpx.MockTransport(
            lambda request: response(request, {"message": "internal or sensitive payload"}, status, headers)
        ),
    ) as connector:
        with pytest.raises(ConnectorError, match=message) as error:
            connector.fetch()
        assert "sensitive payload" not in str(error.value)


def test_server_failure_is_retried_and_capped(monkeypatch):
    calls = []
    monkeypatch.setattr("app.connectors.time.sleep", lambda delay: None)

    def handler(request):
        calls.append(request)
        return response(request, {}, 503)

    with GitHubConnector("test/repo", transport=httpx.MockTransport(handler)) as connector:
        with pytest.raises(ConnectorError):
            connector.fetch()
    assert len(calls) == 3


def test_incremental_commit_cursor_and_etag_are_sent():
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path == "/repos/test/repo":
            return response(request, {}, 304)
        if request.url.path.endswith("/commits"):
            return response(request, [])
        return response(request, {}, 404)

    with GitHubConnector(
        "test/repo", etags={"/repos/test/repo": '"version1"'}, transport=httpx.MockTransport(handler)
    ) as connector:
        snapshot = connector.fetch(since=datetime(2026, 1, 1))
    assert requests[0].headers["if-none-match"] == '"version1"'
    commit_request = next(request for request in requests if request.url.path.endswith("/commits"))
    assert commit_request.url.params["since"] == "2026-01-01T00:00:00Z"
    assert not snapshot.documents


def test_background_sync_failures_are_persisted_with_safe_job_status(workspace, monkeypatch):
    client, _, project_id = workspace
    users = client.get("/api/auth/demo-users").json()
    actor = next(user for user in users if user["role"] == "admin")
    logged_in = client.post("/api/auth/demo-login", json={"user_id": actor["id"]})
    client.headers["X-CSRF-Token"] = logged_in.json()["csrf_token"]
    connection = client.post(
        f"/api/projects/{project_id}/connections/github", json={"repository": "test/repo"}
    )
    assert connection.status_code == 201

    def fail_fetch(self, *, since=None):
        raise ConnectorError(
            "GitHub authorization expired or is invalid. Reconnect the repository.",
            status="authentication_required",
        )

    monkeypatch.setattr(GitHubConnector, "fetch", fail_fetch)
    queued = client.post(f"/api/projects/{project_id}/connections/{connection.json()['id']}/sync")
    assert queued.status_code == 202
    jobs = client.get(f"/api/projects/{project_id}/jobs").json()
    job = next(job for job in jobs if job["id"] == queued.json()["id"])
    assert job["status"] == "failed" and "authorization" in job["error"]
    connections = client.get(f"/api/projects/{project_id}/connections").json()
    assert (
        next(item for item in connections if item["id"] == connection.json()["id"])["status"]
        == "authentication_required"
    )
