"""PluginMarketplace agent handling plugin discovery, search, recommendations, ratings, and reviews.

Implements the complete Plugin Marketplace hierarchy (P11):
- L4 PluginMarketplace coordinator
- L5 atomic workers: PluginSearcher, PluginRecommender, PluginRater, PluginReviewer
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from plugins.exceptions import PluginMarketplaceError


logger = logging.getLogger("FractalCore.PluginSystem.PluginMarketplace")


# ==============================================================================
# L5 Atomic Plugin Marketplace Subagents
# ==============================================================================

class PluginSearcher(BaseAgent):
    """L5 agent searching the marketplace index for plugins by keyword."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginSearcher %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        query = task_envelope.get("query", "").lower()
        catalog = task_envelope.get("catalog", [])
        results = [entry for entry in catalog if query in entry.get("name", "").lower() or query in entry.get("description", "").lower()]
        return {"status": "COMPLETED", "query": query, "results": results, "result_count": len(results)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginSearcher %s cleaned up.", self.agent_id)


class PluginRecommender(BaseAgent):
    """L5 agent recommending plugins based on usage profiles and ratings."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginRecommender %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        catalog = task_envelope.get("catalog", [])
        top = sorted(catalog, key=lambda e: e.get("rating", 0), reverse=True)[:3]
        return {"status": "COMPLETED", "recommendations": [e.get("name") for e in top], "count": len(top)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginRecommender %s cleaned up.", self.agent_id)


class PluginRater(BaseAgent):
    """L5 agent recording numeric ratings for plugins."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginRater %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugin = task_envelope.get("plugin_name", "")
        rating = task_envelope.get("rating", 5)
        ratings = task_envelope.get("ratings", {})
        ratings[plugin] = rating
        return {"status": "COMPLETED", "plugin_name": plugin, "rating": rating, "ratings": ratings, "rated": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginRater %s cleaned up.", self.agent_id)


class PluginReviewer(BaseAgent):
    """L5 agent storing textual reviews for plugins."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginReviewer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugin = task_envelope.get("plugin_name", "")
        review = task_envelope.get("review", "")
        reviews = task_envelope.get("reviews", {})
        reviews[plugin] = review
        return {"status": "COMPLETED", "plugin_name": plugin, "review_saved": True, "reviews": reviews}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginReviewer %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PluginMarketplace Agent
# ==============================================================================

class PluginMarketplace(BaseAgent):
    """L4 coordinator orchestrating search, recommendation, rating, and review services."""

    def __init__(
        self,
        name: str = "PluginMarketplace",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "plugin_marketplace",
            "plugin_searcher",
            "plugin_recommender",
            "plugin_rater",
            "plugin_reviewer",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P11_PLUGIN_MARKETPLACE",
        )
        self.catalog: List[Dict[str, Any]] = [
            {"name": "code-formatter", "rating": 4.8, "description": "Auto-formats generated code"},
            {"name": "security-scanner", "rating": 4.9, "description": "Scans for vulnerabilities"},
            {"name": "test-generator", "rating": 4.7, "description": "Generates unit tests"},
        ]
        self.ratings: Dict[str, int] = {}
        self.reviews: Dict[str, str] = {}
        self.searcher: Optional[PluginSearcher] = None
        self.recommender: Optional[PluginRecommender] = None
        self.rater: Optional[PluginRater] = None
        self.reviewer: Optional[PluginReviewer] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("browse_marketplace", self.browse_marketplace)

    def _spawn_subagents(self) -> None:
        """Spawn atomic marketplace subagents (Rule 1 & Rule 5)."""
        logger.info("PluginMarketplace %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.searcher = self.spawn_subagent(PluginSearcher, name="PluginSearcher", max_depth=child_depth, resources_mb=32)
        self.recommender = self.spawn_subagent(PluginRecommender, name="PluginRecommender", max_depth=child_depth, resources_mb=32)
        self.rater = self.spawn_subagent(PluginRater, name="PluginRater", max_depth=child_depth, resources_mb=32)
        self.reviewer = self.spawn_subagent(PluginReviewer, name="PluginReviewer", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginMarketplace %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.browse_marketplace(payload.get("query", ""))
        return {"status": "COMPLETED", "marketplace": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginMarketplace %s cleanup complete.", self.agent_id)

    def browse_marketplace(self, query: str = "") -> Dict[str, Any]:
        """Search + recommend plugins, returning combined marketplace view."""
        logger.info("Browsing marketplace for '%s'...", query)
        search = self.searcher.process({"query": query, "catalog": self.catalog}) if self.searcher else {"results": []}
        recs = self.recommender.process({"catalog": self.catalog}) if self.recommender else {"recommendations": []}
        return {
            "query": query,
            "search_results": search.get("results", []),
            "recommendations": recs.get("recommendations", []),
            "catalog_size": len(self.catalog),
            "ratings": self.ratings,
            "reviews": self.reviews,
        }

    def rate_plugin(self, plugin_name: str, rating: int) -> Dict[str, Any]:
        """Rate a plugin (1-5 stars)."""
        result = self.rater.process({"plugin_name": plugin_name, "rating": rating, "ratings": self.ratings}) if self.rater else {"rated": False}
        return result

    def review_plugin(self, plugin_name: str, review: str) -> Dict[str, Any]:
        """Store a textual review for a plugin."""
        result = self.reviewer.process({"plugin_name": plugin_name, "review": review, "reviews": self.reviews}) if self.reviewer else {"review_saved": False}
        return result