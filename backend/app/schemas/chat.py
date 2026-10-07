"""Request and response contracts for the chat endpoint."""

from typing import Literal

from pydantic import BaseModel, field_validator

from app.schemas.intent import IntentResult


class ChatRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        """Reject empty and whitespace-only messages. The original text is kept as is."""
        if not value.strip():
            raise ValueError("message must not be empty or whitespace-only")
        return value


class ChatResponse(BaseModel):
    message: str
    status: Literal["received"] = "received"
    classification: IntentResult
