from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.chat_provider import BYNARA_BASE, ProviderBase
from app.schemas import StrictModel


class AISettingsUpdate(StrictModel):
    base_url: ProviderBase = "https://agentrouter.org/v1"
    model: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
    protocol: Literal["responses", "chat_completions"] = "responses"
    api_key: str | None = Field(default=None, min_length=12, max_length=300, repr=False, pattern=r"^\S+$")
    enabled: bool = False

    @model_validator(mode="after")
    def compatible_protocol(self):
        if self.base_url == BYNARA_BASE and self.protocol != "chat_completions":
            raise ValueError("Bynara requires the Chat Completions protocol")
        return self


class ChatRequest(StrictModel):
    message: str = Field(min_length=3, max_length=4000)
    effort: Literal["low", "high"] = "low"
    model: str | None = Field(
        default=None, min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$"
    )
    request_id: UUID


class ActionRequest(StrictModel):
    kind: Literal[
        "investigate", "sync", "start_capture", "generate_handover", "generate_exercises", "simulate"
    ]
    target_id: str = Field(default="", max_length=36)


class Confirmation(StrictModel):
    confirm: Literal[True]
