"""Chat route. Thin: validate, delegate to the service, map failures to HTTP errors."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_intent_extractor
from app.llm.base import IntentExtractor, LLMNotConfiguredError, LLMOutputError, LLMProviderError
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.intent_service import extract_intent

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    extractor: Annotated[IntentExtractor, Depends(get_intent_extractor)],
) -> ChatResponse:
    try:
        classification = await extract_intent(request.message, extractor)
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail="AI service is not configured") from exc
    except (LLMProviderError, LLMOutputError) as exc:
        raise HTTPException(status_code=502, detail="AI service failed to process the message") from exc
    return ChatResponse(message=request.message, classification=classification)
