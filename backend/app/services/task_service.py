from __future__ import annotations

import asyncio
import traceback

import structlog

from app.db.session import async_session_factory
from app.models.task import Task, TaskStatus
from sqlalchemy import select

logger = structlog.get_logger()


class TaskService:
    """Service for managing detection task lifecycle."""

    @staticmethod
    async def run_detection(task_id: str):
        """Main entry point for running a detection task.

        This is called as a background task and orchestrates the entire
        detection pipeline: agent engine -> crawler -> detector -> report.
        """
        logger.info("task_started", task_id=task_id)

        async with async_session_factory() as db:
            try:
                # Load task
                result = await db.execute(select(Task).where(Task.id == task_id))
                task = result.scalar_one_or_none()
                if not task:
                    logger.error("task_not_found", task_id=task_id)
                    return

                # Import here to avoid circular imports
                from agent.engine import AgentEngine

                # Initialize and run agent engine
                engine = AgentEngine(task_id=task_id, config=task.config or {})
                await engine.run(target_url=task.target_url)

                # Mark as completed
                task.status = TaskStatus.COMPLETED
                await db.commit()

                logger.info("task_completed", task_id=task_id)

                # Broadcast completion via WebSocket
                from app.api.ws.task_monitor import manager
                await manager.broadcast(task_id, {
                    "type": "task_completed",
                    "task_id": task_id,
                    "data": {
                        "pages_discovered": task.pages_discovered,
                        "pages_tested": task.pages_tested,
                        "issues_found": task.issues_found,
                    },
                })

            except asyncio.CancelledError:
                task.status = TaskStatus.CANCELLED
                await db.commit()
                logger.info("task_cancelled", task_id=task_id)

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error_message = f"{type(e).__name__}: {str(e)}"
                await db.commit()
                logger.error(
                    "task_failed",
                    task_id=task_id,
                    error=str(e),
                    traceback=traceback.format_exc(),
                )

                from app.api.ws.task_monitor import manager
                await manager.broadcast(task_id, {
                    "type": "task_failed",
                    "task_id": task_id,
                    "data": {"error": str(e)},
                })
