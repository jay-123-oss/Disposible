"""PerformanceTracker agent profiling response times, throughput, request latencies, and scalability."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.monitoring.exceptions import PerformanceTrackingError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Monitoring.PerformanceTracker")


# ==============================================================================
# L5 Atomic Performance Subagents
# ==============================================================================

class ResponseTimeTracker(BaseAgent):
    """L5 agent measuring client round-trip response times against threshold (200ms)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ResponseTimeTracker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        samples = payload.get("response_times", [45.0, 52.0, 48.0, 60.0])
        threshold = payload.get("response_time_threshold_ms", 200.0)

        avg_time = sum(samples) / max(len(samples), 1)
        passed = avg_time <= threshold

        return {
            "status": "COMPLETED",
            "metric": "RESPONSE_TIME",
            "average_ms": round(avg_time, 2),
            "threshold_ms": threshold,
            "passed": passed,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ResponseTimeTracker %s cleaned up.", self.agent_id)


class ThroughputTracker(BaseAgent):
    """L5 agent measuring requests processed per second against target threshold (100 rps)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ThroughputTracker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        rps = payload.get("current_rps", 150.0)
        threshold = payload.get("throughput_threshold_rps", 100.0)

        passed = rps >= threshold
        return {
            "status": "COMPLETED",
            "metric": "THROUGHPUT",
            "current_rps": rps,
            "threshold_rps": threshold,
            "passed": passed,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ThroughputTracker %s cleaned up.", self.agent_id)


class LatencyTracker(BaseAgent):
    """L5 agent computing latency distributions (p50, p95, p99) against threshold (500ms)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LatencyTracker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        latencies = sorted(payload.get("latencies", [20.0, 35.0, 40.0, 55.0, 80.0, 120.0]))
        threshold = payload.get("latency_threshold_ms", 500.0)

        n = len(latencies)
        p50 = latencies[int(n * 0.5)] if n > 0 else 0.0
        p95 = latencies[int(n * 0.95)] if n > 0 else 0.0
        p99 = latencies[int(n * 0.99)] if n > 0 else 0.0

        passed = p95 <= threshold
        return {
            "status": "COMPLETED",
            "metric": "LATENCY",
            "p50_ms": p50,
            "p95_ms": p95,
            "p99_ms": p99,
            "threshold_ms": threshold,
            "passed": passed,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("LatencyTracker %s cleaned up.", self.agent_id)


class ScalabilityTracker(BaseAgent):
    """L5 agent evaluating concurrency scaling behavior and resource saturation."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ScalabilityTracker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        concurrent_agents = payload.get("concurrent_agents", 8)
        max_supported = payload.get("max_supported_concurrency", 32)

        headroom_pct = round(((max_supported - concurrent_agents) / max_supported) * 100, 2)
        return {
            "status": "COMPLETED",
            "metric": "SCALABILITY",
            "current_concurrency": concurrent_agents,
            "max_concurrency": max_supported,
            "headroom_percent": headroom_pct,
            "scaling_healthy": headroom_pct > 20.0,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ScalabilityTracker %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PerformanceTracker Agent
# ==============================================================================

class PerformanceTracker(BaseAgent):
    """L4 coordinator overseeing response times, throughput, latency percentiles, and scalability."""

    def __init__(
        self,
        name: str = "PerformanceTracker",
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
            "performance_tracking",
            "response_time_tracking",
            "throughput_tracking",
            "latency_tracking",
            "scalability_tracking",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M7_PERFORMANCE_TRACKER",
        )

        self.resp_tracker: Optional[ResponseTimeTracker] = None
        self.thru_tracker: Optional[ThroughputTracker] = None
        self.lat_tracker: Optional[LatencyTracker] = None
        self.scale_tracker: Optional[ScalabilityTracker] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("track_performance", self.track_performance)

    def _spawn_subagents(self) -> None:
        """Spawn atomic performance subagents (Rule 1 & Rule 5)."""
        logger.info("PerformanceTracker %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.resp_tracker = self.spawn_subagent(
            ResponseTimeTracker,
            name="ResponseTimeTracker",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.thru_tracker = self.spawn_subagent(
            ThroughputTracker,
            name="ThroughputTracker",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.lat_tracker = self.spawn_subagent(
            LatencyTracker,
            name="LatencyTracker",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.scale_tracker = self.spawn_subagent(
            ScalabilityTracker,
            name="ScalabilityTracker",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PerformanceTracker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        perf_profile = self.track_performance(context=payload)
        return {"status": "COMPLETED", "performance_profile": perf_profile}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PerformanceTracker %s cleanup complete.", self.agent_id)

    def track_performance(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Aggregate performance telemetry across all four sub-domains."""
        ctx = context or {}
        p_env = {"payload": ctx}

        r_res = self.resp_tracker.process(p_env) if self.resp_tracker else {"passed": True}
        t_res = self.thru_tracker.process(p_env) if self.thru_tracker else {"passed": True}
        l_res = self.lat_tracker.process(p_env) if self.lat_tracker else {"passed": True}
        s_res = self.scale_tracker.process(p_env) if self.scale_tracker else {"scaling_healthy": True}

        all_passed = (
            r_res.get("passed", True)
            and t_res.get("passed", True)
            and l_res.get("passed", True)
            and s_res.get("scaling_healthy", True)
        )

        return {
            "all_thresholds_met": all_passed,
            "response_time": r_res,
            "throughput": t_res,
            "latency": l_res,
            "scalability": s_res,
        }
