"""Application settings, read from environment variables.

Secrets never live in code or in the repo. Locally, put them in `backend/.env`
(git-ignored) and start the server with `uvicorn app.main:app --env-file .env`.
"""

import os
from dataclasses import dataclass, field
from functools import lru_cache

DEFAULT_MODEL = "claude-haiku-4-5"
DEFAULT_TIMEOUT_SECONDS = 20.0


@dataclass(frozen=True)
class Settings:
    # repr=False keeps secrets out of logs and tracebacks that print the settings object.
    anthropic_api_key: str | None = field(repr=False)
    llm_model: str
    llm_timeout_seconds: float
    database_url: str | None = field(default=None, repr=False)


@lru_cache
def get_settings() -> Settings:
    return Settings(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
        llm_model=os.environ.get("LLM_MODEL") or DEFAULT_MODEL,
        llm_timeout_seconds=float(os.environ.get("LLM_TIMEOUT_SECONDS") or DEFAULT_TIMEOUT_SECONDS),
        database_url=os.environ.get("DATABASE_URL") or None,
    )
