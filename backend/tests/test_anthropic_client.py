from types import SimpleNamespace
from typing import Any

import anthropic
import httpx2
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.llm.anthropic_client import AnthropicIntentExtractor
from app.llm.base import LLMNotConfiguredError, LLMOutputError, LLMProviderError
from app.llm.prompts import INTENT_SYSTEM_PROMPT
from app.schemas.intent import IntentResult


class FakeMessages:
    """Mimics `AsyncAnthropic().messages`: records the call, then returns or raises."""

    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.kwargs: dict[str, Any] = {}

    async def parse(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.response


def make_extractor(messages: FakeMessages) -> AnthropicIntentExtractor:
    return AnthropicIntentExtractor(SimpleNamespace(messages=messages), "test-model")  # type: ignore[arg-type]


@pytest.mark.anyio
async def test_extract_intent_success_uses_schema_and_instructions() -> None:
    expected = IntentResult(intent="book_appointment", reason="broken tooth", requested_date="tomorrow")
    messages = FakeMessages(SimpleNamespace(parsed_output=expected, stop_reason="end_turn"))

    result = await make_extractor(messages).extract_intent("My tooth broke")

    assert result == expected
    assert messages.kwargs["output_format"] is IntentResult
    assert messages.kwargs["system"] == INTENT_SYSTEM_PROMPT
    assert messages.kwargs["model"] == "test-model"
    assert messages.kwargs["messages"] == [{"role": "user", "content": "My tooth broke"}]


@pytest.mark.anyio
async def test_provider_failure_becomes_llm_provider_error() -> None:
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    messages = FakeMessages(error=anthropic.APIConnectionError(request=request))
    with pytest.raises(LLMProviderError):
        await make_extractor(messages).extract_intent("hi")


@pytest.mark.anyio
async def test_missing_parsed_output_becomes_llm_output_error() -> None:
    messages = FakeMessages(SimpleNamespace(parsed_output=None, stop_reason="max_tokens"))
    with pytest.raises(LLMOutputError, match="max_tokens"):
        await make_extractor(messages).extract_intent("hi")


@pytest.mark.anyio
async def test_schema_validation_failure_becomes_llm_output_error() -> None:
    with pytest.raises(ValidationError) as info:
        IntentResult.model_validate({"intent": "launch_rocket"})
    messages = FakeMessages(error=info.value)
    with pytest.raises(LLMOutputError):
        await make_extractor(messages).extract_intent("hi")


def test_intent_schema_rejects_unknown_intent() -> None:
    with pytest.raises(ValidationError):
        IntentResult.model_validate({"intent": "launch_rocket"})


@pytest.mark.anyio
async def test_missing_api_key_is_reported_at_call_time() -> None:
    settings = Settings(anthropic_api_key=None, llm_model="m", llm_timeout_seconds=5.0)
    extractor = AnthropicIntentExtractor.from_settings(settings)  # does not raise
    with pytest.raises(LLMNotConfiguredError):
        await extractor.extract_intent("hi")


def test_system_prompt_keeps_responsibilities_narrow() -> None:
    text = INTENT_SYSTEM_PROMPT.lower()
    for phrase in ("never guess", "do not claim anything was booked", "medical advice", "untrusted"):
        assert phrase in text
