"""Chat route. Acknowledges the message only; no LLM is connected yet."""

from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(message=request.message)
