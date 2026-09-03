"""TraceReader agent sensing stigmergic signals, evaluating route weights, and aggregating warnings."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.commstate.exceptions import TraceError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.CommState.TraceReader")


# ==============================================================================
# L5 Atomic Trace Reader Subagents
# ==============================================================================

class AttractionTraceReader(BaseAgent):
    """L5 agent sensing positive attraction traces for successful implementation patterns."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AttractionTraceReader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        traces = payload.get("traces", [])
        topic = payload.get("topic")

        filtered = [
            t for t in traces
            if t.get("type") == "attraction" and (not topic or t.get("topic") == topic)
        ]
        return {"status": "COMPLETED", "attraction_traces": filtered}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AttractionTraceReader %s cleaned up.", self.agent_id)


class DangerTraceReader(BaseAgent):
    """L5 agent sensing negative danger traces marking regression risks and anti-patterns."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DangerTraceReader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        traces = payload.get("traces", [])
        topic = payload.get("topic")

        filtered = [
            t for t in traces
            if t.get("type") == "danger" and (not topic or t.get("topic") == topic)
        ]
        return {"status": "COMPLETED", "danger_traces": filtered}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DangerTraceReader %s cleaned up.", self.agent_id)


class InfoTraceReader(BaseAgent):
    """L5 agent sensing informational traces and metadata annotations."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("InfoTraceReader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        traces = payload.get("traces", [])
        topic = payload.get("topic")

        filtered = [
            t for t in traces
            if t.get("type") == "info" and (not topic or t.get("topic") == topic)
        ]
        return {"status": "COMPLETED", "info_traces": filtered}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("InfoTraceReader %s cleaned up.", self.agent_id)


class TraceAnalyzer(BaseAgent):
    """L5 agent calculating composite desirability score for paths and evaluating safety."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TraceAnalyzer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        attractions = payload.get("attraction_traces", [])
        dangers = payload.get("danger_traces", [])

        attr_weight = sum(t.get("current_strength", t.get("strength", 1.0)) for t in attractions)
        danger_weight = sum(t.get("current_strength", t.get("strength", 1.0)) for t in dangers)

        # Net desirability score
        net_score = round(attr_weight - (danger_weight * 2.0), 2)
        safe_to_proceed = danger_weight == 0.0 or net_score > 0.0

        return {
            "status": "COMPLETED",
            "net_score": net_score,
            "attr_weight": attr_weight,
            "danger_weight": danger_weight,
            "safe_to_proceed": safe_to_proceed,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TraceAnalyzer %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 TraceReader Agent
# ==============================================================================

class TraceReader(BaseAgent):
    """L4 coordinator sensing environmental stigmergic pheromones and analyzing path safety."""

    def __init__(
        self,
        name: str = "TraceReader",
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
            "trace_reading",
            "stigmergy_sensing",
            "path_weight_analysis",
            "danger_detection",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C7_TRACE_READER",
        )

        self.attr_reader: Optional[AttractionTraceReader] = None
        self.dang_reader: Optional[DangerTraceReader] = None
        self.info_reader: Optional[InfoTraceReader] = None
        self.analyzer: Optional[TraceAnalyzer] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("sense_traces", self.sense_traces)

    def _spawn_subagents(self) -> None:
        """Spawn atomic trace reader subagents (Rule 1 & Rule 5)."""
        logger.info("TraceReader %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.attr_reader = self.spawn_subagent(
            AttractionTraceReader,
            name="AttractionTraceReader",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.dang_reader = self.spawn_subagent(
            DangerTraceReader,
            name="DangerTraceReader",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.info_reader = self.spawn_subagent(
            InfoTraceReader,
            name="InfoTraceReader",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.analyzer = self.spawn_subagent(
            TraceAnalyzer,
            name="TraceAnalyzer",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TraceReader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        analysis = self.sense_traces(traces=payload.get("traces", []), topic=payload.get("topic"))
        return {"status": "COMPLETED", "analysis": analysis}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TraceReader %s cleanup complete.", self.agent_id)

    def sense_traces(self, traces: List[Dict[str, Any]], topic: Optional[str] = None) -> Dict[str, Any]:
        """Filter environmental traces by category and compute safety scores."""
        p_env = {"payload": {"traces": traces, "topic": topic}}
        a_res = self.attr_reader.process(p_env) if self.attr_reader else {"attraction_traces": []}
        d_res = self.dang_reader.process(p_env) if self.dang_reader else {"danger_traces": []}
        i_res = self.info_reader.process(p_env) if self.info_reader else {"info_traces": []}

        attrs = a_res.get("attraction_traces", [])
        dangs = d_res.get("danger_traces", [])

        eval_env = {"payload": {"attraction_traces": attrs, "danger_traces": dangs}}
        res_anal = self.analyzer.process(eval_env) if self.analyzer else {"safe_to_proceed": True}

        return {
            "attractions": attrs,
            "dangers": dangs,
            "infos": i_res.get("info_traces", []),
            "evaluation": res_anal,
            "safe": res_anal.get("safe_to_proceed", True),
        }
