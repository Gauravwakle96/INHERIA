"""Bounded document parsing, privacy filtering and source version management.

Raw files are processed in memory and never persisted. Secret-bearing files are
quarantined without storing their extracted content. PyMuPDF is AGPL/commercial;
see the project dependency licensing notes before proprietary deployment.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import PurePath
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models import Source, User

MAX_TEXT_CHARS = 100_000
MAX_CHUNKS = 200
CHUNK_CHARS = 2_000
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".md", ".markdown", ".txt", ".json"}


class DocumentError(ValueError):
    """A safe, user-readable document error with no uploaded content."""


@dataclass(frozen=True)
class Segment:
    locator: str
    text: str


@dataclass
class ParsedDocument:
    segments: list[Segment]
    metadata: dict[str, Any] = field(default_factory=dict)
    quarantined: bool = False
    detected_types: list[str] = field(default_factory=list)
    redacted_count: int = 0


SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "api_key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "aws_access_key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "slack_token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "bearer_token": re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{24,}=*", re.I),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    "credential_url": re.compile(
        r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s:/]+:[^\s@]+@", re.I
    ),
    "assigned_secret": re.compile(
        r"(?:password|passwd|api[_ -]?key|access[_ -]?token|client[_ -]?secret|secret[_ -]?key)"
        r"[\"']?\s*[=:]\s*[\"']?([^\s\"',;]{6,})",
        re.I,
    ),
}
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+\d{1,3}[ -]?)?(?:\(\d{3}\)[ -]?\d{3}[ -]\d{4}|\+\d[\d -]{9,16}\d)(?!\w)"
)
PLACEHOLDER = re.compile(
    r"^(?:\$\{|\{\{|\$(?:env:)?[A-Z_][A-Z0-9_]*$|%[A-Z_][A-Z0-9_]*%$|<|"
    r"your[_-]|example|changeme|placeholder|\[redacted\]|redacted|none|null|\*+|x{6,})",
    re.I,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def privacy_filter(text: str) -> tuple[str, list[str], int]:
    """Return redacted text or an empty string if any likely secret is found."""
    detected: set[str] = set()
    for kind, pattern in SECRET_PATTERNS.items():
        for match in pattern.finditer(text):
            if kind == "assigned_secret" and PLACEHOLDER.match(match.group(1)):
                continue
            detected.add(kind)
    if detected:
        return "", sorted(detected), 0
    count = 0

    def email_redact(match: re.Match[str]) -> str:
        nonlocal count
        # Reserved .example identities are deliberately synthetic demo data.
        if match.group(0).lower().endswith((".example", ".invalid", ".test")):
            return match.group(0)
        count += 1
        return "[email redacted]"

    cleaned = EMAIL_PATTERN.sub(email_redact, text)
    cleaned, phone_count = PHONE_PATTERN.subn("[phone redacted]", cleaned)
    count += phone_count
    return cleaned, (["pii_redacted"] if count else []), count


def safe_name(name: str) -> str:
    filename = PurePath(name.replace("\\", "/")).name[:240] or "Untitled source"
    clean, types, _ = privacy_filter(filename)
    return clean if clean and not set(types).difference({"pii_redacted"}) else "Quarantined source"


def safe_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Metadata can contain secrets too; redact values before any persistence."""

    def clean(value: Any, depth: int = 0) -> Any:
        if depth > 5:
            return "[metadata depth exceeded]"
        if isinstance(value, str):
            filtered, detected, _ = privacy_filter(value)
            return filtered[:1000] if filtered else ("[sensitive metadata removed]" if detected else "")
        if isinstance(value, list):
            return [clean(item, depth + 1) for item in value[:200]]
        if isinstance(value, dict):
            return {
                safe_name(str(key))[:100]: clean(item, depth + 1) for key, item in list(value.items())[:100]
            }
        if value is None or isinstance(value, (int, float, bool)):
            return value
        return None

    return clean(metadata)


