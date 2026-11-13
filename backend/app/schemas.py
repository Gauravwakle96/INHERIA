from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProjectCreate(StrictModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)


class Review(StrictModel):
    action: Literal["approve", "reject", "correct"]
    note: str = Field(min_length=3, max_length=2000)
    summary: str | None = Field(default=None, min_length=10, max_length=4000)
    owner_id: str | None = None
    backup_id: str | None = None
    component: str | None = Field(default=None, max_length=120)
    critical: bool | None = None


class InvestigationCreate(StrictModel):
    focus: str = Field(default="", max_length=300)
    employee_id: str | None = None


class GapUpdate(StrictModel):
    status: Literal["open", "in_progress", "resolved"]
    note: str = Field(min_length=3, max_length=2000)


class SimulationCreate(StrictModel):
    employee_id: str
    scenario: Literal["unavailability", "outdated_procedure", "dependency_failure"] = "unavailability"
    component: str = Field(default="", max_length=120)
    assumptions: list[str] = Field(default_factory=list, max_length=10)


class TransitionCreate(StrictModel):
    title: str = Field(min_length=3, max_length=160)
    departing_id: str
    successor_id: str
    departure_date: date


class Note(StrictModel):
    note: str = Field(min_length=3, max_length=2000)
    expected_version: int | None = Field(default=None, ge=0)


class Assignment(StrictModel):
    claim_id: str
    successor_id: str
    backup_id: str | None = None


class TransferResponse(StrictModel):
    action: Literal["accept", "reject"]
    note: str = Field(min_length=3, max_length=2000)


class Submission(StrictModel):
    answer: str = Field(min_length=30, max_length=6000)
    evidence_ids: list[str] = Field(min_length=1, max_length=30)
    escalation: str = Field(min_length=10, max_length=2000)
    validation_kind: Literal["knowledge_walkthrough", "staging_observation"] = "knowledge_walkthrough"
    staging_evidence_ids: list[str] = Field(default_factory=list, max_length=30)


class Assessment(StrictModel):
    action: Literal["pass", "needs_revision"]
    note: str = Field(min_length=10, max_length=2000)
    criteria_passed: list[bool] = Field(default_factory=list, max_length=20)


class Question(StrictModel):
    question: str = Field(min_length=3, max_length=500)


class MemberCreate(StrictModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    title: str = Field(min_length=2, max_length=100)
    role: Literal["manager", "lead", "employee", "incoming", "security"]
    password: str = Field(min_length=12, max_length=200, repr=False)


class InterviewResponse(StrictModel):
    answer: str = Field(min_length=30, max_length=6000)


class Record(BaseModel):
    """Explicitly allow only service-serialised fields; ORM objects never returned."""

    model_config = ConfigDict(extra="allow")
    id: str


class Overview(BaseModel):
    metrics: list[dict[str, Any]]
    activity: list[dict[str, Any]]
    pipeline: list[dict[str, Any]]
    ai_mode: str
    synthetic: bool
    source_health: dict[str, int]


class SuccessorAnswer(BaseModel):
    answer: str
    known: bool
    citations: list[dict[str, Any]]
    unknowns: list[str]
    engine: str
