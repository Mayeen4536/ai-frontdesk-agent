"""Lead persistence. The only code that talks to the leads table."""

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Lead


class LeadPersistenceError(Exception):
    """The lead could not be saved."""


class LeadRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, *, name: str, phone: str | None, email: str | None, reason: str) -> Lead:
        """Insert one lead in its own transaction and return the stored row (with id, created_at)."""
        lead = Lead(name=name, phone=phone, email=email, reason=reason)
        try:
            self._session.add(lead)
            self._session.commit()
            self._session.refresh(lead)
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise LeadPersistenceError("could not save lead") from exc
        return lead
