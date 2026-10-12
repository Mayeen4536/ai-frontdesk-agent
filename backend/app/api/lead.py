"""Lead route. Thin: validate, delegate to the service, map failures to HTTP errors."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_lead_repository
from app.repositories.lead_repository import LeadPersistenceError, LeadRepository
from app.schemas.lead import LeadRequest, LeadResponse
from app.services.lead_service import create_lead as save_lead

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/lead", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(
    request: LeadRequest,
    repository: Annotated[LeadRepository, Depends(get_lead_repository)],
) -> LeadResponse:
    try:
        lead = save_lead(request, repository)
    except LeadPersistenceError as exc:
        # Log the cause type only: driver messages can echo row values (personal data).
        logger.error("Lead persistence failed: %s", type(exc.__cause__).__name__)
        raise HTTPException(status_code=503, detail="Lead could not be saved") from exc
    return LeadResponse.model_validate(lead)
