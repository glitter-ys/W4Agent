from __future__ import annotations

import structlog

from agent.orchestrator import Orchestrator

logger = structlog.get_logger()


class AgentEngine:
    """Main entry point for the agent-based detection system.

    Wraps the LangGraph orchestrator and provides a simple interface
    for the task service to start detections.
    """

    def __init__(self, task_id: str, config: dict):
        self.task_id = task_id
        self.config = config
        self.orchestrator = Orchestrator(task_id=task_id, config=config)

    async def run(self, target_url: str) -> dict:
        """Run the full detection pipeline for a target URL."""
        logger.info("agent_engine_start", task_id=self.task_id, url=target_url)

        try:
            final_state = await self.orchestrator.run(target_url)
            logger.info(
                "agent_engine_complete",
                task_id=self.task_id,
                pages_tested=final_state.get("pages_tested", 0),
                issues_found=final_state.get("issues_found", 0),
            )
            return final_state

        except Exception as e:
            logger.error("agent_engine_error", task_id=self.task_id, error=str(e))
            raise
