"""Anthropic implementation of IntentExtractor. All provider-specific code lives here."""

import anthropic
from pydantic import ValidationError

from app.core.config import Settings
from app.llm.base import LLMNotConfiguredError, LLMOutputError, LLMProviderError
from app.llm.prompts import INTENT_SYSTEM_PROMPT
from app.schemas.intent import IntentResult

_MAX_OUTPUT_TOKENS = 256  # the structured result is tiny


class AnthropicIntentExtractor:
    def __init__(self, client: anthropic.AsyncAnthropic | None, model: str) -> None:
        self._client = client
        self._model = model

    @classmethod
    def from_settings(cls, settings: Settings) -> "AnthropicIntentExtractor":
        """Build from settings. A missing key is reported at call time, not here, so that
        request validation errors (422) still win over configuration errors (503)."""
        if not settings.anthropic_api_key:
            return cls(None, settings.llm_model)
        client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=settings.llm_timeout_seconds,
        )
        return cls(client, settings.llm_model)

    async def extract_intent(self, message: str) -> IntentResult:
        if self._client is None:
            raise LLMNotConfiguredError("ANTHROPIC_API_KEY is not set")
        try:
            response = await self._client.messages.parse(
                model=self._model,
                max_tokens=_MAX_OUTPUT_TOKENS,
                temperature=0,
                system=INTENT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": message}],
                output_format=IntentResult,  # schema-constrained output, validated by Pydantic
            )
        except anthropic.APIError as exc:  # status, connection and timeout errors
            raise LLMProviderError(f"{type(exc).__name__} calling the model") from exc
        except ValidationError as exc:
            raise LLMOutputError("model output failed schema validation") from exc

        if response.parsed_output is None:
            raise LLMOutputError(f"no structured output (stop_reason={response.stop_reason})")
        return response.parsed_output
