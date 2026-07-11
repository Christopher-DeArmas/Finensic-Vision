"""FastAPI application entry point.

Provides app metadata, a health check, and the full REST API under ``/api``.
The WebSocket stream and AI endpoints are added in later stages.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="AI-Powered Anti-Money-Laundering Investigation Platform (demo).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "name": settings.app_name,
        "version": __version__,
        "status": "ok",
        "ai_enabled": settings.ai_enabled,
    }


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "healthy"}


# REST API (customers, transactions, merchants, alerts, cases, dashboard, ...).
app.include_router(api_router)

# Stage 4: WebSocket /ws/transactions + streaming lifecycle hooks.
