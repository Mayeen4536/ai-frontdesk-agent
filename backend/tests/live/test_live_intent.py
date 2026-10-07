"""Optional live check against the real provider. Deselected by default.

Run with: pytest -m live tests/live   (needs ANTHROPIC_API_KEY; costs a fraction of a cent)
"""

import os

import pytest

from app.core.config import get_settings
from app.llm.anthropic_client import AnthropicIntentExtractor

pytestmark = [
    pytest.mark.live,
    pytest.mark.anyio,
    pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set"),
]


async def test_live_urgent_booking_is_classified() -> None:
    extractor = AnthropicIntentExtractor.from_settings(get_settings())
    result = await extractor.extract_intent("My tooth broke and I want to come tomorrow afternoon.")
    assert result.intent == "book_appointment"
