"""Tracks connected WebSocket clients and broadcasts events to all of them."""

from __future__ import annotations

import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger("sentinel.streaming")


class ConnectionManager:
    """Manages active WebSocket connections for the live transaction feed."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    @property
    def count(self) -> int:
        return len(self._connections)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("WS client connected (%d total)", self.count)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("WS client disconnected (%d total)", self.count)

    async def broadcast(self, message: dict) -> None:
        """Send a JSON message to every client; drop any that have died."""
        if not self._connections:
            return
        dead: list[WebSocket] = []
        # Snapshot to avoid mutation during iteration.
        for ws in list(self._connections):
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001 - client vanished mid-send
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)
