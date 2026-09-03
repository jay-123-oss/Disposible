"""TraceCollector agent capturing distributed traces, parsing span trees, and generating latency breakdowns."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from agents.monitoring.exceptions import TraceCollectionError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Monitoring.TraceCollector")


# ==============================================================================
# L5 Atomic Trace Subagents
# ==============================================================================

class TraceExtractor(BaseAgent):
    """L5 agent extracting trace headers, span identifiers, and context propagations."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TraceExtractor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        op_name = payload.get("operation_name", "task_execution")
        parent_span_id = payload.get("parent_span_id")

        span = {
            "trace_id": payload.get("trace_id", f"TRC_{uuid.uuid4().hex[:12]}"),
            "span_id": f"SPN_{uuid.uuid4().hex[:8]}",
            "parent_span_id": parent_span_id,
            "operation": op_name,
            "start_time": time.time(),
            "duration_ms": payload.get("duration_ms", 35.0),
        }
        return {"status": "COMPLETED", "span": span}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TraceExtractor %s cleaned up.", self.agent_id)


class SpanAnalyzer(BaseAgent):
    """L5 agent validating span timing, finding orphaned spans, and checking critical paths."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SpanAnalyzer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        spans = payload.get("spans", [])

        total_duration = sum(s.get("duration_ms", 0.0) for s in spans)
        max_span = max(spans, key=lambda s: s.get("duration_ms", 0.0)) if spans else None

        return {
            "status": "COMPLETED",
            "span_count": len(spans),
            "total_span_duration_ms": total_duration,
            "bottleneck_span": max_span,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SpanAnalyzer %s cleaned up.", self.agent_id)


class TraceGraphGenerator(BaseAgent):
    """L5 agent constructing hierarchical DAG representations from parent-child span relations."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TraceGraphGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        spans = payload.get("spans", [])

        nodes = []
        edges = []
        for s in spans:
            s_id = s.get("span_id")
            p_id = s.get("parent_span_id")
            nodes.append({"id": s_id, "label": s.get("operation")})
            if p_id:
                edges.append({"from": p_id, "to": s_id})

        return {
            "status": "COMPLETED",
            "graph": {
                "nodes": nodes,
                "edges": edges,
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TraceGraphGenerator %s cleaned up.", self.agent_id)


class LatencyBreakdownGenerator(BaseAgent):
    """L5 agent computing per-subsystem percentage contribution to total trace duration."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LatencyBreakdownGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        spans = payload.get("spans", [])

        total = sum(s.get("duration_ms", 0.0) for s in spans)
        breakdown = {}
        for s in spans:
            op = s.get("operation", "unknown")
            dur = s.get("duration_ms", 0.0)
            pct = round((dur / max(total, 0.001)) * 100, 2)
            breakdown[op] = {"duration_ms": dur, "percentage": pct}

        return {
            "status": "COMPLETED",
            "total_ms": round(total, 2),
            "breakdown": breakdown,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("LatencyBreakdownGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 TraceCollector Agent
# ==============================================================================

class TraceCollector(BaseAgent):
    """L4 coordinator overseeing distributed trace collection, span tree parsing, and latency diagnostics."""

    def __init__(
        self,
        name: str = "TraceCollector",
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
            "trace_collection",
            "trace_extraction",
            "span_analysis",
            "trace_graph_generation",
            "latency_breakdown",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M10_TRACE_COLLECTOR",
        )

        self._spans: List[Dict[str, Any]] = []
        self.extractor: Optional[TraceExtractor] = None
        self.analyzer: Optional[SpanAnalyzer] = None
        self.graph_gen: Optional[TraceGraphGenerator] = None
        self.breakdown_gen: Optional[LatencyBreakdownGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("record_span", self.record_span)
        self.register_tool("analyze_trace", self.analyze_trace)

    def _spawn_subagents(self) -> None:
        """Spawn atomic trace subagents (Rule 1 & Rule 5)."""
        logger.info("TraceCollector %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.extractor = self.spawn_subagent(
            TraceExtractor,
            name="TraceExtractor",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.analyzer = self.spawn_subagent(
            SpanAnalyzer,
            name="SpanAnalyzer",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.graph_gen = self.spawn_subagent(
            TraceGraphGenerator,
            name="TraceGraphGenerator",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.breakdown_gen = self.spawn_subagent(
            LatencyBreakdownGenerator,
            name="LatencyBreakdownGenerator",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TraceCollector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        op = payload.get("operation", "lifecycle_execution")
        span = self.record_span(operation=op, duration_ms=payload.get("duration_ms", 25.0))
        analysis = self.analyze_trace()
        return {"status": "COMPLETED", "span": span, "trace_analysis": analysis}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TraceCollector %s cleanup complete.", self.agent_id)

    def record_span(
        self,
        operation: str,
        duration_ms: float = 10.0,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create and append span to trace buffer."""
        p_env = {
            "payload": {
                "operation_name": operation,
                "duration_ms": duration_ms,
                "trace_id": trace_id,
                "parent_span_id": parent_span_id,
            }
        }
        res = self.extractor.process(p_env) if self.extractor else {"span": {"operation": operation}}
        sp = res.get("span", {})
        self._spans.append(sp)
        return sp

    def analyze_trace(self) -> Dict[str, Any]:
        """Generate graph representation and latency breakdown of recorded spans."""
        p_env = {"payload": {"spans": self._spans}}

        ana_res = self.analyzer.process(p_env) if self.analyzer else {}
        graph_res = self.graph_gen.process(p_env) if self.graph_gen else {"graph": {}}
        break_res = self.breakdown_gen.process(p_env) if self.breakdown_gen else {"breakdown": {}}

        return {
            "analysis": ana_res,
            "graph": graph_res.get("graph"),
            "latency_breakdown": break_res,
        }
