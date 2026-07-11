"""FastAPI application entry point.

Provides app metadata, a health check, the full REST API under ``/api``, and a
real-time WebSocket transaction stream at ``/ws/transactions``. AI endpoints
are added in a later stage.
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import api_router
from app.core.config import settings
from app.streaming import manager, simulator


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Start the transaction simulator on startup, stop it on shutdown."""
    await simulator.start()
    try:
        yield
    finally:
        await simulator.stop()


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="AI-Powered Anti-Money-Laundering Investigation Platform (demo).",
    lifespan=lifespan,
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


@app.get("/ws/status", tags=["streaming"])
def ws_status() -> dict:
    """Streaming diagnostics: connected clients and transactions emitted."""
    return {
        "connected_clients": manager.count,
        "transactions_emitted": simulator.emitted,
        "min_tps": settings.stream_min_tps,
        "max_tps": settings.stream_max_tps,
    }


# REST API (customers, transactions, merchants, alerts, cases, dashboard, ...).
app.include_router(api_router)


@app.websocket("/ws/transactions")
async def ws_transactions(websocket: WebSocket) -> None:
    """Live feed of streamed transactions and alerts.

    Clients connect and receive JSON messages of the form
    ``{"type": "transaction"|"alert", "data": {...}}``.
    """
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect inbound messages; this keeps the socket open and
            # detects disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:  # noqa: BLE001
        await manager.disconnect(websocket)
