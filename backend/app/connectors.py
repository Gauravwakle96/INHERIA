"""Functional GitHub REST adapter with bounded requests and safe token handling."""

from __future__ import annotations

import base64
import hashlib
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import unquote, urlencode, urlparse

import httpx
from cryptography.fernet import Fernet, InvalidToken

from app.ingestion import DocumentError, ingest_parsed, invalidate_source, parse_text, utcnow

GITHUB_API = "https://api.github.com"
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9_.-]{1,100}$")


class ConnectorError(ValueError):
    def __init__(self, message: str, *, status: str = "sync_failed", permission_lost: bool = False) -> None:
        super().__init__(message)
        self.status = status
        self.permission_lost = permission_lost


@dataclass
class GitHubDocument:
    external_id: str
    name: str
    kind: str
    text: str
    url: str
    timestamp: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GitHubSnapshot:
    documents: list[GitHubDocument] = field(default_factory=list)
    etags: dict[str, str] = field(default_factory=dict)
    partial: bool = False
    warnings: list[str] = field(default_factory=list)
    requests: int = 0
    deleted_file_ids: list[str] = field(default_factory=list)


def validate_repository(repository: str) -> str:
    repository = repository.strip()
    if repository.startswith("https://github.com/"):
        repository = repository.removeprefix("https://github.com/").rstrip("/")
        if repository.endswith(".git"):
            repository = repository[:-4]
    if not REPOSITORY_PATTERN.fullmatch(repository) or ".." in repository.split("/"):
        raise ConnectorError("Enter a GitHub repository as owner/name or its HTTPS GitHub URL.")
    return repository


def encrypt_token(token: str, encryption_key: str) -> str:
    if not token:
        return ""
    if not encryption_key:
        raise ConnectorError(
            "Private repository tokens require INHERIA_TOKEN_ENCRYPTION_KEY on the server.",
            status="authentication_required",
        )
    try:
        return Fernet(encryption_key.encode()).encrypt(token.encode()).decode()
    except (ValueError, TypeError):
        raise ConnectorError(
            "The server token encryption key is invalid.", status="authentication_required"
        ) from None


def decrypt_token(encrypted: str | None, encryption_key: str) -> str:
    if not encrypted:
        return ""
    try:
        return Fernet(encryption_key.encode()).decrypt(encrypted.encode()).decode()
    except (ValueError, TypeError, InvalidToken):
        raise ConnectorError(
            "Stored authorization cannot be decrypted. Reconnect this repository.",
            status="authentication_required",
        ) from None


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


