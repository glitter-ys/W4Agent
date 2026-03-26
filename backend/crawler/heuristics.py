from __future__ import annotations

import math
from dataclasses import dataclass
from urllib.parse import urlparse

import structlog

logger = structlog.get_logger()


@dataclass
class PagePriority:
    url: str
    score: float
    reason: str


class HeuristicStrategy:
    """Heuristic-based page exploration prioritization.

    Assigns priority scores to URLs to guide the crawler toward
    pages most likely to have accessibility issues or represent
    important user flows.
    """

    # URL patterns that often indicate important pages
    HIGH_PRIORITY_PATTERNS = [
        "login", "signup", "register", "contact", "form",
        "checkout", "cart", "search", "settings", "profile",
        "account", "dashboard", "help", "accessibility",
    ]

    MEDIUM_PRIORITY_PATTERNS = [
        "about", "faq", "terms", "privacy", "blog",
        "news", "article", "product", "service",
    ]

    LOW_PRIORITY_PATTERNS = [
        "api", "feed", "rss", "sitemap", "robots",
        "admin", "wp-admin", "static",
    ]

    # File extensions to skip
    SKIP_EXTENSIONS = {
        ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg",
        ".mp3", ".mp4", ".avi", ".zip", ".tar", ".gz",
        ".css", ".js", ".woff", ".woff2", ".ttf", ".eot",
    }

    def should_skip(self, url: str) -> bool:
        """Check if a URL should be skipped entirely."""
        parsed = urlparse(url)
        path = parsed.path.lower()

        # Skip non-HTTP URLs
        if parsed.scheme not in ("http", "https", ""):
            return True

        # Skip file downloads
        for ext in self.SKIP_EXTENSIONS:
            if path.endswith(ext):
                return True

        return False

    def calculate_priority(
        self,
        url: str,
        depth: int,
        max_depth: int,
        parent_has_forms: bool = False,
        parent_has_issues: bool = False,
    ) -> PagePriority:
        """Calculate exploration priority score for a URL.

        Higher scores = higher priority.

        Factors:
        - URL pattern matching (form pages, login pages, etc.)
        - Depth penalty (deeper pages get lower priority)
        - Parent page characteristics
        - URL uniqueness
        """
        score = 50.0  # Base score
        reasons = []

        path = urlparse(url).path.lower()

        # Pattern matching
        for pattern in self.HIGH_PRIORITY_PATTERNS:
            if pattern in path:
                score += 30
                reasons.append(f"High-priority pattern: {pattern}")
                break

        for pattern in self.MEDIUM_PRIORITY_PATTERNS:
            if pattern in path:
                score += 15
                reasons.append(f"Medium-priority pattern: {pattern}")
                break

        for pattern in self.LOW_PRIORITY_PATTERNS:
            if pattern in path:
                score -= 20
                reasons.append(f"Low-priority pattern: {pattern}")
                break

        # Depth penalty: exponential decay
        depth_penalty = 10 * (depth / max(max_depth, 1))
        score -= depth_penalty
        if depth_penalty > 5:
            reasons.append(f"Depth penalty: -{depth_penalty:.1f}")

        # Bonus for pages whose parent had forms (likely multi-step flows)
        if parent_has_forms:
            score += 15
            reasons.append("Parent has forms")

        # Bonus for pages whose parent had issues (explore similar areas)
        if parent_has_issues:
            score += 10
            reasons.append("Parent had a11y issues")

        # Prefer shorter URLs (usually more important pages)
        url_length_penalty = max(0, (len(url) - 100) * 0.1)
        score -= url_length_penalty

        # Clamp to 0-100
        score = max(0, min(100, score))

        return PagePriority(
            url=url,
            score=score,
            reason="; ".join(reasons) if reasons else "Default priority",
        )

    def rank_urls(
        self,
        urls: list[str],
        depth: int,
        max_depth: int,
        **kwargs,
    ) -> list[PagePriority]:
        """Rank a list of URLs by exploration priority."""
        priorities = []
        for url in urls:
            if not self.should_skip(url):
                priority = self.calculate_priority(
                    url, depth, max_depth, **kwargs
                )
                priorities.append(priority)

        priorities.sort(key=lambda p: p.score, reverse=True)
        return priorities
