"""DriftDetector agent measuring performance, model accuracy, and behavioral output drift."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from agents.monitoring.exceptions import DriftDetectionError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Monitoring.DriftDetector")


# ==============================================================================
# L5 Atomic Drift Subagents
# ==============================================================================

class PerformanceDriftDetector(BaseAgent):
    """L5 agent detecting latency or throughput degradation compared to historical baselines."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PerformanceDriftDetector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        baseline = payload.get("baseline_latency_ms", 50.0)
        current = payload.get("current_latency_ms", 65.0)
        threshold = payload.get("performance_threshold", 20.0)

        drift_pct = ((current - baseline) / max(baseline, 1.0)) * 100
        drift_detected = drift_pct >= threshold

        return {
            "status": "COMPLETED",
            "type": "PERFORMANCE_DRIFT",
            "drift_percentage": round(drift_pct, 2),
            "drift_detected": drift_detected,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PerformanceDriftDetector %s cleaned up.", self.agent_id)


class AccuracyDriftDetector(BaseAgent):
    """L5 agent measuring code generation success rate or benchmark precision decay."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AccuracyDriftDetector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        baseline_acc = payload.get("baseline_accuracy", 0.96)
        current_acc = payload.get("current_accuracy", 0.88)
        threshold = payload.get("accuracy_threshold", 10.0)

        drop_pct = ((baseline_acc - current_acc) / max(baseline_acc, 0.01)) * 100
        drift_detected = drop_pct >= threshold

        return {
            "status": "COMPLETED",
            "type": "ACCURACY_DRIFT",
            "drop_percentage": round(drop_pct, 2),
            "drift_detected": drift_detected,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AccuracyDriftDetector %s cleaned up.", self.agent_id)


class BehaviorDriftDetector(BaseAgent):
    """L5 agent analyzing pattern shifts in generated code structures, styling, or output formats."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("BehaviorDriftDetector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        baseline_patterns = set(payload.get("baseline_patterns", ["pattern_a", "pattern_b"]))
        current_patterns = set(payload.get("current_patterns", ["pattern_a", "pattern_c"]))
        threshold = payload.get("behavior_threshold", 15.0)

        diff = len(baseline_patterns.symmetric_difference(current_patterns))
        total = len(baseline_patterns.union(current_patterns))
        deviation_pct = (diff / max(total, 1)) * 100
        drift_detected = deviation_pct >= threshold

        return {
            "status": "COMPLETED",
            "type": "BEHAVIOR_DRIFT",
            "deviation_percentage": round(deviation_pct, 2),
            "drift_detected": drift_detected,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("BehaviorDriftDetector %s cleaned up.", self.agent_id)


class DriftReporter(BaseAgent):
    """L5 agent synthesizing multidimensional drift evaluations into an actionable report."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DriftReporter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        reports = payload.get("drift_results", [])

        any_drift = any(r.get("drift_detected", False) for r in reports)
        summary = {
            "overall_drift_detected": any_drift,
            "evaluated_dimensions": len(reports),
            "timestamp": time.time(),
            "details": reports,
        }
        return {"status": "COMPLETED", "report": summary}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DriftReporter %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 DriftDetector Agent
# ==============================================================================

class DriftDetector(BaseAgent):
    """L4 coordinator overseeing performance, accuracy, and behavioral model drift analysis."""

    def __init__(
        self,
        name: str = "DriftDetector",
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
            "drift_detection",
            "performance_drift",
            "accuracy_drift",
            "behavior_drift",
            "drift_reporting",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M5_DRIFT_DETECTOR",
        )

        self.perf_drift: Optional[PerformanceDriftDetector] = None
        self.acc_drift: Optional[AccuracyDriftDetector] = None
        self.behav_drift: Optional[BehaviorDriftDetector] = None
        self.reporter: Optional[DriftReporter] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("detect_drift", self.detect_drift)

    def _spawn_subagents(self) -> None:
        """Spawn atomic drift subagents (Rule 1 & Rule 5)."""
        logger.info("DriftDetector %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.perf_drift = self.spawn_subagent(
            PerformanceDriftDetector,
            name="PerformanceDriftDetector",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.acc_drift = self.spawn_subagent(
            AccuracyDriftDetector,
            name="AccuracyDriftDetector",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.behav_drift = self.spawn_subagent(
            BehaviorDriftDetector,
            name="BehaviorDriftDetector",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.reporter = self.spawn_subagent(
            DriftReporter,
            name="DriftReporter",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DriftDetector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        drift_report = self.detect_drift(context=payload)
        return {"status": "COMPLETED", "drift_report": drift_report}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DriftDetector %s cleanup complete.", self.agent_id)

    def detect_drift(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run all drift detection checks and compile report."""
        ctx = context or {}
        p_env = {"payload": ctx}

        p_res = self.perf_drift.process(p_env) if self.perf_drift else {"drift_detected": False}
        a_res = self.acc_drift.process(p_env) if self.acc_drift else {"drift_detected": False}
        b_res = self.behav_drift.process(p_env) if self.behav_drift else {"drift_detected": False}

        eval_list = [p_res, a_res, b_res]
        rep_env = {"payload": {"drift_results": eval_list}}
        rep = self.reporter.process(rep_env) if self.reporter else {"report": {}}

        return rep.get("report", {})
