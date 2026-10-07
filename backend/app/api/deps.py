"""FastAPI dependencies. Tests replace these with `app.dependency_overrides`."""

from functools import lru_cache

from app.core.config import get_settings
from app.llm.anthropic_client import AnthropicIntentExtractor
from app.llm.base import IntentExtractor


@lru_cache
def get_intent_extractor() -> IntentExtractor:
    """One shared extractor (and HTTP connection pool) per process."""
    return AnthropicIntentExtractor.from_settings(get_settings())
