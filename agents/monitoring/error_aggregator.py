"""ErrorAggregator agent collecting runtime exceptions, classifying root causes, and detecting repeating patterns."""

from __future__ import annotations

from collections import Counter
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from agents.monitoring.exceptions import ErrorAggregationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Monitoring.ErrorAggregator")


# ==============================================================================
# L5 Atomic Error Subagents
# ==============================================================================

class ErrorCollector(BaseAgent):
    """L5 agent ingesting raw exception payloads and normalizing metadata into standard structures."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ErrorCollector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        err = payload.get("error", "GeneralException: unexpected error")

        err_rec = {
            "error_id": f"ERR_{uuid.uuid4().hex[:8]}",
            "message": str(err),
            "source_agent": payload.get("source_agent", "UNKNOWN"),
            "timestamp": time.time(),
        }
        return {"status": "COMPLETED", "error_record": err_rec}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ErrorCollector %s cleaned up.", self.agent_id)


class ErrorClassifier(BaseAgent):
    """L5 agent categorizing errors into functional domains (Syntax, Security, Timeout, Resource, Unknown)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ErrorClassifier %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        msg = payload.get("message", "").lower()

        category = "UNKNOWN"
        if "syntax" in msg or "indentation" in msg or "parse" in msg:
            category = "SYNTAX"
        elif "auth" in msg or "permission" in msg or "token" in msg or "security" in msg:
            category = "SECURITY"
        elif "timeout" in msg or "timed out" in msg:
            category = "TIMEOUT"
        elif "ram" in msg or "memory" in msg or "cpu" in msg or "resource" in msg:
            category = "RESOURCE"

        return {"status": "COMPLETED", "category": category}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ErrorClassifier %s cleaned up.", self.agent_id)


class ErrorAnalyzer(BaseAgent):
    """L5 agent isolating primary failure origins and providing targeted debugging clues."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ErrorAnalyzer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        category = payload.get("category", "UNKNOWN")
        msg = payload.get("message", "")

        analysis = {
            "likely_cause": f"System fault attributed to {category.lower()} domain.",
            "actionable_suggestion": f"Inspect trace context for message '{msg[:60]}...'",
        }
        return {"status": "COMPLETED", "analysis": analysis}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ErrorAnalyzer %s cleaned up.", self.agent_id)


class ErrorPatternDetector(BaseAgent):
    """L5 agent computing cluster frequencies and flagging recurrent systematic regressions (>5 occurrences)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ErrorPatternDetector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        errors = payload.get("errors", [])
        threshold = payload.get("pattern_threshold", 5)

        categories = [e.get("category", "UNKNOWN") for e in errors]
        counts = Counter(categories)

        patterns = []
        for cat, cnt in counts.items():
            if cnt >= threshold:
                patterns.append({
                    "category": cat,
                    "count": cnt,
                    "recurrent_regression": True,
                })

        return {
            "status": "COMPLETED",
            "pattern_detected": len(patterns) > 0,
            "patterns": patterns,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ErrorPatternDetector %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 ErrorAggregator Agent
# ==============================================================================

class ErrorAggregator(BaseAgent):
    """L4 coordinator overseeing runtime exception collection, domain classification, and pattern mining."""

    def __init__(
        self,
        name: str = "ErrorAggregator",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "error_aggregation",
            "error_collection",
            "error_classification",
            "error_analysis",
            "error_pattern_detection",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M9_ERROR_AGGREGATOR",
        )

        self._collected_errors: List[Dict[str, Any]] = []
        self.collector: Optional[ErrorCollector] = None
        self.classifier: Optional[ErrorClassifier] = None
        self.analyzer: Optional[ErrorAnalyzer] = None
        self.pattern_detector: Optional[ErrorPatternDetector] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("record_error", self.record_error)
        self.register_tool("detect_patterns", self.detect_patterns)

    def _spawn_subagents(self) -> None:
        """Spawn atomic error aggregator subagents (Rule 1 & Rule 5)."""
        logger.info("ErrorAggregator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.collector = self.spawn_subagent(
            ErrorCollector,
            name="ErrorCollector",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.classifier = self.spawn_subagent(
            ErrorClassifier,
            name="ErrorClassifier",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.analyzer = self.spawn_subagent(
            ErrorAnalyzer,
            name="ErrorAnalyzer",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.pattern_detector = self.spawn_subagent(
            ErrorPatternDetector,
            name="ErrorPatternDetector",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ErrorAggregator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        err = payload.get("error", "SyntaxError: invalid syntax")
        rec = self.record_error(error=err)
        return {"status": "COMPLETED", "recorded_error": rec}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ErrorAggregator %s cleanup complete.", self.agent_id)

    def record_error(self, error: Any, source_agent: str = "UNKNOWN") -> Dict[str, Any]:
        """Ingest, categorize, and store runtime error."""
        p_env = {"payload": {"error": error, "source_agent": source_agent}}
        c_res = self.collector.process(p_env) if self.collector else {"error_record": {"message": str(error)}}
        rec = c_res.get("error_record", {})

        cls_env = {"payload": {"message": rec.get("message", "")}}
        cls_res = self.classifier.process(cls_env) if self.classifier else {"category": "UNKNOWN"}
        rec["category"] = cls_res.get("category", "UNKNOWN")

        ana_env = {"payload": {"category": rec["category"], "message": rec.get("message", "")}}
        ana_res = self.analyzer.process(ana_env) if self.analyzer else {"analysis": {}}
        rec["analysis"] = ana_res.get("analysis", {})

        self._collected_errors.append(rec)
        return rec

    def detect_patterns(self, pattern_threshold: int = 5) -> Dict[str, Any]:
        """Detect recurring error frequencies."""
        p_env = {"payload": {"errors": self._collected_errors, "pattern_threshold": pattern_threshold}}
        res = self.pattern_detector.process(p_env) if self.pattern_detector else {"patterns": []}
        return res
