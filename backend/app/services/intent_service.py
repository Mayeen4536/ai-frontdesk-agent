"""Application service: understand what a chat message is asking for.

Sits between the route and the LLM boundary. The model's answer is probabilistic;
everything after `IntentResult` is ordinary validated code.
"""

from app.llm.base import IntentExtractor
from app.schemas.intent import IntentResult


async def extract_intent(message: str, extractor: IntentExtractor) -> IntentResult:
    return await extractor.extract_intent(message)
