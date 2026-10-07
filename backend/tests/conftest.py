from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_intent_extractor
from app.llm.base import IntentExtractor
from app.main import app
from app.schemas.intent import IntentResult


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class FakeExtractor:
    """Stands in for the LLM: returns a canned result or raises a canned error."""

    def __init__(self, result: IntentResult | None = None, error: Exception | None = None) -> None:
        self.result = result or IntentResult(intent="unknown")
        self.error = error
        self.messages: list[str] = []

    async def extract_intent(self, message: str) -> IntentResult:
        self.messages.append(message)
        if self.error:
            raise self.error
        return self.result


@pytest.fixture
def use_extractor() -> Iterator[Callable[[IntentExtractor], TestClient]]:
    """Install a fake extractor for the app and return a TestClient. Cleans up after."""

    def install(extractor: IntentExtractor) -> TestClient:
        app.dependency_overrides[get_intent_extractor] = lambda: extractor
        return TestClient(app)

    yield install
    app.dependency_overrides.clear()
