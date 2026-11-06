from __future__ import annotations

import io
import json
import zipfile

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ingestion import (
    DocumentError,
    ParsedDocument,
    Segment,
    ingest_document,
    ingest_parsed,
    invalidate_source,
    parse_document,
    parse_text,
    privacy_filter,
    serialize_source,
)
from app.models import Base, Chunk, Claim, Evidence, Membership, Organisation, Project, Source, User


@pytest.fixture
def source_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        org = Organisation(name="Parser test", industry="technology", is_demo=False)
        db.add(org)
        db.flush()
        actor = User(
            org_id=org.id,
            name="Test Manager",
            email="manager@parser.example",
            title="Project Manager",
            role="manager",
            password_hash="unused",
            active=True,
        )
        colleague = User(
            org_id=org.id,
            name="Test Engineer",
            email="engineer@parser.example",
            title="Engineer",
            role="employee",
            password_hash="unused",
            active=True,
        )
        project = Project(org_id=org.id, name="Parser project", description="Tests", stack=[], is_demo=False)
        db.add_all([actor, colleague, project])
        db.flush()
        db.add_all(
            [
                Membership(project_id=project.id, user_id=actor.id, role="manager"),
                Membership(project_id=project.id, user_id=colleague.id, role="employee"),
            ]
        )
        db.commit()
        yield db, actor, colleague, project
    engine.dispose()


def test_markdown_keeps_headings_and_line_locations():
    parsed = parse_document(
        "runbook.md", b"# Deployment\nDeploy only to staging.\n# Rollback\nUse previous release.\n"
    )
    assert len(parsed.segments) == 2
    assert "Deployment" in parsed.segments[0].locator
    assert "lines 1" in parsed.segments[0].locator
    assert "Rollback" in parsed.segments[1].locator
    assert not parsed.quarantined


def test_pdf_keeps_real_page_references():
    import pymupdf

    with pymupdf.open() as document:
        document.new_page().insert_text((72, 72), "Deployment pipeline: staging approval required.")
        document.new_page().insert_text((72, 72), "Rollback procedure: restore previous release.")
        content = document.tobytes()
    parsed = parse_document("operations.pdf", content)
    assert parsed.metadata["pages"] == 2
    assert [item.locator for item in parsed.segments] == ["Page 1", "Page 2"]
    assert "restore previous release" in parsed.segments[1].text


def test_docx_keeps_paragraph_and_table_references():
    from docx import Document

    document = Document()
    document.add_heading("Recovery", level=1)
    document.add_paragraph("Check the backup restore log.")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Database"
    table.cell(0, 1).text = "PostgreSQL"
    buffer = io.BytesIO()
    document.save(buffer)
    parsed = parse_document("recovery.docx", buffer.getvalue())
    assert any("Recovery" in segment.locator for segment in parsed.segments)
    assert any("Table 1" in segment.locator and "PostgreSQL" in segment.text for segment in parsed.segments)


@pytest.mark.parametrize(
    "filename,content",
    [
        ("empty.txt", b""),
        ("binary.txt", b"bad\x00text"),
        ("invalid.json", b"{broken"),
        ("invalid.pdf", b"not a pdf"),
        ("invalid.docx", b"not a zip"),
        ("image.png", b"not supported"),
    ],
)
def test_malformed_documents_fail_with_safe_errors(filename, content):
    with pytest.raises(DocumentError) as error:
        parse_document(filename, content)
    assert content.decode("utf-8", errors="ignore") not in str(error.value) or content == b""


def test_scanned_pdf_is_explicitly_not_ocr_supported():
    import pymupdf

    with pymupdf.open() as document:
        document.new_page()
        content = document.tobytes()
    with pytest.raises(DocumentError, match="OCR"):
        parse_document("scan.pdf", content)


def test_upload_size_and_decompression_caps():
    with pytest.raises(DocumentError, match="upload limit"):
        parse_document("large.txt", b"x" * 101, max_bytes=100)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", "x" * 1_000_000)
    with pytest.raises(DocumentError, match="compression ratio"):
        parse_document("bomb.docx", buffer.getvalue())


