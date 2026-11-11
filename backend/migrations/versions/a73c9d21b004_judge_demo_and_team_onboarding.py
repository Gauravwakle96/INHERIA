"""Isolated judge visits, secure invitations and scoped access requests."""

import sqlalchemy as sa
from alembic import op

revision = "a73c9d21b004"
down_revision = "e4058f85541c"
branch_labels = None
depends_on = None


def identity():
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    ]


def scope(project=False):
    columns = [
        sa.Column(
            "org_id", sa.String(36), sa.ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False
        )
    ]
    if project:
        columns.append(
            sa.Column(
                "project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
            )
        )
    return columns


def upgrade():
    op.create_table(
        "demo_visits",
        *identity(),
        *scope(),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "invitations",
        *identity(),
        *scope(True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
    )
    op.create_table(
        "access_requests",
        *identity(),
        *scope(True),
        sa.Column(
            "requested_by", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column(
            "reviewed_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
    )
    for table in ("demo_visits", "invitations", "access_requests"):
        op.create_index("ix_" + table + "_org_id", table, ["org_id"])
        if table != "demo_visits":
            op.create_index("ix_" + table + "_project_id", table, ["project_id"])
        if table != "access_requests":
            op.create_index("ix_" + table + "_token_hash", table, ["token_hash"], unique=True)
            op.create_index("ix_" + table + "_expires_at", table, ["expires_at"])


def downgrade():
    for table in ("access_requests", "invitations", "demo_visits"):
        op.drop_table(table)
