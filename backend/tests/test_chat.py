from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_intent_extractor
from app.core.config import get_settings
from app.llm.base import IntentExtractor, LLMOutputError, LLMProviderError
from app.main import app
from app.schemas.intent import IntentResult
from tests.conftest import FakeExtractor

UseExtractor = Callable[[IntentExtractor], TestClient]


def test_chat_returns_message_and_structured_intent(use_extractor: UseExtractor) -> None:
    fake = FakeExtractor(
        IntentResult(
            intent="book_appointment",
            reason="broken tooth",
            requested_date="tomorrow",
            time_preference="afternoon",
        )
    )
    client = use_extractor(fake)

    response = client.post("/chat", json={"message": "My tooth broke, can I come tomorrow afternoon?"})

    assert response.status_code == 200
    assert response.json() == {
        "message": "My tooth broke, can I come tomorrow afternoon?",
        "status": "received",
        "classification": {
            "intent": "book_appointment",
            "reason": "broken tooth",
            "requested_date": "tomorrow",
            "time_preference": "afternoon",
        },
    }
    assert fake.messages == ["My tooth broke, can I come tomorrow afternoon?"]


def test_chat_optional_fields_default_to_null(use_extractor: UseExtractor) -> None:
    client = use_extractor(FakeExtractor(IntentResult(intent="business_question")))
    body = client.post("/chat", json={"message": "Do you take Delta Dental?"}).json()
    assert body["classification"] == {
        "intent": "business_question",
        "reason": None,
        "requested_date": None,
        "time_preference": None,
    }


@pytest.mark.parametrize("message", ["", "   ", "\n\t "])
def test_chat_blank_message_is_rejected_without_calling_the_model(
    use_extractor: UseExtractor, message: str
) -> None:
    fake = FakeExtractor()
    client = use_extractor(fake)
    assert client.post("/chat", json={"message": message}).status_code == 422
    assert fake.messages == []


def test_chat_missing_message_field_is_rejected(use_extractor: UseExtractor) -> None:
    assert use_extractor(FakeExtractor()).post("/chat", json={}).status_code == 422


@pytest.mark.parametrize("error", [LLMProviderError("secret-timeout"), LLMOutputError("secret-bad-json")])
def test_chat_reports_502_not_success_when_ai_fails(use_extractor: UseExtractor, error: Exception) -> None:
    client = use_extractor(FakeExtractor(error=error))

    response = client.post("/chat", json={"message": "Book me a cleaning"})

    assert response.status_code == 502
    assert "classification" not in response.json()
    assert "received" not in response.text
    assert "secret-" not in response.text  # internal error text is not leaked


def test_chat_reports_503_when_api_key_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    get_settings.cache_clear()
    get_intent_extractor.cache_clear()
    try:
        response = TestClient(app).post("/chat", json={"message": "hello"})
    finally:
        get_settings.cache_clear()
        get_intent_extractor.cache_clear()
    assert response.status_code == 503


def test_chat_validation_error_wins_over_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    get_settings.cache_clear()
    get_intent_extractor.cache_clear()
    try:
        response = TestClient(app).post("/chat", json={"message": "  "})
    finally:
        get_settings.cache_clear()
        get_intent_extractor.cache_clear()
    assert response.status_code == 422
