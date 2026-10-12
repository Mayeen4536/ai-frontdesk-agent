"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import chat, health, lead
from app.db.session import DatabaseNotConfiguredError


def create_app() -> FastAPI:
    """Build the FastAPI application and register its routers."""
    app = FastAPI(title="AI Frontdesk Agent")
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(lead.router)

    @app.exception_handler(DatabaseNotConfiguredError)
    def database_not_configured(_: Request, __: Exception) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": "Database is not configured"})

    return app


app = create_app()
