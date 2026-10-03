"""Lead route. Validates and echoes the lead; nothing is persisted yet."""

from fastapi import APIRouter

from app.schemas.lead import LeadRequest, LeadResponse

router = APIRouter()


@router.post("/lead")
def create_lead(request: LeadRequest) -> LeadResponse:
    return LeadResponse(**request.model_dump())
