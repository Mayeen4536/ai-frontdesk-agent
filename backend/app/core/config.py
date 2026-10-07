"""Application settings, read from environment variables.

Secrets never live in code or in the repo. Locally, put them in `backend/.env`
(git-ignored) and start the server with `uvicorn app.main:app --env-file .env`.
"""

import os
from dataclasses import dataclass
from functools import lru_cache

DEFAULT_MODEL = "claude-haiku-4-5"
DEFAULT_TIMEOUT_SECONDS = 20.0


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str | None
    llm_model: str
    llm_timeout_seconds: float


@lru_cache
def get_settings() -> Settings:
    return Settings(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
        llm_model=os.environ.get("LLM_MODEL") or DEFAULT_MODEL,
        llm_timeout_seconds=float(os.environ.get("LLM_TIMEOUT_SECONDS") or DEFAULT_TIMEOUT_SECONDS),
    )
