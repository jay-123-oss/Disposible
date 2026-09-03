"""LogAggregator agent collecting, indexing, searching, and visualizing distributed cluster logs.

Implements the complete Log Aggregator hierarchy (D14):
- L4 LogAggregator coordinator
- L5 atomic workers: LogCollector, LogIndexer, LogSearcher, LogVisualizer
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from distributed.exceptions import LogAggregationError

logger = logging.getLogger("FractalCore.Distributed.LogAggregator")


# ==============================================================================
# L5 Atomic Log Aggregator Subagents
# ==============================================================================

class LogCollector(BaseAgent):
    """L5 agent collecting structured log lines from individual node agents."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LogCollector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        node_id = task_envelope.get("node_id", "node-1")
        lines = task_envelope.get("lines", [])
        collected = []
        for line in lines:
            collected.append({
                "node_id": node_id,
                "message": line if isinstance(line, str) else line.get("message", ""),
                "level": line.get("level", "INFO") if isinstance(line, dict) else "INFO",
                "timestamp": time.time(),
            })
        return {"status": "COMPLETED", "collected_logs": collected, "count": len(collected)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("LogCollector %s cleaned up.", self.agent_id)


class LogIndexer(BaseAgent):
    """L5 agent tokenizing and organizing log entries by node, level, and timestamp."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LogIndexer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        logs = task_envelope.get("logs", [])
        index_by_level: Dict[str, List[Dict[str, Any]]] = {}
        for entry in logs:
            lvl = entry.get("level", "INFO")
            if lvl not in index_by_level:
                index_by_level[lvl] = []
            index_by_level[lvl].append(entry)
        return {"status": "COMPLETED", "index_by_level": index_by_level, "indexed_count": len(logs)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("LogIndexer %s cleaned up.", self.agent_id)


class LogSearcher(BaseAgent):
    """L5 agent querying indexed logs by keyword, level, or time window."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LogSearcher %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        logs = task_envelope.get("logs", [])
        query = task_envelope.get("query", "").lower()
        level = task_envelope.get("level")

        matches = []
        for entry in logs:
            if level and entry.get("level") != level:
                continue
            if query and query not in entry.get("message", "").lower():
                continue
            matches.append(entry)

        return {"status": "COMPLETED", "matches": matches, "match_count": len(matches)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("LogSearcher %s cleaned up.", self.agent_id)


class LogVisualizer(BaseAgent):
    """L5 agent formatting log statistics into ASCII distributions or JSON dashboard payloads."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LogVisualizer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        logs = task_envelope.get("logs", [])
        counts: Dict[str, int] = {}
        for l in logs:
            lvl = l.get("level", "INFO")
            counts[lvl] = counts.get(lvl, 0) + 1

        chart = [f"[{lvl}]: {'#' * count} ({count})" for lvl, count in counts.items()]
        return {"status": "COMPLETED", "counts": counts, "ascii_chart": "\n".join(chart)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("LogVisualizer %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 LogAggregator Agent
# ==============================================================================

class LogAggregator(BaseAgent):
    """L4 coordinator managing centralized distributed cluster logging and query facilities."""

    def __init__(
        self,
        name: str = "LogAggregator",
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
            "log_aggregator",
            "log_collector",
            "log_indexer",
            "log_searcher",
            "log_visualizer",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "D14_LOG_AGGREGATOR",
        )
        self.logs_store: List[Dict[str, Any]] = []

        self.collector: Optional[LogCollector] = None
        self.indexer: Optional[LogIndexer] = None
        self.searcher: Optional[LogSearcher] = None
        self.visualizer: Optional[LogVisualizer] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("ingest_logs", self.ingest_logs)
        self.register_tool("search_logs", self.search_logs)
        self.register_tool("get_log_dashboard", self.get_log_dashboard)

    def _spawn_subagents(self) -> None:
        """Spawn atomic log aggregator subagents (Rule 1 & Rule 5)."""
        logger.info("LogAggregator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.collector = self.spawn_subagent(LogCollector, name="LogCollector", max_depth=child_depth, resources_mb=32)
        self.indexer = self.spawn_subagent(LogIndexer, name="LogIndexer", max_depth=child_depth, resources_mb=32)
        self.searcher = self.spawn_subagent(LogSearcher, name="LogSearcher", max_depth=child_depth, resources_mb=32)
        self.visualizer = self.spawn_subagent(LogVisualizer, name="LogVisualizer", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LogAggregator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return self.search_logs(task_envelope.get("query", ""), task_envelope.get("level"))

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("LogAggregator %s cleaned up.", self.agent_id)

    def ingest_logs(self, node_id: str, lines: List[Any]) -> Dict[str, Any]:
        """Ingest log records from a node."""
        res = self.collector.process({"node_id": node_id, "lines": lines}) if self.collector else {
            "collected_logs": [{"node_id": node_id, "message": str(l), "level": "INFO"} for l in lines]
        }
        records = res.get("collected_logs", [])
        self.logs_store.extend(records)
        return {"ingested_count": len(records), "total_logs": len(self.logs_store)}

    def search_logs(self, query: str = "", level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search stored logs matching keyword and optional level filter."""
        res = self.searcher.process({"logs": self.logs_store, "query": query, "level": level}) if self.searcher else {
            "matches": [l for l in self.logs_store if query.lower() in l.get("message", "").lower()]
        }
        return res.get("matches", [])

    def get_log_dashboard(self) -> Dict[str, Any]:
        """Generate log level summary metrics and ASCII chart."""
        if self.visualizer:
            res = self.visualizer.process({"logs": self.logs_store})
            return {"counts": res.get("counts", {}), "chart": res.get("ascii_chart", "")}
        return {"counts": {}, "chart": ""}
