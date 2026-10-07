"""Provider-neutral LLM boundary: the interface and the errors callers can expect."""

from typing import Protocol

from app.schemas.intent import IntentResult


class LLMError(Exception):
    """Base class for failures of the LLM layer."""


class LLMNotConfiguredError(LLMError):
    """No credentials or settings available to call the provider."""


class LLMProviderError(LLMError):
    """The provider call failed (network, timeout, rate limit, server error, auth)."""


class LLMOutputError(LLMError):
    """The provider answered, but not with a usable, schema-valid result."""


class IntentExtractor(Protocol):
    """Anything that can turn a user message into a validated IntentResult."""

    async def extract_intent(self, message: str) -> IntentResult: ...
