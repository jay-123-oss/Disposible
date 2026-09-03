"""WebSocket connection manager and event broadcaster for the GUI Dashboard."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("FractalCore.GUI.WebSocket")


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts real-time telemetry."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept incoming client WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected. Total active: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove disconnected client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket client disconnected. Total active: %d", len(self.active_connections))

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        """Send message to a specific connection."""
        await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast real-time system event to all connected clients."""
        payload = json.dumps(message)
        dead_connections: List[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


ws_manager = ConnectionManager()
