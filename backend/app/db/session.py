"""Engine and session handling. The only place that builds a database connection."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


class DatabaseNotConfiguredError(Exception):
    """DATABASE_URL is not set."""


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    if not url:
        raise DatabaseNotConfiguredError("DATABASE_URL is not set")
    # pre_ping drops stale pooled connections instead of failing a request on them.
    return create_engine(url, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request, always closed."""
    with sessionmaker(bind=get_engine(), expire_on_commit=False)() as session:
        yield session