def _bound_segments(segments: list[Segment], metadata: dict[str, Any]) -> list[Segment]:
    result: list[Segment] = []
    used = 0
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        remaining = MAX_TEXT_CHARS - used
        if remaining <= 0 or len(result) >= MAX_CHUNKS:
            metadata["truncated"] = True
            break
        if len(text) > remaining:
            text = text[:remaining]
            metadata["truncated"] = True
        for start in range(0, len(text), CHUNK_CHARS):
            if len(result) >= MAX_CHUNKS:
                metadata["truncated"] = True
                break
            part = text[start : start + CHUNK_CHARS]
            locator = segment.locator
            if len(text) > CHUNK_CHARS:
                locator += f" · part {start // CHUNK_CHARS + 1}"
            result.append(Segment(locator[:250], part))
            used += len(part)
    metadata["extracted_characters"] = used
    return result


def parse_text(text: str, *, kind: str = "txt", metadata: dict[str, Any] | None = None) -> ParsedDocument:
    meta = safe_metadata(dict(metadata or {}))
    meta["format"] = kind
    # Privacy scans cover the whole input, including content beyond indexing cap.
    cleaned, detected, redactions = privacy_filter(text)
    if not cleaned and detected:
        meta.update({"detected_types": detected, "stored_content": False})
        return ParsedDocument([], meta, True, detected, redactions)
    segments: list[Segment] = []
    lines = cleaned.splitlines()
    heading = "Document"
    buffer: list[str] = []
    start_line = 1
    for number, line in enumerate(lines, 1):
        if re.match(r"^#{1,6}\s+", line):
            if buffer:
                segments.append(Segment(f"{heading} · lines {start_line}–{number - 1}", "\n".join(buffer)))
            heading = re.sub(r"^#{1,6}\s+", "", line).strip()[:150]
            buffer = [line]
            start_line = number
        else:
            buffer.append(line)
        if len(buffer) >= 35:
            segments.append(Segment(f"{heading} · lines {start_line}–{number}", "\n".join(buffer)))
            buffer = []
            start_line = number + 1
    if buffer:
        segments.append(Segment(f"{heading} · lines {start_line}–{len(lines)}", "\n".join(buffer)))
    if not any(s.text.strip() for s in segments):
        raise DocumentError("The document contains no readable text.")
    meta.update({"line_count": len(lines), "redacted_count": redactions, "detected_types": detected})
    return ParsedDocument(_bound_segments(segments, meta), meta, False, detected, redactions)


def _json_segments(value: Any, path: str = "$", depth: int = 0) -> list[Segment]:
    if depth > 40:
        raise DocumentError("JSON nesting exceeds the supported depth of 40.")
    if isinstance(value, dict):
        results = []
        for key, child in value.items():
            results.extend(_json_segments(child, f"{path}.{str(key)[:150]}", depth + 1))
            if len(results) > MAX_CHUNKS * 5:
                break
        return results
    if isinstance(value, list):
        results = []
        for index, child in enumerate(value[:1000]):
            results.extend(_json_segments(child, f"{path}[{index}]", depth + 1))
            if len(results) > MAX_CHUNKS * 5:
                break
        return results
    return [Segment(path, f"{path}: {json.dumps(value, ensure_ascii=False)}")]


