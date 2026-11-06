"""Permission revalidation must govern cached evidence, not just sync status."""

import base64

import httpx
import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select

from app.config import settings
from app.connectors import GitHubConnector
from app.models import Claim, Evidence, Source


@pytest.mark.parametrize("removal", ["readme_404", "complete_tree", "file_404", "partial_tree"])
def test_definitive_file_disappearance_invalidates_cache_but_partial_trees_do_not(
    workspace, monkeypatch, removal
):
    client, factory, project_id = workspace
    users = client.get("/api/auth/demo-users").json()
    actor = next(user for user in users if user["role"] == "admin")
    login = client.post("/api/auth/demo-login", json={"user_id": actor["id"]})
    client.headers["X-CSRF-Token"] = login.json()["csrf_token"]
    original_init = GitHubConnector.__init__
    phase = {"removed": False}
    tracked_text = b"Procedure: Tracked recovery\nSystem: private-service\n1. Restore the test backup in an isolated sandbox."

    def response(request, payload, status=200, headers=None):
        if (
            headers is None
            and status == 200
            and (request.url.path.endswith("/readme") or "/contents/" in request.url.path)
        ):
            headers = {"etag": '"tracked-doc-version"'}
        return httpx.Response(status, json=payload, request=request, headers=headers or {})

    def handler(request):
        path = request.url.path
        if path == "/repos/test/repo":
            return response(request, {"default_branch": "main", "topics": []})
        if path.endswith("/readme"):
            if removal == "readme_404":
                if not phase["removed"] and request.headers.get("if-none-match"):
                    return response(request, {}, 304)
                return (
                    response(request, {}, 404)
                    if phase["removed"]
                    else response(
                        request, {"content": base64.b64encode(tracked_text).decode(), "path": "README.md"}
                    )
                )
            return response(
                request,
                {
                    "content": base64.b64encode(
                        b"# General documentation\nThis README does not contain the tracked recovery procedure."
                    ).decode(),
                    "path": "README.md",
                },
            )
        if "/git/trees/" in path:
            paths = (
                []
                if removal == "readme_404"
                or (phase["removed"] and removal in {"complete_tree", "partial_tree"})
                else [{"path": "docs/recovery.md", "type": "blob"}]
            )
            return response(
                request, {"tree": paths, "truncated": phase["removed"] and removal == "partial_tree"}
            )
        if "/contents/docs/recovery.md" in path:
            if not phase["removed"] and request.headers.get("if-none-match"):
                return response(request, {}, 304)
            return (
                response(request, {}, 404)
                if phase["removed"] and removal == "file_404"
                else response(
                    request, {"content": base64.b64encode(tracked_text).decode(), "size": len(tracked_text)}
                )
            )
        return response(request, [])

    def configured_init(self, repository, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        original_init(self, repository, **kwargs)

    monkeypatch.setattr(GitHubConnector, "__init__", configured_init)
    connection = client.post(
        f"/api/projects/{project_id}/connections/github", json={"repository": "test/repo"}
    )
    assert connection.status_code == 201
    connection_id = connection.json()["id"]
    assert client.post(f"/api/projects/{project_id}/connections/{connection_id}/sync").status_code == 202
    external_id = "github:readme" if removal == "readme_404" else "github:file:docs/recovery.md"
    with factory() as db:
        source = db.scalar(
            select(Source).where(Source.connection_id == connection_id, Source.external_id == external_id)
        )
        evidence = db.scalar(select(Evidence).where(Evidence.source_id == source.id))
        claim = db.get(Claim, evidence.claim_id)
        claim.status, claim.verified_by = "verified", actor["id"]
        db.commit()
        source_id, claim_id = source.id, claim.id
    phase["removed"] = True
    queued = client.post(f"/api/projects/{project_id}/connections/{connection_id}/sync")
    assert queued.status_code == 202
    job = next(
        job
        for job in client.get(f"/api/projects/{project_id}/jobs").json()
        if job["id"] == queued.json()["id"]
    )
    assert job["status"] == "completed"
    from app.intelligence import current_claims
    from app.models import User

    with factory() as db:
        source, claim = db.get(Source, source_id), db.get(Claim, claim_id)
        visible_claims = current_claims(db, db.get(User, actor["id"]), project_id)
        if removal == "partial_tree":
            assert source.status == "ready" and claim.status == "verified"
            assert claim.id in {item.id for item in visible_claims}
            assert job["stats"]["partial"]
            assert job["stats"]["source_removals"]["sources_unavailable"] == 0
        else:
            assert source.status == "unavailable" and claim.status == "invalidated"
            assert source.source_metadata["source_unavailable_reason"] == "original_source_removed"
            assert claim.id not in {item.id for item in visible_claims}
            assert job["stats"]["source_removals"]["sources_unavailable"] == 1
    if removal != "partial_tree":
        phase["removed"] = False
        assert client.post(f"/api/projects/{project_id}/connections/{connection_id}/sync").status_code == 202
        with factory() as db:
            source = db.get(Source, source_id)
            assert source.status == "ready" and source.version == 2
            evidence = list(
                db.scalars(
                    select(Evidence).where(Evidence.source_id == source.id, Evidence.source_version == 2)
                )
            )
            assert evidence and all(db.get(Claim, item.claim_id).status == "pending" for item in evidence)


@pytest.mark.parametrize(
    "failure_status,failure_headers,failure_message,permission_lost",
    [
        (401, {}, "Invalid authorization", True),
        (403, {}, "Repository permission denied", True),
        (404, {}, "Repository not found", True),
        (429, {}, "Rate limited", False),
        (403, {"x-ratelimit-remaining": "0"}, "API rate limit exceeded", False),
        (403, {"x-ratelimit-remaining": "20"}, "You have exceeded a secondary rate limit", False),
        (403, {"retry-after": "60"}, "Secondary throttling", False),
        (503, {}, "Temporary outage", False),
        ("network", {}, "Offline", False),
    ],
)
def test_permission_loss_invalidates_cached_knowledge_but_transient_failures_preserve_it(
    workspace,
    monkeypatch,
    failure_status,
    failure_headers,
    failure_message,
    permission_lost,
):
    client, factory, project_id = workspace
    users = client.get("/api/auth/demo-users").json()
    actor = next(user for user in users if user["role"] == "admin")
    logged_in = client.post("/api/auth/demo-login", json={"user_id": actor["id"]})
    client.headers["X-CSRF-Token"] = logged_in.json()["csrf_token"]
    monkeypatch.setattr(settings, "token_encryption_key", Fernet.generate_key().decode())
    monkeypatch.setattr("app.connectors.time.sleep", lambda delay: None)
    phase = {"fail": False}
    original_init = GitHubConnector.__init__

    def response(request, payload, status=200, headers=None):
        return httpx.Response(status, json=payload, headers=headers or {}, request=request)

    def handler(request):
        if phase["fail"]:
            if failure_status == "network":
                raise httpx.ConnectError("Test network failure", request=request)
            return response(request, {"message": failure_message}, failure_status, failure_headers)
        path = request.url.path
        if path == "/repos/test/repo":
            return response(
                request,
                {"default_branch": "main", "description": "Private test repository", "topics": []},
                headers={"etag": '"repo-version"'},
            )
        if path.endswith("/readme"):
            text = b"Procedure: Permitted recovery\nSystem: private-service\n1. Restore a test backup in an isolated sandbox."
            return response(
                request,
                {"content": base64.b64encode(text).decode(), "path": "README.md"},
                headers={"etag": '"readme-version"'},
            )
        if "/git/trees/" in path:
            return response(request, {"tree": [], "truncated": False})
        return response(request, [])

    def configured_init(self, repository, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        original_init(self, repository, **kwargs)

    monkeypatch.setattr(GitHubConnector, "__init__", configured_init)
    connection = client.post(
        f"/api/projects/{project_id}/connections/github",
        json={"repository": "test/repo", "token": "synthetic-test-authorization"},
    )
    assert connection.status_code == 201
    connection_id = connection.json()["id"]
    assert client.post(f"/api/projects/{project_id}/connections/{connection_id}/sync").status_code == 202
    with factory() as db:
        source = db.scalar(
            select(Source).where(Source.connection_id == connection_id, Source.external_id == "github:readme")
        )
        evidence = db.scalar(select(Evidence).where(Evidence.source_id == source.id))
        claim = db.get(Claim, evidence.claim_id)
        claim.status = "verified"
        claim.verified_by = actor["id"]
        db.commit()
        source_id, claim_id = source.id, claim.id
    before = client.post(f"/api/projects/{project_id}/successor/ask", json={"question": "Permitted recovery"})
    assert before.status_code == 200 and before.json()["known"]
    phase["fail"] = True
    queued = client.post(f"/api/projects/{project_id}/connections/{connection_id}/sync")
    assert queued.status_code == 202
    jobs = client.get(f"/api/projects/{project_id}/jobs").json()
    job = next(item for item in jobs if item["id"] == queued.json()["id"])
    assert job["status"] == "failed"
    after = client.post(f"/api/projects/{project_id}/successor/ask", json={"question": "Permitted recovery"})
    assert after.status_code == 200
    with factory() as db:
        source, claim = db.get(Source, source_id), db.get(Claim, claim_id)
        if permission_lost:
            assert source.status == "unavailable" and source.source_metadata["revoked_by_permission_loss"]
            assert claim.status == "invalidated"
            assert job["stats"]["permission_lost"]
            assert not after.json()["known"] and not after.json()["citations"]
        else:
            assert source.status == "ready" and claim.status == "verified"
            assert not job["stats"].get("permission_lost")
            assert after.json()["known"]
    if permission_lost:
        # Reauthorization permits source revalidation, never automatic approval
        # of a previously invalidated responsibility/procedure.
        phase["fail"] = False
        assert client.post(f"/api/projects/{project_id}/connections/{connection_id}/sync").status_code == 202
        with factory() as db:
            source = db.get(Source, source_id)
            assert source.status == "ready" and source.version == 2
            assert not source.source_metadata.get("revoked_by_permission_loss")
            evidence = list(
                db.scalars(
                    select(Evidence).where(Evidence.source_id == source.id, Evidence.source_version == 2)
                )
            )
            assert evidence and all(db.get(Claim, item.claim_id).status == "pending" for item in evidence)
        after_revalidation = client.post(
            f"/api/projects/{project_id}/successor/ask", json={"question": "Permitted recovery"}
        )
        assert not after_revalidation.json()["known"]
