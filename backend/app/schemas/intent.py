"""Structured classification result for a user message."""

from typing import Literal

from pydantic import BaseModel

Intent = Literal["book_appointment", "business_question", "unknown"]


class IntentResult(BaseModel):
    """What the user appears to want, as typed data rather than free text.

    Optional fields are None when the message did not provide them.
    """

    intent: Intent
    reason: str | None = None
    requested_date: str | None = None
    time_preference: str | None = None