def parse_document(filename: str, content: bytes, *, max_bytes: int = 10 * 1024 * 1024) -> ParsedDocument:
    extension = PurePath(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise DocumentError("Supported file formats are PDF, DOCX, Markdown, TXT and JSON.")
    if not content:
        raise DocumentError("The uploaded file is empty.")
    if len(content) > max_bytes:
        raise DocumentError(f"The file exceeds the {max_bytes // (1024 * 1024)} MB upload limit.")
    metadata: dict[str, Any] = {"byte_count": len(content), "format": extension.lstrip(".")}
    segments: list[Segment] = []
    try:
        if extension == ".pdf":
            import pymupdf

            if b"%PDF-" not in content[:1024]:
                raise DocumentError("The file is not a valid PDF.")
            with pymupdf.open(stream=content, filetype="pdf") as document:
                if document.needs_pass:
                    raise DocumentError("Password-protected PDFs must be unlocked before upload.")
                if document.page_count > 200:
                    raise DocumentError("PDFs are limited to 200 pages per upload.")
                metadata["pages"] = document.page_count
                for number, page in enumerate(document, 1):
                    page_text = page.get_text("text", sort=True)
                    segments.append(Segment(f"Page {number}", page_text))
        elif extension == ".docx":
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                entries = archive.infolist()
                if len(entries) > 2000 or sum(x.file_size for x in entries) > 20 * 1024 * 1024:
                    raise DocumentError("The DOCX expands beyond the safe processing limit.")
                if any(x.file_size > max(1, x.compress_size) * 1000 for x in entries):
                    raise DocumentError("The DOCX compression ratio exceeds the safe processing limit.")
                if "word/document.xml" not in archive.namelist():
                    raise DocumentError("The file is not a valid DOCX document.")
            from docx import Document

            document = Document(io.BytesIO(content))
            heading = "Document"
            for number, paragraph in enumerate(document.paragraphs, 1):
                if paragraph.style and paragraph.style.name.startswith("Heading"):
                    heading = paragraph.text[:150]
                segments.append(Segment(f"{heading} · paragraph {number}", paragraph.text))
            for table_number, table in enumerate(document.tables, 1):
                for row_number, row in enumerate(table.rows, 1):
                    segments.append(
                        Segment(
                            f"Table {table_number} · row {row_number}",
                            " | ".join(cell.text for cell in row.cells),
                        )
                    )
            metadata["paragraphs"] = len(document.paragraphs)
        else:
            try:
                text = content.decode("utf-8-sig")
            except UnicodeDecodeError:
                raise DocumentError("Text documents must use UTF-8 encoding.") from None
            if "\x00" in text:
                raise DocumentError("Binary content is not supported as a text document.")
            if extension != ".json":
                return parse_text(text, kind=extension.lstrip("."), metadata=metadata)
            cleaned, detected, redactions = privacy_filter(text)
            if not cleaned and detected:
                metadata.update({"detected_types": detected, "stored_content": False})
                return ParsedDocument([], metadata, True, detected, redactions)
            try:
                value = json.loads(cleaned)
            except (json.JSONDecodeError, RecursionError):
                raise DocumentError("The file does not contain valid, supported JSON.") from None
            segments = _json_segments(value)
            metadata.update({"redacted_count": redactions, "detected_types": detected})
            if not segments:
                raise DocumentError("The JSON contains no knowledge to index.")
            return ParsedDocument(_bound_segments(segments, metadata), metadata, False, detected, redactions)
    except DocumentError:
        raise
    except Exception:
        raise DocumentError("The document could not be parsed. Check its format and try again.") from None
    if not any(segment.text.strip() for segment in segments):
        raise DocumentError("No readable text was found. Scanned PDFs require OCR before upload.")
    detected_types: set[str] = set()
    redacted_count = 0
    safe_segments: list[Segment] = []
    for segment in segments:
        cleaned, detected, count = privacy_filter(segment.text)
        detected_types.update(detected)
        redacted_count += count
        if detected and not cleaned:
            metadata.update({"detected_types": sorted(detected_types), "stored_content": False})
            return ParsedDocument([], metadata, True, sorted(detected_types), redacted_count)
        safe_segments.append(Segment(safe_name(segment.locator), cleaned))
    metadata.update({"detected_types": sorted(detected_types), "redacted_count": redacted_count})
    return ParsedDocument(
        _bound_segments(safe_segments, metadata), metadata, False, sorted(detected_types), redacted_count
    )


def invalidate_source(db: Session, source: Source) -> int:
    """Invalidate every dependent claim; stale evidence never stays authoritative."""
    from sqlalchemy import select

    from app.models import Claim, Evidence

    claim_ids = set(db.scalars(select(Evidence.claim_id).where(Evidence.source_id == source.id)))
    claims = list(db.scalars(select(Claim).where(Claim.id.in_(claim_ids)))) if claim_ids else []
    for claim in claims:
        claim.status = "invalidated"
        claim.verified_by = None
        claim.verified_at = None
    return len(claims)


def ingest_parsed(
    db: Session,
    user: User,
    project_id: str,
    *,
    name: str,
    kind: str,
    parsed: ParsedDocument,
    checksum: str,
    acl: list[str] | None = None,
    connection_id: str | None = None,
    external_id: str | None = None,
    url: str | None = None,
    source_time: datetime | None = None,
    synthetic: bool = False,
) -> tuple[Source, bool]:
    from sqlalchemy import select

    from app.models import Chunk, Source
    from app.security import audit, project_access

    project_access(db, user, project_id, write=True)
    allowed = sorted(set(acl or []))
    # A duplicate with different access scope is a different source. Never widen ACL.
    existing_sources = list(
        db.scalars(
            select(Source).where(
                Source.org_id == user.org_id,
                Source.project_id == project_id,
                Source.checksum == checksum,
                Source.status.in_(["ready", "quarantined"]),
            )
        )
    )
    for source in existing_sources:
        if (
            sorted(source.acl or []) == allowed
            and source.connection_id == connection_id
            and source.external_id == external_id
        ):
            return source, True
    source = None
    if external_id and connection_id:
        source = db.scalar(
            select(Source).where(
                Source.org_id == user.org_id,
                Source.project_id == project_id,
                Source.connection_id == connection_id,
                Source.external_id == external_id,
            )
        )
    if source is not None:
        # Re-sync of revoked or permission-changed sources is deliberately blocked.
        if source.status == "revoked" and not (source.source_metadata or {}).get("revoked_by_connection"):
            return source, True
        if sorted(source.acl or []) != allowed:
            raise DocumentError("The existing source has a different access scope.")
        invalidate_source(db, source)
        source.version += 1
        # Historical chunks remain available for audit. Current reconstruction
        # selects only this source's current version.
    else:
        source = Source(org_id=user.org_id, project_id=project_id, version=1)
        db.add(source)
    source.name = safe_name(name)
    source.kind = kind
    source.connection_id = connection_id
    source.external_id = external_id
    source.url = url or ""
    source.checksum = checksum
    source.status = "quarantined" if parsed.quarantined else "ready"
    source.acl = allowed
    source.source_time = source_time or utcnow()
    source.synthetic = synthetic
    source.source_metadata = safe_metadata(parsed.metadata)
    db.flush()
    for ordinal, segment in enumerate(parsed.segments):
        db.add(
            Chunk(
                org_id=user.org_id,
                project_id=project_id,
                source_id=source.id,
                source_version=source.version,
                ordinal=ordinal,
                locator=segment.locator,
                text=segment.text,
            )
        )
    audit(
        db,
        user,
        project_id,
        "source.quarantined" if parsed.quarantined else "source.ingested",
        "source",
        source.id,
        {
            "kind": kind,
            "version": source.version,
            "chunks": len(parsed.segments),
            "redacted_count": parsed.redacted_count,
            "detected_types": parsed.detected_types,
        },
    )
    db.flush()
    return source, False


def ingest_document(
    db: Session, user: User, project_id: str, *, filename: str, content: bytes, acl: list[str] | None = None
) -> tuple[Source, bool]:
    from app.config import settings

    parsed = parse_document(filename, content, max_bytes=settings.max_upload_bytes)
    return ingest_parsed(
        db,
        user,
        project_id,
        name=filename,
        kind=PurePath(filename).suffix.lower().lstrip("."),
        parsed=parsed,
        checksum=hashlib.sha256(content).hexdigest(),
        acl=acl,
    )


def serialize_source(db: Session, user: User, source: Source) -> dict[str, Any]:
    from fastapi import HTTPException
    from sqlalchemy import func, select

    from app.models import Chunk
    from app.security import can_read_source

    if not can_read_source(db, user, source, include_inactive=True):
        raise HTTPException(404, "Source not found or access unavailable.")
    count = (
        db.scalar(
            select(func.count(Chunk.id)).where(
                Chunk.source_id == source.id, Chunk.source_version == source.version
            )
        )
        or 0
    )
    # Metadata is an explicit allowlist so connector tokens and arbitrary uploaded
    # JSON cannot be reflected by a serializer.
    allowed_meta = {
        "pages",
        "paragraphs",
        "format",
        "byte_count",
        "line_count",
        "truncated",
        "extracted_characters",
        "redacted_count",
        "detected_types",
        "stored_content",
        "repository",
        "number",
        "state",
        "labels",
        "paths",
        "author_login",
    }
    metadata = {k: v for k, v in (source.source_metadata or {}).items() if k in allowed_meta}
    return {
        "id": source.id,
        "name": source.name,
        "kind": source.kind,
        "status": source.status,
        "url": source.url,
        "version": source.version,
        "source_time": source.source_time,
        "updated_at": source.updated_at,
        "synthetic": source.synthetic,
        "restricted": bool(source.acl),
        "metadata": metadata,
        "chunk_count": count,
    }
