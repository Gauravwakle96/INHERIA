"""Backfill parent evidence references on previously captured interviews.

Revision ID: b19e47a2c805
Revises: a73c9d21b004
"""

import sqlalchemy as sa
from alembic import op

revision = "b19e47a2c805"
down_revision = "a73c9d21b004"
branch_labels = None
depends_on = None


def tables():
    return (
        sa.table(
            "sources",
            sa.column("id", sa.String),
            sa.column("project_id", sa.String),
            sa.column("kind", sa.String),
            sa.column("metadata", sa.JSON),
        ),
        sa.table(
            "gaps",
            sa.column("id", sa.String),
            sa.column("project_id", sa.String),
            sa.column("source_ids", sa.JSON),
        ),
    )


def upgrade():
    sources, gaps = tables()
    db = op.get_bind()
    parents = {row.id: row for row in db.execute(sa.select(gaps)).all()}
    for row in db.execute(sa.select(sources).where(sources.c.kind == "interview")).all():
        metadata = dict(row.metadata or {})
        gap = parents.get(metadata.get("gap_id"))
        if gap and gap.project_id == row.project_id and "lineage_source_ids" not in metadata:
            metadata.update(lineage_source_ids=gap.source_ids or [], lineage_backfill_version="source-acl-v1")
            db.execute(sources.update().where(sources.c.id == row.id).values(metadata=metadata))


def downgrade():
    sources, _ = tables()
    db = op.get_bind()
    for row in db.execute(sa.select(sources).where(sources.c.kind == "interview")).all():
        metadata = dict(row.metadata or {})
        if metadata.get("lineage_backfill_version") == "source-acl-v1":
            metadata.pop("lineage_backfill_version")
            metadata.pop("lineage_source_ids", None)
            db.execute(sources.update().where(sources.c.id == row.id).values(metadata=metadata))
