from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeStatus(str, Enum):
    DISCOVERED = "discovered"
    EXPLORING = "exploring"
    EXPLORED = "explored"
    TESTING = "testing"
    TESTED = "tested"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class StateNode:
    """Represents a page/state in the application state graph."""
    url: str
    title: str = ""
    status: NodeStatus = NodeStatus.DISCOVERED
    depth: int = 0
    parent_url: str | None = None
    content_hash: str | None = None
    is_duplicate: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class StateEdge:
    """Represents a transition between two states (e.g., a link click)."""
    from_url: str
    to_url: str
    action: str = "navigate"  # navigate, click, submit, etc.
    element_selector: str | None = None
    element_text: str | None = None


class ApplicationStateGraph:
    """Directed graph representing the application's page structure.

    Used by the adaptive crawler to track explored pages and plan
    exploration strategies.
    """

    def __init__(self):
        self._nodes: dict[str, StateNode] = {}
        self._edges: list[StateEdge] = []
        self._adjacency: dict[str, list[str]] = {}

    def add_node(self, url: str, **kwargs) -> StateNode:
        """Add a page node to the graph."""
        if url not in self._nodes:
            node = StateNode(url=url, **kwargs)
            self._nodes[url] = node
            self._adjacency[url] = []
        return self._nodes[url]

    def add_edge(self, from_url: str, to_url: str, **kwargs):
        """Add a transition edge between two pages."""
        # Ensure both nodes exist
        self.add_node(from_url)
        self.add_node(to_url)

        edge = StateEdge(from_url=from_url, to_url=to_url, **kwargs)
        self._edges.append(edge)

        if to_url not in self._adjacency[from_url]:
            self._adjacency[from_url].append(to_url)

    def get_node(self, url: str) -> StateNode | None:
        return self._nodes.get(url)

    def update_node_status(self, url: str, status: NodeStatus):
        if url in self._nodes:
            self._nodes[url].status = status

    def get_unexplored_urls(self) -> list[str]:
        """Get all URLs that haven't been explored yet."""
        return [
            url for url, node in self._nodes.items()
            if node.status == NodeStatus.DISCOVERED and not node.is_duplicate
        ]

    def get_untested_urls(self) -> list[str]:
        """Get all URLs that have been explored but not tested."""
        return [
            url for url, node in self._nodes.items()
            if node.status == NodeStatus.EXPLORED and not node.is_duplicate
        ]

    def get_nodes_at_depth(self, depth: int) -> list[StateNode]:
        """Get all nodes at a specific depth."""
        return [node for node in self._nodes.values() if node.depth == depth]

    @property
    def total_nodes(self) -> int:
        return len(self._nodes)

    @property
    def explored_count(self) -> int:
        return sum(
            1 for n in self._nodes.values()
            if n.status in (NodeStatus.EXPLORED, NodeStatus.TESTING, NodeStatus.TESTED)
        )

    @property
    def tested_count(self) -> int:
        return sum(1 for n in self._nodes.values() if n.status == NodeStatus.TESTED)

    def to_dict(self) -> dict:
        """Serialize the graph for API/WebSocket transmission."""
        return {
            "nodes": [
                {
                    "url": n.url,
                    "title": n.title,
                    "status": n.status.value,
                    "depth": n.depth,
                    "is_duplicate": n.is_duplicate,
                }
                for n in self._nodes.values()
            ],
            "edges": [
                {
                    "from": e.from_url,
                    "to": e.to_url,
                    "action": e.action,
                }
                for e in self._edges
            ],
            "stats": {
                "total": self.total_nodes,
                "explored": self.explored_count,
                "tested": self.tested_count,
            },
        }
