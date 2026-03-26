from __future__ import annotations

import asyncio
import json
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger()

ws_router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time task monitoring."""

    def __init__(self):
        # task_id -> set of websocket connections
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        self._connections[task_id].add(websocket)
        logger.info("ws_connected", task_id=task_id)

    def disconnect(self, websocket: WebSocket, task_id: str):
        self._connections[task_id].discard(websocket)
        if not self._connections[task_id]:
            del self._connections[task_id]
        logger.info("ws_disconnected", task_id=task_id)

    async def broadcast(self, task_id: str, message: dict):
        """Broadcast message to all connections watching a specific task."""
        dead_connections = set()
        for connection in self._connections.get(task_id, set()):
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)

        # Cleanup dead connections
        for conn in dead_connections:
            self._connections[task_id].discard(conn)

    async def broadcast_all(self, message: dict):
        """Broadcast to all connected clients."""
        for task_id in list(self._connections.keys()):
            await self.broadcast(task_id, message)


# Global connection manager instance
manager = ConnectionManager()


@ws_router.websocket("/task/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task monitoring.

    Clients connect to watch a specific task's progress.
    Server pushes updates as the agent engine processes the task.
    """
    await manager.connect(websocket, task_id)
    try:
        while True:
            # Keep connection alive; handle client messages if needed
            data = await websocket.receive_text()
            msg = json.loads(data)

            # Handle client commands (e.g., pause, resume)
            if msg.get("command") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
    except Exception as e:
        logger.error("ws_error", task_id=task_id, error=str(e))
        manager.disconnect(websocket, task_id)
