"""POST /lead behaviour. Uses in-memory SQLite and fake stores: no PostgreSQL, no production data."""

from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_lead_repository
from app.db.base import Base
from app.db.models import Lead
from app.main import app
from app.repositories.lead_repository import LeadPersistenceError, LeadRepository


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    def repository() -> Iterator[LeadRepository]:
        with session_factory() as session:
            yield LeadRepository(session)

    app.dependency_overrides[get_lead_repository] = repository
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_store() -> Iterator[Callable[[Any], TestClient]]:
    def install(store: Any) -> TestClient:
        app.dependency_overrides[get_lead_repository] = lambda: store
        return TestClient(app)

    yield install
    app.dependency_overrides.clear()


def saved_leads(session_factory: sessionmaker[Session]) -> list[Lead]:
    with session_factory() as session:
        return list(session.scalars(select(Lead)))


def test_valid_lead_is_persisted_and_saved_record_returned(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    payload = {"name": " Ada ", "phone": "555-0100", "email": "ada@example.com", "reason": "Cleaning"}
    response = client.post("/lead", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] >= 1
    assert body["created_at"]
    assert (body["name"], body["phone"], body["email"], body["reason"]) == (
        "Ada",
        "555-0100",
        "ada@example.com",
        "Cleaning",
    )
    rows = saved_leads(session_factory)
    assert len(rows) == 1
    assert rows[0].id == body["id"]


def test_lead_email_only_is_persisted(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    response = client.post("/lead", json={"name": "Ada", "email": "ada@example.com", "reason": "Cleaning"})
    assert response.status_code == 201
    assert response.json()["phone"] is None
    assert saved_leads(session_factory)[0].phone is None


def test_lead_phone_only_is_persisted(client: TestClient, session_factory: sessionmaker[Session]) -> None:
    response = client.post("/lead", json={"name": "Ada", "phone": "555-0100", "reason": "Cleaning"})
    assert response.status_code == 201
    assert response.json()["email"] is None
    assert saved_leads(session_factory)[0].email is None


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "Ada", "reason": "Cleaning"},
        {"name": "Ada", "phone": " ", "email": "", "reason": "Cleaning"},
        {"email": "ada@example.com", "reason": "Cleaning"},
        {"name": "Ada", "email": "ada@example.com"},
        {"name": "  ", "email": "ada@example.com", "reason": "Cleaning"},
    ],
    ids=["no-contact", "blank-contact", "missing-name", "missing-reason", "blank-name"],
)
def test_invalid_lead_is_rejected_and_not_persisted(
    client: TestClient, session_factory: sessionmaker[Session], payload: dict[str, str]
) -> None:
    assert client.post("/lead", json=payload).status_code == 422
    assert saved_leads(session_factory) == []


class FailingStore:
    def add(self, **_: Any) -> Lead:
        raise LeadPersistenceError("could not save lead")


def test_persistence_failure_returns_503_not_success(client_with_store: Callable[[Any], TestClient]) -> None:
    response = client_with_store(FailingStore()).post(
        "/lead", json={"name": "Ada", "email": "ada@example.com", "reason": "Cleaning"}
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "Lead could not be saved"}


def test_database_error_is_rolled_back_and_wrapped(session_factory: sessionmaker[Session]) -> None:
    """A real SQLAlchemy failure inside the repository becomes LeadPersistenceError, with nothing stored."""
    with session_factory() as session:

        def broken_commit() -> None:
            raise OperationalError("INSERT", {}, Exception("db down"))

        session.commit = broken_commit  # type: ignore[method-assign]
        with pytest.raises(LeadPersistenceError):
            LeadRepository(session).add(name="Ada", phone=None, email="a@b.co", reason="x")
    assert saved_leads(session_factory) == []


def test_missing_database_url_returns_503(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import get_settings
    from app.db.session import get_engine

    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    get_engine.cache_clear()
    try:
        response = TestClient(app).post("/lead", json={"name": "Ada", "email": "a@b.co", "reason": "x"})
    finally:
        get_settings.cache_clear()
        get_engine.cache_clear()
    assert response.status_code == 503
