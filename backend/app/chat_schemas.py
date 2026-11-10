from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas import StrictModel


class AISettingsUpdate(StrictModel):
    base_url: Literal["https://agentrouter.org/v1", "https://ps.air-outer.com/v1"] = (
        "https://agentrouter.org/v1"
    )
    model: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
    protocol: Literal["responses", "chat_completions"] = "responses"
    api_key: str | None = Field(default=None, min_length=12, max_length=300, repr=False, pattern=r"^\S+$")
    enabled: bool = False


class ChatRequest(StrictModel):
    message: str = Field(min_length=3, max_length=4000)
    effort: Literal["low", "high"] = "low"
    model: Literal["gpt-6.1-sol", "gpt-6-astra", "gpt-5.6-sol"] | None = None
    request_id: UUID


class ActionRequest(StrictModel):
    kind: Literal[
        "investigate", "sync", "start_capture", "generate_handover", "generate_exercises", "simulate"
    ]
    target_id: str = Field(default="", max_length=36)


class Confirmation(StrictModel):
    confirm: Literal[True]
