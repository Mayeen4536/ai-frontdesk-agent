"""FastAPI dependencies. Tests replace these with `app.dependency_overrides`."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_session
from app.llm.anthropic_client import AnthropicIntentExtractor
from app.llm.base import IntentExtractor
from app.repositories.lead_repository import LeadRepository


@lru_cache
def get_intent_extractor() -> IntentExtractor:
    """One shared extractor (and HTTP connection pool) per process."""
    return AnthropicIntentExtractor.from_settings(get_settings())


def get_lead_repository(session: Annotated[Session, Depends(get_session)]) -> LeadRepository:
    return LeadRepository(session)