def test_json_has_pointer_locations_and_rejects_extreme_nesting():
    parsed = parse_document("tasks.json", json.dumps({"project": {"tasks": ["Verify staging"]}}).encode())
    assert parsed.segments[0].locator == "$.project.tasks[0]"
    with pytest.raises(DocumentError, match="depth"):
        parse_document("deep.json", ("[" * 50 + "0" + "]" * 50).encode())


@pytest.mark.parametrize(
    "content",
    [
        "password=real-secret-value",
        '{"password": "real-secret-value"}',
        "-----BEGIN PRIVATE KEY-----\nprivate-data\n-----END PRIVATE KEY-----",
        "postgresql://administrator:actual-password@db.internal/app",
        "Authorization: Bearer " + "a" * 35,
        "ghp_" + "a" * 36,
    ],
)
def test_secret_content_is_quarantined_without_retaining_raw_text(content):
    parsed = parse_document("private.txt", content.encode())
    assert parsed.quarantined
    assert parsed.segments == []
    assert parsed.detected_types
    assert content not in json.dumps(parsed.metadata)


def test_secret_beyond_indexing_limit_still_quarantines():
    parsed = parse_document("long.txt", ("Safe content.\n" * 10_000 + "password=real-secret-value").encode())
    assert parsed.quarantined
    assert not parsed.segments


def test_quarantine_removes_secret_metadata_too():
    secret = "ghp_" + "a" * 36
    parsed = parse_text(
        "Labels: " + secret, metadata={"labels": [secret], "note": "password=real-secret-value"}
    )
    assert parsed.quarantined
    assert secret not in json.dumps(parsed.metadata)
    assert "real-secret-value" not in json.dumps(parsed.metadata)


def test_placeholder_and_pii_handling():
    text, kinds, count = privacy_filter(
        "password=${DEPLOY_PASSWORD}\nContact someone@gmail.com or +1 415 555 1234"
    )
    assert text
    assert "someone@gmail.com" not in text
    assert "+1 415 555 1234" not in text
    assert "pii_redacted" in kinds and count == 2
    assert "fiction@nexora.example" in privacy_filter("fiction@nexora.example")[0]


@pytest.mark.parametrize(
    "assignment", ["password:\n  unsafe-secret-value", '"api_key":\n  "unsafe-secret-value"']
)
def test_multiline_secret_assignment_is_quarantined(assignment):
    parsed = parse_document("multiline.txt", assignment.encode())
    assert parsed.quarantined and not parsed.segments
    assert "unsafe-secret-value" not in json.dumps(parsed.metadata)


@pytest.mark.parametrize(
    "placeholder",
    ["${DEPLOY_PASSWORD}", "$DEPLOY_PASSWORD", "$env:DEPLOY_PASSWORD", "%DEPLOY_PASSWORD%", "[REDACTED]"],
)
def test_multiline_documented_environment_placeholders_remain_readable(placeholder):
    parsed = parse_document("setup.md", ("# Setup\npassword:\n  " + placeholder).encode())
    assert not parsed.quarantined and parsed.segments


def test_text_indexing_caps_are_visible():
    parsed = parse_text("Evidence line\n" * 20_000)
    assert parsed.metadata["truncated"]
    assert parsed.metadata["extracted_characters"] <= 100_000
    assert len(parsed.segments) <= 200


def test_duplicate_ingestion_does_not_widen_source_permissions(source_db):
    db, actor, colleague, project = source_db
    first, duplicate = ingest_document(
        db, actor, project.id, filename="runbook.md", content=b"# Runbook\nCheck staging.", acl=[actor.id]
    )
    assert not duplicate
    second, duplicate = ingest_document(
        db, actor, project.id, filename="runbook.md", content=b"# Runbook\nCheck staging.", acl=[actor.id]
    )
    assert duplicate and second.id == first.id
    public, duplicate = ingest_document(
        db, actor, project.id, filename="runbook.md", content=b"# Runbook\nCheck staging.", acl=[]
    )
    assert not duplicate and public.id != first.id
    assert first.acl == [actor.id]
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        serialize_source(db, colleague, first)
    assert error.value.status_code == 404