class GitHubConnector:
    def __init__(
        self,
        repository: str,
        *,
        token: str = "",
        request_limit: int = 30,
        etags: dict[str, str] | None = None,
        known_file_ids: list[str] | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.repository = validate_repository(repository)
        self.request_limit = max(6, min(request_limit, 100))
        self.etags = dict(etags or {})
        self.known_file_ids = set(known_file_ids or [])
        self.snapshot = GitHubSnapshot(etags=dict(self.etags))
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "INHERIA-knowledge-continuity/0.1",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.Client(
            base_url=GITHUB_API, headers=headers, timeout=20, follow_redirects=False, transport=transport
        )

    def __enter__(self) -> GitHubConnector:
        return self

    def __exit__(self, *args: Any) -> None:
        self.client.close()

    def _url(self, path: str) -> str:
        if path.startswith("https://"):
            parsed = urlparse(path)
            if (
                parsed.scheme != "https"
                or parsed.netloc != "api.github.com"
                or parsed.username
                or parsed.password
            ):
                raise ConnectorError("GitHub returned an unsafe pagination URL.")
            return path
        if not path.startswith("/repos/") or ".." in path.split("/"):
            raise ConnectorError("Unsupported GitHub API path.")
        return path

    def _get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        conditional: bool = False,
        optional: bool = False,
    ) -> httpx.Response | None:
        url = self._url(path)
        cache_key = path + ("?" + urlencode(params or {}) if params else "")
        headers = {"If-None-Match": self.etags[cache_key]} if conditional and cache_key in self.etags else {}
        for attempt in range(3):
            if self.snapshot.requests >= self.request_limit:
                self.snapshot.partial = True
                self.snapshot.warnings.append("Request budget reached; this is a partial snapshot.")
                return None
            self.snapshot.requests += 1
            try:
                response = self.client.get(url, params=params, headers=headers)
            except httpx.RequestError:
                if attempt == 2:
                    raise ConnectorError(
                        "GitHub could not be reached. Retry synchronization later."
                    ) from None
                time.sleep(0.2 * (attempt + 1))
                continue
            if response.status_code == 304:
                return None
            if response.status_code in (301, 302, 307, 308):
                raise ConnectorError("The repository redirects. Reconnect using its current owner/name.")
            if response.status_code == 401:
                raise ConnectorError(
                    "GitHub authorization expired or is invalid. Reconnect the repository.",
                    status="authentication_required",
                    permission_lost=True,
                )
            if response.status_code == 429 or (
                response.status_code == 403
                and (
                    response.headers.get("x-ratelimit-remaining") == "0"
                    or bool(response.headers.get("retry-after"))
                    or b"secondary rate limit" in response.content.lower()
                    or b"api rate limit exceeded" in response.content.lower()
                )
            ):
                raise ConnectorError("GitHub rate limit reached. Retry after the rate-limit reset.")
            if response.status_code == 403:
                raise ConnectorError(
                    "GitHub denied access. Check repository selection and token permissions.",
                    status="authentication_required",
                    permission_lost=True,
                )
            if response.status_code == 404:
                if optional:
                    root = f"/repos/{self.repository}"
                    if path == root + "/readme":
                        self.snapshot.deleted_file_ids.append("github:readme")
                    elif path.startswith(root + "/contents/"):
                        file_path = unquote(path.removeprefix(root + "/contents/"))
                        self.snapshot.deleted_file_ids.append("github:file:" + file_path)
                    return None
                raise ConnectorError(
                    "Repository not found or not authorized. Check its name and access.",
                    status="authentication_required",
                    permission_lost=True,
                )
            if response.status_code >= 500 and attempt < 2:
                time.sleep(0.2 * (attempt + 1))
                continue
            if response.status_code >= 400:
                raise ConnectorError(
                    "GitHub rejected the synchronization request. Check the integration and retry."
                )
            if len(response.content) > 8 * 1024 * 1024:
                raise ConnectorError("GitHub returned a response beyond the safe processing limit.")
            if conditional and response.headers.get("etag"):
                self.snapshot.etags[cache_key] = response.headers["etag"]
            return response
        raise ConnectorError("GitHub could not complete synchronization.")

    def _json(self, response: httpx.Response | None) -> Any:
        if response is None:
            return None
        try:
            return response.json()
        except ValueError:
            raise ConnectorError("GitHub returned an invalid API response.") from None

    def _list(
        self,
        suffix: str,
        *,
        params: dict[str, Any] | None = None,
        max_pages: int = 2,
        since: datetime | None = None,
    ) -> list[dict[str, Any]]:
        path = f"/repos/{self.repository}/{suffix}"
        query = {"per_page": 100, **(params or {})}
        collected: list[dict[str, Any]] = []
        for page in range(max_pages):
            response = self._get(path, params=query if page == 0 else None, optional=True)
            payload = self._json(response)
            if payload is None:
                break
            if not isinstance(payload, list):
                raise ConnectorError("GitHub returned an unexpected list response.")
            stop = False
            for item in payload:
                if not isinstance(item, dict):
                    continue
                updated = parse_timestamp(item.get("updated_at"))
                if since is not None and updated is not None and updated < since:
                    stop = True
                    break
                collected.append(item)
            next_url = response.links.get("next", {}).get("url") if response is not None else None
            if stop or not next_url:
                break
            if page == max_pages - 1:
                self.snapshot.partial = True
                self.snapshot.warnings.append(f"{suffix} pagination capped at {max_pages} pages.")
                break
            path = self._url(next_url)
        return collected

    def fetch(self, *, since: datetime | None = None) -> GitHubSnapshot:
        root = f"/repos/{self.repository}"
        repo = self._json(self._get(root, conditional=True))
        default_branch = "HEAD"
        if repo is not None:
            if not isinstance(repo, dict):
                raise ConnectorError("GitHub repository metadata is invalid.")
            default_branch = repo.get("default_branch") or "HEAD"
            self.snapshot.documents.append(
                GitHubDocument(
                    "github:repository",
                    f"{self.repository} · repository",
                    "repository",
                    f"# Repository {self.repository}\nDescription: {repo.get('description') or 'Not documented'}\n"
                    f"Default branch: {default_branch}\nLanguage: {repo.get('language') or 'Unknown'}\n"
                    f"Archived: {bool(repo.get('archived'))}\nOpen issues: {repo.get('open_issues_count', 0)}\n"
                    f"Topics: {', '.join(repo.get('topics') or [])}",
                    f"https://github.com/{self.repository}",
                    parse_timestamp(repo.get("updated_at")),
                    {"repository": self.repository},
                )
            )
        readme = self._json(self._get(root + "/readme", conditional=True, optional=True))
        if isinstance(readme, dict) and readme.get("content"):
            try:
                readme_text = base64.b64decode(readme["content"], validate=False).decode("utf-8-sig")
            except (ValueError, UnicodeDecodeError):
                readme_text = ""
            if readme_text:
                self.snapshot.documents.append(
                    GitHubDocument(
                        "github:readme",
                        f"{self.repository} · README",
                        "markdown",
                        readme_text,
                        f"https://github.com/{self.repository}/blob/{default_branch}/{readme.get('path', 'README.md')}",
                        metadata={"repository": self.repository},
                    )
                )
        tree = self._json(
            self._get(
                root + f"/git/trees/{default_branch}",
                params={"recursive": 1},
                conditional=True,
                optional=True,
            )
        )
        if isinstance(tree, dict):
            items = [item for item in (tree.get("tree") or []) if isinstance(item, dict)]
            paths = [str(item.get("path", "")) for item in items if item.get("type") == "blob"]
            # GitHub must explicitly attest completeness. An omitted flag or a
            # malformed tree cannot establish that an existing file disappeared.
            complete_tree = tree.get("truncated") is False and isinstance(tree.get("tree"), list)
            if complete_tree and len(paths) <= 1500:
                present_ids = {"github:file:" + path for path in paths}
                self.snapshot.deleted_file_ids.extend(
                    sorted(
                        file_id
                        for file_id in self.known_file_ids
                        if file_id.startswith("github:file:") and file_id not in present_ids
                    )
                )
            if tree.get("truncated") or len(paths) > 1500:
                self.snapshot.partial = True
                self.snapshot.warnings.append(
                    "Repository structure is truncated; absent files cannot be inferred as missing."
                )
            self.snapshot.documents.append(
                GitHubDocument(
                    "github:structure",
                    f"{self.repository} · repository structure",
                    "repository",
                    "# Repository structure\n" + "\n".join(paths[:1500]),
                    f"https://github.com/{self.repository}/tree/{default_branch}",
                    metadata={
                        "repository": self.repository,
                        "truncated": bool(tree.get("truncated") or len(paths) > 1500),
                    },
                )
            )
            document_paths = [
                path
                for path in paths
                if path.lower().endswith((".md", ".txt"))
                and path.lower() != "readme.md"
                and not any(
                    part in path.lower().split("/") for part in ("node_modules", "vendor", "test", "tests")
                )
            ]
            for path in document_paths[:5]:
                # Encode individual path segments while retaining the fixed API host.
                encoded_path = "/".join(httpx.URL(path=part).raw_path.decode() for part in path.split("/"))
                body = self._json(
                    self._get(root + "/contents/" + encoded_path, conditional=True, optional=True)
                )
                if not isinstance(body, dict) or not body.get("content") or body.get("size", 0) > 1024 * 1024:
                    continue
                try:
                    doc_text = base64.b64decode(body["content"]).decode("utf-8-sig")
                except (ValueError, UnicodeDecodeError):
                    continue
                self.snapshot.documents.append(
                    GitHubDocument(
                        f"github:file:{path}",
                        f"{self.repository} · {path}",
                        "markdown",
                        doc_text,
                        f"https://github.com/{self.repository}/blob/{default_branch}/{path}",
                        metadata={"repository": self.repository, "paths": [path]},
                    )
                )
        commit_params: dict[str, Any] = {}
        if since:
            commit_params["since"] = since.isoformat() + "Z"
        for commit in self._list("commits", params=commit_params):
            info = commit.get("commit") or {}
            sha = str(commit.get("sha", ""))
            if not sha:
                continue
            author = (commit.get("author") or {}).get("login") or "Unknown GitHub contributor"
            timestamp = parse_timestamp((info.get("committer") or {}).get("date"))
            self.snapshot.documents.append(
                GitHubDocument(
                    f"github:commit:{sha}",
                    f"{self.repository} · commit {sha[:8]}",
                    "commit",
                    f"# Commit {sha}\nGitHub contributor: {author}\nMessage: {info.get('message') or ''}\n"
                    "Contributor activity is a candidate signal; it does not prove ownership or expertise.",
                    f"https://github.com/{self.repository}/commit/{sha}",
                    timestamp,
                    {"repository": self.repository, "author_login": author},
                )
            )
        pull_requests = self._list(
            "pulls", params={"state": "all", "sort": "updated", "direction": "desc"}, since=since
        )
        for pull in pull_requests:
            number = pull.get("number")
            author = (pull.get("user") or {}).get("login") or "Unknown GitHub contributor"
            labels = [str(x.get("name", "")) for x in (pull.get("labels") or []) if isinstance(x, dict)]
            self.snapshot.documents.append(
                GitHubDocument(
                    f"github:pull:{number}",
                    f"{self.repository} · PR #{number}",
                    "pull_request",
                    f"# Pull request #{number}: {pull.get('title') or ''}\nGitHub contributor: {author}\n"
                    f"State: {pull.get('state') or 'unknown'}\nLabels: {', '.join(labels)}\n"
                    f"Description:\n{pull.get('body') or 'No description recorded.'}",
                    f"https://github.com/{self.repository}/pull/{number}",
                    parse_timestamp(pull.get("updated_at")),
                    {
                        "repository": self.repository,
                        "number": number,
                        "state": pull.get("state"),
                        "labels": labels,
                        "author_login": author,
                    },
                )
            )
        issue_params: dict[str, Any] = {"state": "all", "sort": "updated", "direction": "desc"}
        if since:
            issue_params["since"] = since.isoformat() + "Z"
        for issue in self._list("issues", params=issue_params):
            if issue.get("pull_request"):
                continue
            number = issue.get("number")
            labels = [str(x.get("name", "")) for x in (issue.get("labels") or []) if isinstance(x, dict)]
            assignees = [
                (x or {}).get("login", "") for x in (issue.get("assignees") or []) if isinstance(x, dict)
            ]
            self.snapshot.documents.append(
                GitHubDocument(
                    f"github:issue:{number}",
                    f"{self.repository} · issue #{number}",
                    "issue",
                    f"# Issue #{number}: {issue.get('title') or ''}\nState: {issue.get('state') or 'unknown'}\n"
                    f"Assignees: {', '.join(assignees) or 'Unassigned'}\nLabels: {', '.join(labels)}\n"
                    f"Description:\n{issue.get('body') or 'No description recorded.'}",
                    f"https://github.com/{self.repository}/issues/{number}",
                    parse_timestamp(issue.get("updated_at")),
                    {
                        "repository": self.repository,
                        "number": number,
                        "state": issue.get("state"),
                        "labels": labels,
                    },
                )
            )
        for release in self._list("releases", max_pages=1):
            tag = release.get("tag_name") or str(release.get("id", ""))
            self.snapshot.documents.append(
                GitHubDocument(
                    f"github:release:{tag}",
                    f"{self.repository} · release {tag}",
                    "release",
                    f"# Release {tag}\nPrerelease: {bool(release.get('prerelease'))}\nNotes:\n{release.get('body') or 'No release notes recorded.'}",
                    f"https://github.com/{self.repository}/releases/tag/{tag}",
                    parse_timestamp(release.get("published_at")),
                    {"repository": self.repository},
                )
            )
        return self.snapshot


