from __future__ import annotations

import json
from datetime import datetime, timezone

import structlog

logger = structlog.get_logger()


class NotificationService:
    """Service for broadcasting real-time notifications via WebSocket."""

    @staticmethod
    async def notify_task_progress(task_id: str, data: dict):
        from app.api.ws.task_monitor import manager
        await manager.broadcast(task_id, {
            "type": "task_progress",
            "task_id": task_id,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    @staticmethod
    async def notify_page_discovered(task_id: str, url: str, depth: int):
        from app.api.ws.task_monitor import manager
        await manager.broadcast(task_id, {
            "type": "page_discovered",
            "task_id": task_id,
            "data": {"url": url, "depth": depth},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    @staticmethod
    async def notify_issue_found(task_id: str, issue_data: dict):
        from app.api.ws.task_monitor import manager
        await manager.broadcast(task_id, {
            "type": "issue_found",
            "task_id": task_id,
            "data": issue_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    @staticmethod
    async def notify_agent_reasoning(task_id: str, agent_name: str, reasoning: str):
        from app.api.ws.task_monitor import manager
        await manager.broadcast(task_id, {
            "type": "agent_reasoning",
            "task_id": task_id,
            "data": {"agent": agent_name, "reasoning": reasoning},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    @staticmethod
    async def notify_event_detected(task_id: str, event_type: str, action_taken: str):
        from app.api.ws.task_monitor import manager
        await manager.broadcast(task_id, {
            "type": "event_detected",
            "task_id": task_id,
            "data": {"event_type": event_type, "action_taken": action_taken},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
