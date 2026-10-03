"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api import chat, health, lead


def create_app() -> FastAPI:
    """Build the FastAPI application and register its routers."""
    app = FastAPI(title="AI Frontdesk Agent")
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(lead.router)
    return app


app = create_app()