def serialize_connection(connection: Any) -> dict[str, Any]:
    return {
        "id": connection.id,
        "name": connection.name,
        "provider": connection.provider,
        "repository": connection.repository,
        "status": connection.status,
        "last_sync_at": connection.last_sync_at,
        "has_token": bool(connection.encrypted_token),
    }


def serialize_job(job: Any) -> dict[str, Any]:
    return {
        "id": job.id,
        "kind": job.kind,
        "status": job.status,
        "error": job.error,
        "stats": job.stats or {},
        "created_at": job.created_at,
        "finished_at": job.finished_at,
    }


def _mark_sources_unavailable(db, connection, *, reason: str, external_ids: list[str]) -> dict[str, int]:
    """Definitive source removal invalidates evidence and preserves its history."""
    from sqlalchemy import select

    from app.models import Claim, Evidence, Source

    sources = list(
        db.scalars(
            select(Source).where(
                Source.connection_id == connection.id,
                Source.external_id.in_(external_ids),
                Source.status.in_(["ready", "unavailable"]),
            )
        )
    )
    claim_ids = set()
    for source in sources:
        refs = set(db.scalars(select(Evidence.claim_id).where(Evidence.source_id == source.id)))
        if refs:
            claim_ids.update(
                db.scalars(select(Claim.id).where(Claim.id.in_(refs), Claim.status != "invalidated"))
            )
        invalidate_source(db, source)
        source.status = "unavailable"
        source.source_metadata = {
            **(source.source_metadata or {}),
            "source_unavailable_reason": reason,
            "source_unavailable_at": utcnow().isoformat(),
        }
    return {"sources_unavailable": len(sources), "claims_invalidated": len(claim_ids)}


