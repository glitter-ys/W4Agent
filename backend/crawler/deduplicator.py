from __future__ import annotations

import hashlib
from typing import Any

import structlog

logger = structlog.get_logger()


class SemanticDeduplicator:
    """Deduplicates pages based on content similarity.

    Uses content hashing and structural comparison to identify
    pages that are semantically similar (e.g., different product
    pages with the same template).
    """

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self._content_hashes: dict[str, str] = {}  # url -> hash
        self._structural_signatures: dict[str, str] = {}  # url -> structure hash
        self._template_groups: dict[str, list[str]] = {}  # template_hash -> [urls]

    def compute_structural_signature(self, page_data: dict) -> str:
        """Compute a structural signature based on DOM structure.

        Pages with the same template (e.g., product pages) will have
        similar structural signatures even with different content.
        """
        # Build signature from element hierarchy
        headings = page_data.get("headings", [])
        forms = page_data.get("forms", [])
        landmarks = page_data.get("landmarks", [])
        images = page_data.get("images", [])

        signature_parts = [
            f"h:{len(headings)}",
            f"f:{len(forms)}",
            f"l:{len(landmarks)}",
            f"i:{len(images)}",
            # Heading structure
            ",".join(str(h.get("level", 0)) for h in headings),
            # Form structure
            ",".join(
                str(len(f.get("inputs", []))) for f in forms
            ),
            # Landmark types
            ",".join(l.get("role", "") for l in landmarks),
        ]

        signature = "|".join(signature_parts)
        return hashlib.md5(signature.encode()).hexdigest()[:12]

    def is_duplicate(self, url: str, page_data: dict) -> tuple[bool, str | None]:
        """Check if a page is a duplicate of an already-seen page.

        Returns (is_duplicate, original_url).
        """
        content_hash = page_data.get("content_hash", "")
        structural_sig = self.compute_structural_signature(page_data)

        # Check exact content match
        for existing_url, existing_hash in self._content_hashes.items():
            if existing_hash == content_hash and existing_url != url:
                logger.info("exact_duplicate", url=url, original=existing_url)
                return True, existing_url

        # Check structural similarity (same template)
        if structural_sig in self._template_groups:
            group = self._template_groups[structural_sig]
            if len(group) >= 3:
                # Already have enough examples of this template
                logger.info(
                    "template_duplicate",
                    url=url,
                    template_group_size=len(group),
                )
                return True, group[0]
            group.append(url)
        else:
            self._template_groups[structural_sig] = [url]

        # Store this page's data
        self._content_hashes[url] = content_hash
        self._structural_signatures[url] = structural_sig

        return False, None

    def get_template_groups(self) -> dict[str, list[str]]:
        """Get all detected template groups."""
        return {
            sig: urls for sig, urls in self._template_groups.items()
            if len(urls) > 1
        }

    @property
    def total_duplicates_skipped(self) -> int:
        return sum(max(0, len(urls) - 3) for urls in self._template_groups.values())
