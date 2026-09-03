"""TraceDepositor agent emitting stigmergic pheromone traces (attraction, danger, info) and decay rates."""

from __future__ import annotations

import logging
import math
import time
import uuid
from typing import Any, Dict, List, Optional

from agents.commstate.exceptions import TraceError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.CommState.TraceDepositor")


# ==============================================================================
# L5 Atomic Trace Depositor Subagents
# ==============================================================================

class AttractionTraceLeaver(BaseAgent):
    """L5 agent leaving positive attraction pheromones marking successful paths."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AttractionTraceLeaver %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        sig_id = f"sig_{uuid.uuid4().hex[:12]}"
        trace = {
            "signature_id": sig_id,
            "type": "attraction",
            "source_agent": payload.get("source_agent", "UNKNOWN"),
            "topic": payload.get("topic", "SUCCESS"),
            "payload": payload.get("data", {}),
            "strength": float(payload.get("strength", 1.0)),
            "created_at": time.time(),
        }
        return {"status": "COMPLETED", "trace": trace}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "trace" not in result:
            raise TraceError("AttractionTraceLeaver produced invalid trace.")
        return result

    def cleanup(self) -> None:
        logger.debug("AttractionTraceLeaver %s cleaned up.", self.agent_id)


class DangerTraceLeaver(BaseAgent):
    """L5 agent leaving repulsive danger pheromones marking failed paths or deadlocks."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DangerTraceLeaver %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        sig_id = f"sig_{uuid.uuid4().hex[:12]}"
        trace = {
            "signature_id": sig_id,
            "type": "danger",
            "source_agent": payload.get("source_agent", "UNKNOWN"),
            "topic": payload.get("topic", "FAILURE"),
            "payload": payload.get("data", {}),
            "strength": float(payload.get("strength", 1.0)),
            "created_at": time.time(),
        }
        return {"status": "COMPLETED", "trace": trace}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DangerTraceLeaver %s cleaned up.", self.agent_id)


class InfoTraceLeaver(BaseAgent):
    """L5 agent leaving neutral informational marks on artifacts and task boundaries."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("InfoTraceLeaver %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        sig_id = f"sig_{uuid.uuid4().hex[:12]}"
        trace = {
            "signature_id": sig_id,
            "type": "info",
            "source_agent": payload.get("source_agent", "UNKNOWN"),
            "topic": payload.get("topic", "ANNOTATION"),
            "payload": payload.get("data", {}),
            "strength": float(payload.get("strength", 0.8)),
            "created_at": time.time(),
        }
        return {"status": "COMPLETED", "trace": trace}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("InfoTraceLeaver %s cleaned up.", self.agent_id)


class TraceDecayer(BaseAgent):
    """L5 agent computing exponential half-life decay on environmental traces."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TraceDecayer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        traces = list(payload.get("traces", []))
        decay_rate = payload.get("decay_rate", 0.1)
        now = time.time()

        active_traces = []
        for t in traces:
            age = now - t.get("created_at", now)
            decayed_strength = t.get("strength", 1.0) * math.exp(-decay_rate * (age / 60.0))
            if decayed_strength > 0.05:
                t_copy = dict(t)
                t_copy["current_strength"] = round(decayed_strength, 3)
                active_traces.append(t_copy)

        return {"status": "COMPLETED", "active_traces": active_traces, "pruned": len(traces) - len(active_traces)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TraceDecayer %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 TraceDepositor Agent
# ==============================================================================

class TraceDepositor(BaseAgent):
    """L4 coordinator orchestrating stigmergic signal deposition across the multi-agent space."""

    def __init__(
        self,
        name: str = "TraceDepositor",
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
            "trace_deposition",
            "stigmergy_signaling",
            "attraction_marking",
            "danger_marking",
            "trace_decay_management",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C6_TRACE_DEPOSITOR",
        )

        self._trace_log: List[Dict[str, Any]] = []
        self.attr_leaver: Optional[AttractionTraceLeaver] = None
        self.dang_leaver: Optional[DangerTraceLeaver] = None
        self.info_leaver: Optional[InfoTraceLeaver] = None
        self.decayer: Optional[TraceDecayer] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("deposit_trace", self.deposit_trace)
        self.register_tool("decay_traces", self.decay_traces)

    def _spawn_subagents(self) -> None:
        """Spawn atomic trace depositor subagents (Rule 1 & Rule 5)."""
        logger.info("TraceDepositor %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.attr_leaver = self.spawn_subagent(
            AttractionTraceLeaver,
            name="AttractionTraceLeaver",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.dang_leaver = self.spawn_subagent(
            DangerTraceLeaver,
            name="DangerTraceLeaver",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.info_leaver = self.spawn_subagent(
            InfoTraceLeaver,
            name="InfoTraceLeaver",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.decayer = self.spawn_subagent(
            TraceDecayer,
            name="TraceDecayer",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TraceDepositor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        trace = self.deposit_trace(
            trace_type=payload.get("trace_type", "info"),
            source_agent=payload.get("source_agent", "SELF"),
            topic=payload.get("topic", "DEFAULT"),
            data=payload.get("data", {}),
        )
        return {"status": "COMPLETED", "trace": trace}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TraceDepositor %s cleanup complete.", self.agent_id)

    def deposit_trace(self, trace_type: str, source_agent: str, topic: str, data: Any = None, strength: float = 1.0) -> Dict[str, Any]:
        """Deposit new stigmergic trace into environment."""
        p_env = {"payload": {"source_agent": source_agent, "topic": topic, "data": data, "strength": strength}}
        if trace_type == "attraction" and self.attr_leaver:
            res = self.attr_leaver.process(p_env)
        elif trace_type == "danger" and self.dang_leaver:
            res = self.dang_leaver.process(p_env)
        elif self.info_leaver:
            res = self.info_leaver.process(p_env)
        else:
            res = {"trace": {"signature_id": "sig_fallback", "type": trace_type, "topic": topic}}

        trace = res["trace"]
        self._trace_log.append(trace)
        return trace

    def decay_traces(self, decay_rate: float = 0.1) -> List[Dict[str, Any]]:
        """Apply decay formula to environment traces and prune dead marks."""
        p_env = {"payload": {"traces": self._trace_log, "decay_rate": decay_rate}}
        res = self.decayer.process(p_env) if self.decayer else {"active_traces": self._trace_log}
        self._trace_log = res.get("active_traces", [])
        return self._trace_log