def run_sync_job(job_id: str) -> None:
    from sqlalchemy import select

    from app.config import settings
    from app.database import SessionLocal
    from app.models import Connection, Job, Source, User
    from app.security import audit, project_access

    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if job is None or job.status != "queued":
            return
        connection = db.get(Connection, job.connection_id)
        user = db.get(User, job.requested_by)
        if connection is None or user is None or not user.active or connection.status == "revoked":
            job.status = "failed"
            job.error = "The source connection is no longer available."
            job.finished_at = utcnow()
            db.commit()
            return
        try:
            project_access(db, user, job.project_id, write=True)
            job.status = "running"
            job.started_at = utcnow()
            job.attempts = (job.attempts or 0) + 1
            connection.status = "syncing"
            db.commit()
            token = decrypt_token(connection.encrypted_token, settings.token_encryption_key)
            config = dict(connection.config or {})
            known_file_ids = list(
                db.scalars(
                    select(Source.external_id).where(
                        Source.connection_id == connection.id,
                        Source.status.in_(["ready", "unavailable"]),
                        Source.external_id.is_not(None),
                    )
                )
            )
            with GitHubConnector(
                connection.repository,
                token=token,
                request_limit=settings.github_request_limit,
                etags=config.get("etags"),
                known_file_ids=known_file_ids,
            ) as connector:
                snapshot = connector.fetch(since=connection.last_sync_at)
            removed = _mark_sources_unavailable(
                db,
                connection,
                reason="original_source_removed",
                external_ids=list(set(snapshot.deleted_file_ids)),
            )
            if removed["sources_unavailable"]:
                # A recreated file with the same body may keep its old ETag.
                # Force a fresh body before restoring availability and review.
                snapshot.etags = {}
                audit(
                    db,
                    user,
                    job.project_id,
                    "integration.sources_removed",
                    "connection",
                    connection.id,
                    removed,
                )
                db.commit()
            imported = duplicates = quarantined = 0
            for document in snapshot.documents:
                # Re-check revocation and actor authorization between each item.
                db.refresh(connection)
                if connection.status == "revoked":
                    raise ConnectorError("The integration was revoked while synchronizing.", status="revoked")
                project_access(db, user, job.project_id, write=True)
                try:
                    parsed = parse_text(document.text, kind=document.kind, metadata=document.metadata)
                    _, duplicate = ingest_parsed(
                        db,
                        user,
                        job.project_id,
                        name=document.name,
                        kind=document.kind,
                        parsed=parsed,
                        checksum=hashlib.sha256(document.text.encode()).hexdigest(),
                        connection_id=connection.id,
                        external_id=document.external_id,
                        url=document.url,
                        source_time=document.timestamp,
                        synthetic=False,
                    )
                    duplicates += int(duplicate)
                    imported += int(not duplicate)
                    quarantined += int(parsed.quarantined)
                    db.commit()
                except DocumentError:
                    snapshot.partial = True
                    snapshot.warnings.append("A source could not be parsed and was excluded.")
            config["etags"] = snapshot.etags
            config["last_warnings"] = list(dict.fromkeys(snapshot.warnings))
            config.pop("permission_lost", None)
            connection.config = config
            connection.status = "partial" if snapshot.partial else "connected"
            # Partial history must be retried without advancing the incremental cursor.
            if not snapshot.partial:
                connection.last_sync_at = utcnow()
            job.status = "completed"
            job.finished_at = utcnow()
            job.stats = {
                "imported": imported,
                "duplicates": duplicates,
                "quarantined": quarantined,
                "requests": snapshot.requests,
                "partial": snapshot.partial,
                "warnings": list(dict.fromkeys(snapshot.warnings)),
                "source_removals": removed,
            }
            audit(db, user, job.project_id, "integration.synced", "connection", connection.id, job.stats)
            db.commit()
            try:
                from app.intelligence import reconstruct_project

                reconstruct_project(db, user, job.project_id)
                db.commit()
            except ImportError:
                pass
            except Exception:
                db.rollback()
                job = db.get(Job, job_id)
                job.stats = {
                    **(job.stats or {}),
                    "analysis_status": "failed",
                    "analysis_error": "Sources synchronized; reconstruction can be retried from Investigation.",
                }
                db.commit()
        except Exception as exc:
            db.rollback()
            job = db.get(Job, job_id)
            connection = db.get(Connection, job.connection_id) if job else None
            if job:
                job.status = "failed"
                job.error = (
                    str(exc)
                    if isinstance(exc, ConnectorError)
                    else "Synchronization failed safely. Check integration access and retry."
                )
                job.finished_at = utcnow()
            if connection and connection.status != "revoked":
                connection.status = exc.status if isinstance(exc, ConnectorError) else "sync_failed"
                if isinstance(exc, ConnectorError) and exc.permission_lost:
                    invalidated = 0
                    sources = list(db.scalars(select(Source).where(Source.connection_id == connection.id)))
                    affected = 0
                    for source in sources:
                        if source.status in {"revoked", "quarantined"}:
                            continue  # Explicit exclusions remain revoked after a later reconnection.
                        invalidated += invalidate_source(db, source)
                        source.status = "unavailable"
                        source.source_metadata = {
                            **(source.source_metadata or {}),
                            "revoked_by_permission_loss": True,
                            "permission_loss_at": utcnow().isoformat(),
                        }
                        affected += 1
                    # A renewed connection must fetch fresh bodies, rather than
                    # reusing ETags or advancing from an inaccessible history.
                    connection.config = {**(connection.config or {}), "etags": {}, "permission_lost": True}
                    connection.last_sync_at = None
                    if job:
                        job.stats = {
                            **(job.stats or {}),
                            "permission_lost": True,
                            "sources_unavailable": affected,
                            "claims_invalidated": invalidated,
                        }
                    audit(
                        db,
                        user,
                        job.project_id,
                        "integration.permission_lost",
                        "connection",
                        connection.id,
                        {"sources_unavailable": affected, "claims_invalidated": invalidated},
                    )
            db.commit()
