from __future__ import annotations

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()


class JiraService:
    """Service for creating and syncing issues with Jira."""

    @staticmethod
    async def create_issue(
        summary: str,
        description: str,
        issue_type: str = "Bug",
        priority: str = "Medium",
        labels: list[str] | None = None,
    ) -> str | None:
        """Create a Jira issue and return the issue key."""
        if not settings.JIRA_BASE_URL or not settings.JIRA_API_TOKEN:
            logger.warning("jira_not_configured")
            return None

        url = f"{settings.JIRA_BASE_URL}/rest/api/3/issue"
        headers = {
            "Authorization": f"Bearer {settings.JIRA_API_TOKEN}",
            "Content-Type": "application/json",
        }

        payload = {
            "fields": {
                "project": {"key": settings.JIRA_PROJECT_KEY},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                },
                "issuetype": {"name": issue_type},
                "priority": {"name": priority},
            }
        }

        if labels:
            payload["fields"]["labels"] = labels

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                issue_key = data["key"]
                logger.info("jira_issue_created", key=issue_key)
                return issue_key
        except Exception as e:
            logger.error("jira_create_failed", error=str(e))
            return None

    @staticmethod
    def severity_to_jira_priority(severity: str) -> str:
        mapping = {
            "critical": "Highest",
            "major": "High",
            "minor": "Medium",
            "info": "Low",
        }
        return mapping.get(severity, "Medium")
