"""Persisted knowledge, evidence and human workflow with explicit tenant/project scopes."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_id():
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class Identity:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class TenantScope:
    org_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)


class ProjectScope(TenantScope):
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)


class Organisation(Identity, Base):
    __tablename__ = "organisations"
    name: Mapped[str] = mapped_column(String(150))
    industry: Mapped[str] = mapped_column(String(80), default="technology")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class User(Identity, TenantScope, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(100), default="Team member")
    role: Mapped[str] = mapped_column(String(30), default="employee")
    password_hash: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Project(Identity, TenantScope, Base):
    __tablename__ = "projects"
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, default="")
    stack: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="active")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class Membership(Identity, Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_user"),)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(30), default="employee")


class SessionRecord(Identity, Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    csrf_token: Mapped[str] = mapped_column(String(100))
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class DemoVisit(Identity, TenantScope, Base):
    __tablename__ = "demo_visits"
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class Invitation(Identity, ProjectScope, Base):
    __tablename__ = "invitations"
    email: Mapped[str] = mapped_column(String(254))
    name: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(30))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")


class AccessRequest(Identity, ProjectScope, Base):
    __tablename__ = "access_requests"
    requested_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=True)
    purpose: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    note: Mapped[str] = mapped_column(Text, default="")
    reviewed_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class Connection(Identity, ProjectScope, Base):
    __tablename__ = "connections"
    __table_args__ = (UniqueConstraint("project_id", "provider", "repository", name="uq_connection_repo"),)
    name: Mapped[str] = mapped_column(String(180))
    provider: Mapped[str] = mapped_column(String(30))
    repository: Mapped[str] = mapped_column(String(240), default="")
    status: Mapped[str] = mapped_column(String(30), default="available", index=True)
    encrypted_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Source(Identity, ProjectScope, Base):
    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("project_id", "connection_id", "external_id", name="uq_source_external"),
        Index("ix_source_project_checksum", "project_id", "checksum"),
    )
    connection_id: Mapped[str | None] = mapped_column(
        ForeignKey("connections.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(500))
    kind: Mapped[str] = mapped_column(String(30))
    external_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    url: Mapped[str] = mapped_column(Text, default="")
    checksum: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(30), default="ready", index=True)
    acl: Mapped[list] = mapped_column(JSON, default=list)
    version: Mapped[int] = mapped_column(Integer, default=1)
    source_time: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    source_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)


class Chunk(Identity, ProjectScope, Base):
    __tablename__ = "chunks"
    __table_args__ = (UniqueConstraint("source_id", "source_version", "ordinal", name="uq_chunk_ordinal"),)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    source_version: Mapped[int] = mapped_column(Integer, default=1)
    ordinal: Mapped[int] = mapped_column(Integer, default=0)
    locator: Mapped[str] = mapped_column(String(250), default="")
    text: Mapped[str] = mapped_column(Text)


class Claim(Identity, ProjectScope, Base):
    __tablename__ = "claims"
    __table_args__ = (Index("ix_claim_project_kind_status", "project_id", "kind", "status"),)
    kind: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    confidence: Mapped[str] = mapped_column(String(30), default="limited")
    confidence_reason: Mapped[str] = mapped_column(Text, default="Awaiting independent verification")
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Evidence(Identity, ProjectScope, Base):
    __tablename__ = "evidence"
    __table_args__ = (UniqueConstraint("claim_id", "chunk_id", "source_version", name="uq_claim_evidence"),)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), index=True)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    source_version: Mapped[int] = mapped_column(Integer)
    quote: Mapped[str] = mapped_column(Text)


class Investigation(Identity, ProjectScope, Base):
    __tablename__ = "investigations"
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    report: Mapped[dict] = mapped_column(JSON, default=dict)


class Gap(Identity, ProjectScope, Base):
    __tablename__ = "gaps"
    __table_args__ = (Index("ix_gap_project_status", "project_id", "status"),)
    title: Mapped[str] = mapped_column(String(500))
    kind: Mapped[str] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(30), default="open")
    claim_id: Mapped[str | None] = mapped_column(ForeignKey("claims.id", ondelete="SET NULL"), nullable=True)
    investigation_id: Mapped[str | None] = mapped_column(
        ForeignKey("investigations.id", ondelete="SET NULL"), nullable=True
    )
    details: Mapped[str] = mapped_column(Text, default="")
    question: Mapped[str] = mapped_column(Text, default="")
    source_ids: Mapped[list] = mapped_column(JSON, default=list)
    note: Mapped[str] = mapped_column(Text, default="")


class Simulation(Identity, ProjectScope, Base):
    __tablename__ = "simulations"
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    employee_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    scenario: Mapped[str] = mapped_column(String(50))
    assumptions: Mapped[list] = mapped_column(JSON, default=list)
    report: Mapped[dict] = mapped_column(JSON, default=dict)


class Transition(Identity, ProjectScope, Base):
    __tablename__ = "transitions"
    departing_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    successor_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    departure_date: Mapped[str] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    version: Mapped[int] = mapped_column(Integer, default=0)
    report: Mapped[dict] = mapped_column(JSON, default=dict)


class Transfer(Identity, ProjectScope, Base):
    __tablename__ = "transfers"
    __table_args__ = (UniqueConstraint("transition_id", "claim_id", name="uq_transfer_claim"),)
    transition_id: Mapped[str] = mapped_column(ForeignKey("transitions.id", ondelete="CASCADE"), index=True)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), index=True)
    successor_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    backup_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    note: Mapped[str] = mapped_column(Text, default="")
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Exercise(Identity, ProjectScope, Base):
    __tablename__ = "exercises"
    transition_id: Mapped[str] = mapped_column(ForeignKey("transitions.id", ondelete="CASCADE"), index=True)
    transfer_id: Mapped[str | None] = mapped_column(
        ForeignKey("transfers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    prompt: Mapped[str] = mapped_column(Text)
    criteria: Mapped[list] = mapped_column(JSON, default=list)
    expected_source_ids: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    answer: Mapped[str] = mapped_column(Text, default="")
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    escalation: Mapped[str] = mapped_column(Text, default="")
    supervisor_note: Mapped[str] = mapped_column(Text, default="")
    assessment: Mapped[dict] = mapped_column(JSON, default=dict)
    reviewed_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class Job(Identity, ProjectScope, Base):
    __tablename__ = "jobs"
    connection_id: Mapped[str | None] = mapped_column(
        ForeignKey("connections.id", ondelete="SET NULL"), nullable=True
    )
    requested_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    error: Mapped[str] = mapped_column(Text, default="")
    stats: Mapped[dict] = mapped_column(JSON, default=dict)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Audit(Identity, TenantScope, Base):
    __tablename__ = "audit_events"
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(50))
    resource_id: Mapped[str] = mapped_column(String(36), default="")
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class AIConfiguration(Identity, TenantScope, Base):
    __tablename__ = "ai_configurations"
    __table_args__ = (UniqueConstraint("org_id", name="uq_ai_configuration_org"),)
    provider: Mapped[str] = mapped_column(String(30), default="agentrouter")
    base_url: Mapped[str] = mapped_column(String(240), default="https://agentrouter.org/v1")
    model: Mapped[str] = mapped_column(String(120), default="")
    protocol: Mapped[str] = mapped_column(String(20), default="responses")
    encrypted_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)


class Conversation(Identity, ProjectScope, Base):
    __tablename__ = "conversations"
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(100), default="New conversation")


class ChatTurn(Identity, ProjectScope, Base):
    __tablename__ = "chat_turns"
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    request_id: Mapped[str] = mapped_column(String(36))
    __table_args__ = (UniqueConstraint("conversation_id", "request_id", name="uq_chat_request"),)
    question: Mapped[str] = mapped_column(Text)
    effort: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="running")
    response: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)


class ChatAction(Identity, ProjectScope, Base):
    __tablename__ = "chat_actions"
    turn_id: Mapped[str] = mapped_column(ForeignKey("chat_turns.id", ondelete="CASCADE"), index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    target_id: Mapped[str] = mapped_column(String(36), default="")
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
