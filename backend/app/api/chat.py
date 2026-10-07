"""Chat route. Thin: validates input, delegates to the classifier, returns the result."""

from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.classifier import classify_message

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(
        message=request.message,
        classification=classify_message(request.message),
    )
