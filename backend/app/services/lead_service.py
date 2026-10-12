"""Lead application logic. Persists through a store; knows nothing about HTTP or SQL."""

from typing import Protocol

from app.db.models import Lead
from app.schemas.lead import LeadRequest


class LeadStore(Protocol):
    def add(self, *, name: str, phone: str | None, email: str | None, reason: str) -> Lead: ...


def create_lead(request: LeadRequest, store: LeadStore) -> Lead:
    """Save a validated lead. Raises if persistence fails; never reports success otherwise."""
    return store.add(name=request.name, phone=request.phone, email=request.email, reason=request.reason)
