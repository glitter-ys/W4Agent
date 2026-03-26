from __future__ import annotations

import os
import uuid
from typing import Any
from urllib.parse import urlparse

import structlog

from app.config import settings
from app.db.session import async_session_factory
from app.models.page import Page, PageStatus
from app.services.notification_service import NotificationService
from crawler.action_executor import BrowserPool, ActionExecutor
from crawler.page_analyzer import PageAnalyzer
from crawler.state_graph import ApplicationStateGraph, NodeStatus
from crawler.heuristics import HeuristicStrategy
from crawler.deduplicator import SemanticDeduplicator
from crawler.event_responder import EventResponder
from sqlalchemy import select

logger = structlog.get_logger()


class AdaptiveCrawler:
    """Self-adaptive web page crawler with intelligent exploration.

    Combines heuristic-based exploration, accessibility tree analysis,
    semantic deduplication, and event handling for efficient page discovery.
    """

    def __init__(self, task_id: str, config: dict):
        self.task_id = task_id
        self.config = config
        self.max_depth = config.get("max_depth", 5)
        self.max_pages = config.get("max_pages", 100)

        self.state_graph = ApplicationStateGraph()
        self.heuristic = HeuristicStrategy()
        self.deduplicator = SemanticDeduplicator()
        self.event_responder = EventResponder(task_id)
        self.page_analyzer = PageAnalyzer()

        self._page_data_cache: dict[str, dict] = {}

    async def explore_page(self, url: str) -> dict:
        """Explore a single page: navigate, analyze, discover links.

        Returns a dict with page data and discovered URLs.
        """
        page = await BrowserPool.get_page()
        executor = ActionExecutor(page)

        try:
            # Navigate to the URL
            nav_result = await executor.navigate(url)
            if not nav_result.get("success"):
                logger.warning("navigation_failed", url=url, error=nav_result.get("error"))
                self.state_graph.update_node_status(url, NodeStatus.FAILED)
                return {"url": url, "success": False, "discovered_urls": []}

            actual_url = nav_result["url"]

            # Handle unexpected events (popups, cookie banners, etc.)
            await self.event_responder.check_and_handle(page)

            # Analyze the page
            page_data = await self.page_analyzer.analyze(page)
            self._page_data_cache[url] = page_data

            # Check for duplicates
            is_dup, original_url = self.deduplicator.is_duplicate(url, page_data)
            if is_dup:
                self.state_graph.add_node(url, title=page_data["title"])
                self.state_graph.get_node(url).is_duplicate = True
                self.state_graph.update_node_status(url, NodeStatus.SKIPPED)
                logger.info("page_skipped_duplicate", url=url, original=original_url)
                return {"url": url, "success": True, "discovered_urls": [], "is_duplicate": True}

            # Update state graph
            node = self.state_graph.add_node(url, title=page_data["title"])
            self.state_graph.update_node_status(url, NodeStatus.EXPLORED)

            # Take screenshot
            screenshot_path = await self._take_screenshot(page, url)

            # Discover links
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            discovered_links = await executor.get_all_links(base_url)

            # Filter and prioritize discovered URLs
            current_depth = node.depth
            new_urls = []

            if current_depth < self.max_depth:
                priorities = self.heuristic.rank_urls(
                    discovered_links,
                    depth=current_depth + 1,
                    max_depth=self.max_depth,
                )

                for priority in priorities:
                    child_url = priority.url
                    if (
                        self.state_graph.get_node(child_url) is None
                        and self.state_graph.total_nodes < self.max_pages
                    ):
                        child_node = self.state_graph.add_node(
                            child_url,
                            depth=current_depth + 1,
                            parent_url=url,
                        )
                        self.state_graph.add_edge(url, child_url, action="link")
                        new_urls.append(child_url)

            # Save to database
            await self._save_page_to_db(url, page_data, screenshot_path)

            # Notify progress
            await NotificationService.notify_page_discovered(
                self.task_id, url, current_depth
            )

            logger.info(
                "page_explored",
                url=url,
                title=page_data["title"],
                new_links=len(new_urls),
                total_nodes=self.state_graph.total_nodes,
            )

            return {
                "url": url,
                "success": True,
                "title": page_data["title"],
                "discovered_urls": new_urls,
                "page_data": page_data,
                "screenshot_path": screenshot_path,
            }

        except Exception as e:
            logger.error("explore_error", url=url, error=str(e))
            self.state_graph.update_node_status(url, NodeStatus.FAILED)
            return {"url": url, "success": False, "discovered_urls": [], "error": str(e)}

        finally:
            await BrowserPool.release_page(page)

    async def get_page_data(self, url: str) -> dict:
        """Get cached page data for a URL, or re-analyze if not cached."""
        if url in self._page_data_cache:
            return self._page_data_cache[url]

        # Re-navigate and analyze
        page = await BrowserPool.get_page()
        executor = ActionExecutor(page)

        try:
            await executor.navigate(url)
            await self.event_responder.check_and_handle(page)
            page_data = await self.page_analyzer.analyze(page)
            self._page_data_cache[url] = page_data
            return page_data
        finally:
            await BrowserPool.release_page(page)

    async def _take_screenshot(self, page, url: str) -> str | None:
        """Take a screenshot and return the file path."""
        if not self.config.get("enable_screenshots", True):
            return None

        try:
            os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
            filename = f"{uuid.uuid4()}.png"
            path = os.path.join(settings.SCREENSHOT_DIR, filename)
            await page.screenshot(path=path, full_page=True)
            return path
        except Exception as e:
            logger.warning("screenshot_error", url=url, error=str(e))
            return None

    async def _save_page_to_db(self, url: str, page_data: dict, screenshot_path: str | None):
        """Save page record to database."""
        async with async_session_factory() as db:
            # Check if page already exists
            result = await db.execute(
                select(Page).where(Page.task_id == self.task_id, Page.url == url)
            )
            page_record = result.scalar_one_or_none()

            if not page_record:
                node = self.state_graph.get_node(url)
                page_record = Page(
                    task_id=self.task_id,
                    url=url,
                    title=page_data.get("title"),
                    status=PageStatus.COMPLETED,
                    depth=node.depth if node else 0,
                    content_hash=page_data.get("content_hash"),
                    screenshot_path=screenshot_path,
                    a11y_tree=page_data.get("a11y_tree"),
                )
                db.add(page_record)
            else:
                page_record.title = page_data.get("title")
                page_record.status = PageStatus.COMPLETED
                page_record.content_hash = page_data.get("content_hash")
                page_record.screenshot_path = screenshot_path
                page_record.a11y_tree = page_data.get("a11y_tree")

            await db.commit()