def test_quarantined_source_persists_only_safe_metadata(source_db):
    db, actor, _, project = source_db
    raw = b"password=real-secret-value"
    source, duplicate = ingest_document(db, actor, project.id, filename="private.txt", content=raw)
    db.commit()
    assert source.status == "quarantined" and not duplicate
    assert not list(db.scalars(select(Chunk).where(Chunk.source_id == source.id)))
    payload = serialize_source(db, actor, source)
    assert raw.decode() not in json.dumps(payload, default=str)
    assert payload["chunk_count"] == 0


def test_source_change_invalidates_claim_but_preserves_historical_citation(source_db):
    db, actor, _, project = source_db
    from app.models import Connection

    connection = Connection(
        org_id=actor.org_id,
        project_id=project.id,
        name="test/repo",
        provider="github",
        repository="test/repo",
        status="connected",
    )
    db.add(connection)
    db.flush()
    source, _ = ingest_parsed(
        db,
        actor,
        project.id,
        name="Runbook",
        kind="markdown",
        parsed=ParsedDocument([Segment("Recovery", "Restore previous release.")]),
        checksum="old",
        connection_id=connection.id,
        external_id="github:file:runbook.md",
    )
    chunk = db.scalar(select(Chunk).where(Chunk.source_id == source.id))
    claim = Claim(
        org_id=actor.org_id,
        project_id=project.id,
        kind="procedure",
        title="Rollback",
        summary=chunk.text,
        status="verified",
        confidence="strong",
        confidence_reason="Verified procedure",
        data={},
    )
    db.add(claim)
    db.flush()
    evidence = Evidence(
        org_id=actor.org_id,
        project_id=project.id,
        source_id=source.id,
        claim_id=claim.id,
        chunk_id=chunk.id,
        source_version=1,
        quote=chunk.text,
    )
    db.add(evidence)
    db.commit()
    updated, _ = ingest_parsed(
        db,
        actor,
        project.id,
        name="Runbook",
        kind="markdown",
        parsed=ParsedDocument([Segment("Recovery", "Validate backup first.")]),
        checksum="new",
        connection_id=connection.id,
        external_id="github:file:runbook.md",
    )
    db.commit()
    assert updated.id == source.id and updated.version == 2
    assert claim.status == "invalidated"
    assert db.get(Chunk, chunk.id).text == "Restore previous release."
    assert db.get(Evidence, evidence.id).source_version == 1
    assert serialize_source(db, actor, updated)["chunk_count"] == 1


def test_revocation_invalidates_all_dependent_claims(source_db):
    db, actor, _, project = source_db
    source, _ = ingest_document(
        db, actor, project.id, filename="procedure.txt", content=b"Deploy to staging."
    )
    chunk = db.scalar(select(Chunk).where(Chunk.source_id == source.id))
    claim = Claim(
        org_id=actor.org_id,
        project_id=project.id,
        kind="procedure",
        title="Deploy",
        summary=chunk.text,
        status="verified",
        confidence="strong",
        confidence_reason="Verified",
        data={},
    )
    db.add(claim)
    db.flush()
    db.add(
        Evidence(
            org_id=actor.org_id,
            project_id=project.id,
            source_id=source.id,
            claim_id=claim.id,
            chunk_id=chunk.id,
            source_version=source.version,
            quote=chunk.text,
        )
    )
    db.flush()
    assert invalidate_source(db, source) == 1
    source.status = "revoked"
    assert claim.status == "invalidated"
    from app.security import can_read_source

    assert not can_read_source(db, actor, source)
    assert can_read_source(db, actor, source, include_inactive=True)


def _api_login(client, *, role="admin"):
    users = client.get("/api/auth/demo-users").json()
    actor = next(user for user in users if user["role"] == role)
    result = client.post("/api/auth/demo-login", json={"user_id": actor["id"]})
    assert result.status_code == 200
    client.headers["X-CSRF-Token"] = result.json()["csrf_token"]
    return actor


def test_upload_api_rejects_unprivileged_user_and_bad_acl(workspace):
    client, _, project_id = workspace
    actor = _api_login(client, role="employee")
    result = client.post(
        f"/api/projects/{project_id}/sources/upload",
        files={"file": ("runbook.md", b"# Deploy\nUse staging.")},
    )
    assert result.status_code == 403
    actor = _api_login(client)
    result = client.post(
        f"/api/projects/{project_id}/sources/upload",
        files={"file": ("runbook.md", b"# Deploy\nUse staging.")},
        data={"allowed_user_ids": json.dumps(["not-a-project-member", actor["id"]])},
    )
    assert result.status_code == 422


