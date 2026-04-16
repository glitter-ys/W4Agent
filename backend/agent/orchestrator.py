from __future__ import annotations

import json
from typing import Any, TypedDict, Annotated
from enum import Enum

from langgraph.graph import StateGraph, END
import structlog

from agent.agents.master_agent import MasterAgent
from agent.agents.crawler_agent import CrawlerAgent
from agent.agents.detector_agent import DetectorAgent
from agent.agents.reporter_agent import ReporterAgent
from agent.llm.provider import get_llm
from agent.memory.short_term import ShortTermMemory
from agent.memory.long_term import LongTermMemory
from app.config import settings
from app.services.notification_service import NotificationService
from crawler.adaptive_crawler import AdaptiveCrawler

logger = structlog.get_logger()


class PipelineState(TypedDict):
    """State shared across all nodes in the LangGraph pipeline."""
    task_id: str
    target_url: str
    config: dict
    pages_discovered: int
    pages_tested: int
    issues_found: int
    current_action: str
    current_url: str
    explored_urls: list[str]
    pending_urls: list[str]
    pending_test_urls: list[str]
    all_issues: list[dict]
    report_data: dict
    error: str | None
    iteration: int
    max_iterations: int


class Orchestrator:
    """Multi-agent orchestrator using LangGraph state machine.

    Controls the flow between Master, Crawler, Detector, and Reporter agents.
    """

    def __init__(self, task_id: str, config: dict):
        self.task_id = task_id
        self.config = config
        self.llm = get_llm()

        # Shared memory
        self.short_term_memory = ShortTermMemory()
        self.long_term_memory = LongTermMemory()

        # Shared crawler instance (reused across explore and test nodes)
        self.adaptive_crawler = AdaptiveCrawler(task_id=task_id, config=config)

        # Initialize agents
        self.master = MasterAgent(
            name="Master",
            llm=self.llm,
            task_id=task_id,
            short_term_memory=self.short_term_memory,
            long_term_memory=self.long_term_memory,
        )
        self.crawler = CrawlerAgent(
            name="Crawler",
            llm=self.llm,
            task_id=task_id,
            short_term_memory=self.short_term_memory,
            long_term_memory=self.long_term_memory,
        )
        self.detector = DetectorAgent(
            name="Detector",
            llm=self.llm,
            task_id=task_id,
            short_term_memory=self.short_term_memory,
            long_term_memory=self.long_term_memory,
        )
        self.reporter = ReporterAgent(
            name="Reporter",
            llm=self.llm,
            task_id=task_id,
            short_term_memory=self.short_term_memory,
            long_term_memory=self.long_term_memory,
        )

        # Build the state graph
        self.graph = self._build_graph()

    # How many pages to explore/test per node invocation before returning to the router
    EXPLORE_BATCH_SIZE = 5
    TEST_BATCH_SIZE = 3

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine for the detection pipeline."""
        graph = StateGraph(PipelineState)

        # Add nodes
        graph.add_node("route", self._route_node)
        graph.add_node("explore", self._explore_node)
        graph.add_node("test", self._test_node)
        graph.add_node("report", self._report_node)

        # Set entry point
        graph.set_entry_point("route")

        # Deterministic routing: route decides next step without LLM
        graph.add_conditional_edges(
            "route",
            self._deterministic_route,
            {
                "explore": "explore",
                "test": "test",
                "report": "report",
                "end": END,
            },
        )

        # After explore/test, go back to route (not LLM)
        graph.add_edge("explore", "route")
        graph.add_edge("test", "route")

        # After report, end
        graph.add_edge("report", END)

        return graph.compile()

    def _deterministic_route(self, state: PipelineState) -> str:
        """Pure deterministic routing — no LLM involved.

        Rules (in priority order):
        1. max_iterations reached → drain pending tests, then report
        2. pending_test_urls accumulated enough (>= TEST_BATCH_SIZE) → test
        3. pending_urls available and under page limit → explore
        4. pending_test_urls remaining (any) → test
        5. nothing left → report
        """
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", 50)
        pending_urls = state.get("pending_urls", [])
        pending_test_urls = state.get("pending_test_urls", [])
        explored_count = len(state.get("explored_urls", []))
        max_pages = state.get("config", {}).get("max_pages", 100)

        # Safety: prevent infinite loops
        if iteration >= max_iterations:
            logger.warning("max_iterations_reached", task_id=self.task_id, iteration=iteration)
            if pending_test_urls:
                return "test"
            return "report"

        # If tests have piled up, drain them first
        if len(pending_test_urls) >= self.TEST_BATCH_SIZE:
            return "test"

        # Still have URLs to explore and haven't hit page limit
        if pending_urls and explored_count < max_pages:
            return "explore"

        # No more exploration, but still have pages to test
        if pending_test_urls:
            return "test"

        # Everything done — generate report
        # Only allow report if we actually tested at least one page
        if state.get("pages_tested", 0) > 0:
            return "report"

        # Edge case: nothing was explored or tested (all URLs failed)
        return "end"

    async def _route_node(self, state: PipelineState) -> PipelineState:
        """Lightweight routing node — just increments iteration counter.

        LLM is only called at strategic checkpoints (e.g. mid-crawl strategy
        adjustment), not on every iteration.
        """
        state["iteration"] = state.get("iteration", 0) + 1

        action = self._deterministic_route(state)
        state["current_action"] = action.upper()

        logger.info(
            "route_decision",
            task_id=self.task_id,
            action=state["current_action"],
            iteration=state["iteration"],
            pending_urls=len(state.get("pending_urls", [])),
            pending_test_urls=len(state.get("pending_test_urls", [])),
            explored=len(state.get("explored_urls", [])),
            tested=state.get("pages_tested", 0),
        )

        await NotificationService.notify_agent_reasoning(
            task_id=self.task_id,
            agent_name="Master",
            reasoning=f"第{state['iteration']}轮调度决策: {state['current_action']} | "
                      f"已探索{len(state.get('explored_urls', []))}页, "
                      f"已检测{state.get('pages_tested', 0)}页, "
                      f"待探索{len(state.get('pending_urls', []))}个URL, "
                      f"待检测{len(state.get('pending_test_urls', []))}个URL, "
                      f"发现{state.get('issues_found', 0)}个问题",
        )

        return state

    async def _explore_node(self, state: PipelineState) -> PipelineState:
        """Crawler agent explores pages — processes up to EXPLORE_BATCH_SIZE URLs."""
        crawler = self.adaptive_crawler
        max_pages = state.get("config", {}).get("max_pages", 100)
        batch = 0

        while state["pending_urls"] and batch < self.EXPLORE_BATCH_SIZE:
            # Stop exploring if we've hit the page limit
            if len(state["explored_urls"]) >= max_pages:
                logger.info("page_limit_reached", task_id=self.task_id, limit=max_pages)
                break

            url_to_explore = state["pending_urls"][0]
            batch += 1

            try:
                result = await crawler.explore_page(url_to_explore)

                # Update state with discovered pages
                already_known = set(state["explored_urls"]) | set(state["pending_urls"])
                new_urls = [u for u in result.get("discovered_urls", []) if u not in already_known]
                state["explored_urls"].append(url_to_explore)
                state["pending_urls"] = [u for u in state["pending_urls"] if u != url_to_explore]
                state["pending_urls"].extend(new_urls)
                state["pending_test_urls"].append(url_to_explore)
                state["pages_discovered"] = len(state["explored_urls"]) + len(state["pending_urls"])

                logger.info(
                    "explored_page",
                    task_id=self.task_id,
                    url=url_to_explore,
                    new_urls_found=len(new_urls),
                    batch_progress=f"{batch}/{self.EXPLORE_BATCH_SIZE}",
                )

                await NotificationService.notify_agent_reasoning(
                    task_id=self.task_id,
                    agent_name="Crawler",
                    reasoning=f"探索页面: {url_to_explore} | "
                              f"发现{len(new_urls)}个新URL, "
                              f"批次进度 {batch}/{self.EXPLORE_BATCH_SIZE}",
                )

                # Update DB
                await self._update_task_progress(state)

            except Exception as e:
                logger.error("explore_error", url=url_to_explore, error=str(e))
                # Remove failed URL from pending
                state["pending_urls"] = [u for u in state["pending_urls"] if u != url_to_explore]

        return state

    async def _test_node(self, state: PipelineState) -> PipelineState:
        """Detector agent tests pages — processes up to TEST_BATCH_SIZE URLs."""
        from detector.detection_engine import DetectionEngine
        from detector.ai_based.visual_analyzer import VisualAnnotator

        batch = 0

        while state["pending_test_urls"] and batch < self.TEST_BATCH_SIZE:
            url_to_test = state["pending_test_urls"].pop(0)
            batch += 1

            try:
                # Get page data (uses cache from explore_node since same crawler instance)
                page_data = await self.adaptive_crawler.get_page_data(url_to_test)

                screenshot_path = page_data.get("screenshot_path")
                bounding_boxes = page_data.get("bounding_boxes", [])

                # Run rule-based detection
                detection_engine = DetectionEngine()
                rule_issues = await detection_engine.detect(page_data)

                # Run AI detection (includes multimodal vision if screenshot available)
                enable_vision = state["config"].get(
                    "enable_vision_detection", settings.ENABLE_VISION_DETECTION
                )
                ai_input = {
                    "url": url_to_test,
                    "title": page_data.get("title", ""),
                    "a11y_tree": page_data.get("a11y_tree", {}),
                    "html_snippet": page_data.get("html", "")[:5000],
                    "rule_issues": rule_issues,
                }
                if enable_vision and screenshot_path:
                    ai_input["screenshot_path"] = screenshot_path
                    ai_input["bounding_boxes"] = bounding_boxes

                ai_result = await self.detector.run(ai_input)

                # Store issues
                all_issues = ai_result.get("all_issues", [])
                state["all_issues"].extend(all_issues)
                state["issues_found"] = len(state["all_issues"])
                state["pages_tested"] += 1

                logger.info(
                    "tested_page",
                    task_id=self.task_id,
                    url=url_to_test,
                    issues_found=len(all_issues),
                    batch_progress=f"{batch}/{self.TEST_BATCH_SIZE}",
                )

                await NotificationService.notify_agent_reasoning(
                    task_id=self.task_id,
                    agent_name="Detector",
                    reasoning=f"检测页面: {url_to_test} | "
                              f"发现{len(all_issues)}个无障碍问题 "
                              f"(规则{len(rule_issues)}个, AI{len(ai_result.get('ai_issues', []))}个, "
                              f"视觉{len(ai_result.get('vision_issues', []))}个), "
                              f"批次进度 {batch}/{self.TEST_BATCH_SIZE}",
                )

                # Generate annotated screenshot (works for both rule-based and AI issues)
                annotated_path = None
                if screenshot_path and all_issues:
                    annotator = VisualAnnotator()
                    annotated_path = annotator.annotate_screenshot(
                        screenshot_path, all_issues, bounding_boxes
                    )

                # Save issues to DB (with bounding box context)
                await self._save_issues(
                    url_to_test, all_issues, bounding_boxes, annotated_path, screenshot_path
                )
                await self._update_task_progress(state)

            except Exception as e:
                logger.error("test_error", url=url_to_test, error=str(e))

        return state

    async def _report_node(self, state: PipelineState) -> PipelineState:
        """Reporter agent generates the final report."""
        # Calculate issue distribution
        issue_dist = {}
        for issue in state["all_issues"]:
            criterion = issue.get("wcag_criterion", "unknown")
            issue_dist[criterion] = issue_dist.get(criterion, 0) + 1

        severity_counts = {"critical": 0, "major": 0, "minor": 0, "info": 0}
        for issue in state["all_issues"]:
            sev = issue.get("severity", "minor")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Calculate score
        total_pages = state["pages_tested"]
        total_issues = state["issues_found"]
        if total_pages > 0:
            overall_score = max(0, 100 - (total_issues / total_pages * 10))
        else:
            overall_score = 0

        # Generate report via reporter agent
        report_result = await self.reporter.run({
            "total_pages": total_pages,
            "total_issues": total_issues,
            "critical_issues": severity_counts["critical"],
            "major_issues": severity_counts["major"],
            "minor_issues": severity_counts["minor"],
            "overall_score": round(overall_score, 1),
            "issue_distribution": issue_dist,
        })

        state["report_data"] = {
            "overall_score": round(overall_score, 1),
            "severity_counts": severity_counts,
            "summary": report_result.get("summary", ""),
            "recommendations": report_result.get("recommendations", []),
        }

        await NotificationService.notify_agent_reasoning(
            task_id=self.task_id,
            agent_name="Reporter",
            reasoning=f"生成检测报告 | 综合评分: {round(overall_score, 1)}, "
                      f"共检测{total_pages}个页面, 发现{total_issues}个问题 "
                      f"(严重{severity_counts['critical']}个, "
                      f"重要{severity_counts['major']}个, "
                      f"轻微{severity_counts['minor']}个)",
        )

        # Save report to DB
        await self._save_report(state)

        return state

    async def _update_task_progress(self, state: PipelineState):
        """Update task progress in the database."""
        from app.db.session import async_session_factory
        from app.models.task import Task
        from sqlalchemy import select

        async with async_session_factory() as db:
            result = await db.execute(select(Task).where(Task.id == self.task_id))
            task = result.scalar_one_or_none()
            if task:
                task.pages_discovered = state["pages_discovered"]
                task.pages_tested = state["pages_tested"]
                task.issues_found = state["issues_found"]
                await db.commit()

        # Notify via WebSocket
        from app.services.notification_service import NotificationService
        await NotificationService.notify_task_progress(self.task_id, {
            "pages_discovered": state["pages_discovered"],
            "pages_tested": state["pages_tested"],
            "issues_found": state["issues_found"],
            "current_url": state.get("current_url", ""),
        })

    async def _save_issues(
        self,
        url: str,
        issues: list[dict],
        bounding_boxes: list[dict] | None = None,
        annotated_screenshot_path: str | None = None,
        screenshot_path: str | None = None,
    ):
        """Save detected issues to the database."""
        from app.db.session import async_session_factory
        from app.models.issue import Issue
        from app.models.page import Page
        from sqlalchemy import select

        # Build selector -> bbox lookup
        bbox_lookup: dict[str, dict] = {}
        if bounding_boxes:
            for bb in bounding_boxes:
                selector = bb.get("selector")
                if selector and bb.get("bbox"):
                    bbox_lookup[selector] = bb["bbox"]

        async with async_session_factory() as db:
            # Find or create page record
            result = await db.execute(
                select(Page).where(Page.task_id == self.task_id, Page.url == url)
            )
            page = result.scalar_one_or_none()

            if not page:
                page = Page(task_id=self.task_id, url=url)
                db.add(page)
                await db.flush()

            # Update screenshot paths on the page
            if screenshot_path:
                page.screenshot_path = screenshot_path
            if annotated_screenshot_path:
                page.annotated_screenshot_path = annotated_screenshot_path

            for issue_data in issues:
                # Build context with bounding box if available
                context = issue_data.get("context") or {}
                selector = issue_data.get("element_selector")
                if selector and selector in bbox_lookup:
                    context["bounding_box"] = bbox_lookup[selector]

                issue = Issue(
                    task_id=self.task_id,
                    page_id=page.id,
                    wcag_criterion=issue_data.get("wcag_criterion", "unknown"),
                    wcag_level=issue_data.get("wcag_level", "A"),
                    rule_id=issue_data.get("rule_id", "ai-detection"),
                    severity=issue_data.get("severity", "minor"),
                    title=issue_data.get("title", "Untitled Issue"),
                    description=issue_data.get("description", ""),
                    recommendation=issue_data.get("recommendation"),
                    element_selector=issue_data.get("element_selector"),
                    element_html=issue_data.get("element_html"),
                    screenshot_path=screenshot_path,
                    detected_by=issue_data.get("detected_by", "ai"),
                    confidence=issue_data.get("confidence"),
                    context=context if context else None,
                )
                db.add(issue)

            await db.commit()

    async def _save_report(self, state: PipelineState):
        """Save the generated report to the database."""
        from app.services.report_service import ReportService
        from app.db.session import async_session_factory

        async with async_session_factory() as db:
            await ReportService.generate_report(self.task_id, db)

    async def run(self, target_url: str) -> PipelineState:
        """Execute the full detection pipeline."""
        initial_state: PipelineState = {
            "task_id": self.task_id,
            "target_url": target_url,
            "config": self.config,
            "pages_discovered": 0,
            "pages_tested": 0,
            "issues_found": 0,
            "current_action": "EXPLORE",
            "current_url": target_url,
            "explored_urls": [],
            "pending_urls": [target_url],
            "pending_test_urls": [],
            "all_issues": [],
            "report_data": {},
            "error": None,
            "iteration": 0,
            "max_iterations": self.config.get("max_pages", 100),
        }

        final_state = await self.graph.ainvoke(initial_state)
        return final_state
