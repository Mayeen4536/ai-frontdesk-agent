"""Request and response contracts for the lead endpoint."""

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


def _strip(value: str) -> str:
    return value.strip()


class LeadRequest(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None
    reason: str

    @field_validator("name", "reason")
    @classmethod
    def required_text_not_blank(cls, value: str) -> str:
        """Required text fields must contain something besides whitespace."""
        value = _strip(value)
        if not value:
            raise ValueError("must not be empty or whitespace-only")
        return value

    @field_validator("phone", "email")
    @classmethod
    def blank_contact_becomes_none(cls, value: str | None) -> str | None:
        """Treat blank optional contact fields as not provided."""
        if value is None:
            return None
        return _strip(value) or None

    @model_validator(mode="after")
    def require_a_contact_method(self) -> Self:
        """A lead is only useful if the clinic can reach the person."""
        if self.phone is None and self.email is None:
            raise ValueError("at least one of phone or email is required")
        return self


class LeadResponse(BaseModel):
    """The saved record, as stored."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str | None
    email: str | None
    reason: str
    created_at: datetime