def test_upload_api_redacts_pii_and_quarantines_secrets(workspace):
    client, factory, project_id = workspace
    _api_login(client)
    secret = "ghp_" + "a" * 36
    result = client.post(
        f"/api/projects/{project_id}/sources/upload", files={"file": ("private.txt", secret.encode())}
    )
    assert result.status_code == 201 and result.json()["source"]["status"] == "quarantined"
    assert secret not in result.text
    with factory() as db:
        assert not list(db.scalars(select(Chunk).where(Chunk.source_id == result.json()["source"]["id"])))
    result = client.post(
        f"/api/projects/{project_id}/sources/upload",
        files={
            "file": ("contacts.md", b"# Operations\nContact private@gmail.com before staging deployment.")
        },
    )
    assert result.status_code == 201
    evidence = client.get(f"/api/projects/{project_id}/evidence/{result.json()['source']['id']}")
    assert evidence.status_code == 200
    assert "private@gmail.com" not in evidence.text and "email redacted" in evidence.text


def test_delete_api_removes_persisted_derived_quotes(workspace):
    client, factory, project_id = workspace
    actor = _api_login(client)
    marker = "Unique historical deletion marker; rollback restores the previous approved release."
    uploaded = client.post(
        f"/api/projects/{project_id}/sources/upload", files={"file": ("deletion.md", marker.encode())}
    )
    assert uploaded.status_code == 201
    source_id = uploaded.json()["source"]["id"]
    from app.models import Gap, Investigation, Simulation, Transition

    with factory() as db:
        chunk = db.scalar(select(Chunk).where(Chunk.source_id == source_id))
        claim = Claim(
            org_id=actor["org_id"],
            project_id=project_id,
            kind="procedure",
            title="Rollback",
            summary=marker,
            status="verified",
            confidence="strong",
            confidence_reason="Explicit source",
            data={"details": marker},
        )
        db.add(claim)
        db.flush()
        db.add(
            Evidence(
                org_id=actor["org_id"],
                project_id=project_id,
                source_id=source_id,
                claim_id=claim.id,
                chunk_id=chunk.id,
                source_version=1,
                quote=marker,
            )
        )
        db.add(
            Gap(
                org_id=actor["org_id"],
                project_id=project_id,
                title="Review recovery",
                kind="procedure",
                details=marker,
                question=marker,
                source_ids=[source_id],
                claim_id=claim.id,
            )
        )
        db.add(
            Investigation(
                org_id=actor["org_id"],
                project_id=project_id,
                created_by=actor["id"],
                report={"summary": marker, "findings": [{"source_ids": [source_id], "details": marker}]},
            )
        )
        db.add(
            Simulation(
                org_id=actor["org_id"],
                project_id=project_id,
                created_by=actor["id"],
                employee_id=actor["id"],
                scenario="unavailability",
                report={"source_ids": [source_id], "affected": [{"evidence": [{"quote": marker}]}]},
            )
        )
        db.add(
            Transition(
                org_id=actor["org_id"],
                project_id=project_id,
                departing_id=actor["id"],
                successor_id=actor["id"],
                departure_date="2026-12-01",
                title="Deletion test",
                report={"source_ids": [source_id], "knowledge": [{"id": claim.id, "summary": marker}]},
            )
        )
        db.commit()
        claim_id = claim.id
    result = client.delete(f"/api/projects/{project_id}/sources/{source_id}")
    assert result.status_code == 200, result.text
    with factory() as db:
        assert db.get(Source, source_id) is None
        assert not list(db.scalars(select(Chunk).where(Chunk.source_id == source_id)))
        assert db.get(Claim, claim_id).status == "invalidated"
        for model, field in [
            (Claim, "summary"),
            (Claim, "data"),
            (Gap, "details"),
            (Investigation, "report"),
            (Simulation, "report"),
            (Transition, "report"),
        ]:
            assert all(
                marker not in json.dumps(getattr(row, field), default=str)
                for row in db.scalars(select(model))
            )
