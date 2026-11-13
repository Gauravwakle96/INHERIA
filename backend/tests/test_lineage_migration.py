"""Existing interview metadata is backfilled without widening source permissions."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import models as m
from app.config import settings


def test_populated_interview_lineage_upgrade_and_owned_downgrade(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{(tmp_path / 'lineage.db').as_posix()}")
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "a73c9d21b004")
    engine = create_engine(settings.database_url)
    with Session(engine) as db:
        org = m.Organisation(name="Migration fixture")
        db.add(org)
        db.flush()
        project = m.Project(org_id=org.id, name="Primary")
        other = m.Project(org_id=org.id, name="Other")
        db.add_all([project, other])
        db.flush()
        parent = m.Source(
            org_id=org.id,
            project_id=project.id,
            name="Restricted parent",
            kind="markdown",
            acl=["existing-reader"],
        )
        db.add(parent)
        db.flush()
        gap = m.Gap(
            org_id=org.id,
            project_id=project.id,
            title="Missing recovery detail",
            kind="procedure",
            source_ids=[parent.id],
        )
        db.add(gap)
        db.flush()
        originals = [
            ("historical", project.id, "interview", {"gap_id": gap.id, "existing": "preserved"}),
            (
                "already-linked",
                project.id,
                "interview",
                {"gap_id": gap.id, "lineage_source_ids": [parent.id]},
            ),
            ("different-project", other.id, "interview", {"gap_id": gap.id}),
            ("orphan", project.id, "interview", {"gap_id": "missing-gap"}),
            ("document", project.id, "markdown", {"gap_id": gap.id}),
        ]
        sources = [
            m.Source(org_id=org.id, project_id=pid, name=name, kind=kind, source_metadata=metadata)
            for name, pid, kind, metadata in originals
        ]
        db.add_all(sources)
        db.commit()
        parent_id, source_ids = parent.id, {s.name: s.id for s in sources}
    command.upgrade(config, "head")
    command.upgrade(config, "head")
    with Session(engine) as db:
        historical = db.get(m.Source, source_ids["historical"])
        assert historical.source_metadata == {
            **originals[0][3],
            "lineage_source_ids": [parent_id],
            "lineage_backfill_version": "source-acl-v1",
        }
        for name, _, _, metadata in originals[1:]:
            assert db.get(m.Source, source_ids[name]).source_metadata == metadata
        assert db.get(m.Source, parent_id).acl == ["existing-reader"]
    command.downgrade(config, "a73c9d21b004")
    with Session(engine) as db:
        for name, _, _, metadata in originals:
            assert db.get(m.Source, source_ids[name]).source_metadata == metadata
        assert db.get(m.Source, parent_id).acl == ["existing-reader"]
    engine.dispose()
