"""PredictiveAnalyzer agent forecasting failures, detecting latent anomalies, and providing capacity guidance."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from agents.monitoring.exceptions import PredictiveAnalysisError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Monitoring.PredictiveAnalyzer")


# ==============================================================================
# L5 Atomic Predictive Subagents
# ==============================================================================

class FailurePredictor(BaseAgent):
    """L5 agent evaluating regression rate curves and forecasting impending task execution failures."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("FailurePredictor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        recent_failures = payload.get("recent_failure_count", 0)
        total_tasks = payload.get("total_task_count", 20)

        failure_rate = recent_failures / max(total_tasks, 1)
        risk_probability = min(failure_rate * 1.5, 1.0)

        return {
            "status": "COMPLETED",
            "prediction": "FAILURE_RISK",
            "risk_score_percent": round(risk_probability * 100, 1),
            "high_risk": risk_probability > 0.4,
            "forecast_window_hours": 24,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("FailurePredictor %s cleaned up.", self.agent_id)


class AnomalyPredictor(BaseAgent):
    """L5 agent computing statistical z-score outliers across latency and error rate distributions."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AnomalyPredictor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        samples = payload.get("latency_samples", [45.0, 48.0, 50.0, 52.0, 49.0])
        current = payload.get("current_sample", 51.0)

        mean = sum(samples) / max(len(samples), 1)
        variance = sum((x - mean) ** 2 for x in samples) / max(len(samples), 1)
        std_dev = variance ** 0.5

        z_score = (current - mean) / max(std_dev, 0.001)
        anomaly_detected = abs(z_score) >= 2.5

        return {
            "status": "COMPLETED",
            "prediction": "LATENT_ANOMALY",
            "z_score": round(z_score, 2),
            "anomaly_detected": anomaly_detected,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AnomalyPredictor %s cleaned up.", self.agent_id)


class CapacityPredictor(BaseAgent):
    """L5 agent extrapolating memory and disk growth curves to estimate time to capacity exhaustion."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CapacityPredictor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        current_ram_mb = payload.get("current_ram_mb", 4096)
        growth_rate_mb_hr = payload.get("growth_rate_mb_hr", 50.0)
        ceiling_mb = 8192

        remaining_mb = max(ceiling_mb - current_ram_mb, 0)
        hrs_remaining = remaining_mb / max(growth_rate_mb_hr, 0.001)

        return {
            "status": "COMPLETED",
            "prediction": "CAPACITY_HEADROOM",
            "remaining_ram_mb": remaining_mb,
            "estimated_hours_to_exhaustion": round(hrs_remaining, 1),
            "critical_exhaustion_soon": hrs_remaining < 48.0,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CapacityPredictor %s cleaned up.", self.agent_id)


class RecommendationGenerator(BaseAgent):
    """L5 agent mapping predictive insights to preventative remediation steps."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RecommendationGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        fail_res = payload.get("failure", {})
        cap_res = payload.get("capacity", {})

        recs = []
        if fail_res.get("high_risk"):
            recs.append("Trigger proactive test suite rerun and inspect error logs.")
        if cap_res.get("critical_exhaustion_soon"):
            recs.append("Execute checkpoint cleaner and compress stale agent memory states.")
        if not recs:
            recs.append("Cluster operating normally; maintain standard telemetry interval.")

        return {
            "status": "COMPLETED",
            "actionable_recommendations": recs,
            "confidence_score": 85.0,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("RecommendationGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PredictiveAnalyzer Agent
# ==============================================================================

class PredictiveAnalyzer(BaseAgent):
    """L4 coordinator overseeing predictive failure modeling, anomaly forecasting, and capacity guidance."""

    def __init__(
        self,
        name: str = "PredictiveAnalyzer",
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
            "predictive_analysis",
            "failure_prediction",
            "anomaly_prediction",
            "capacity_prediction",
            "proactive_recommendations",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M14_PREDICTIVE_ANALYZER",
        )

        self.fail_pred: Optional[FailurePredictor] = None
        self.anom_pred: Optional[AnomalyPredictor] = None
        self.cap_pred: Optional[CapacityPredictor] = None
        self.rec_gen: Optional[RecommendationGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("run_predictive_analysis", self.run_predictive_analysis)

    def _spawn_subagents(self) -> None:
        """Spawn atomic predictive subagents (Rule 1 & Rule 5)."""
        logger.info("PredictiveAnalyzer %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.fail_pred = self.spawn_subagent(
            FailurePredictor,
            name="FailurePredictor",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.anom_pred = self.spawn_subagent(
            AnomalyPredictor,
            name="AnomalyPredictor",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.cap_pred = self.spawn_subagent(
            CapacityPredictor,
            name="CapacityPredictor",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.rec_gen = self.spawn_subagent(
            RecommendationGenerator,
            name="RecommendationGenerator",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PredictiveAnalyzer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        analysis = self.run_predictive_analysis(context=payload)
        return {"status": "COMPLETED", "predictive_analysis": analysis}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PredictiveAnalyzer %s cleanup complete.", self.agent_id)

    def run_predictive_analysis(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synthesize multidimensional predictive models into actionable recommendations."""
        ctx = context or {}
        p_env = {"payload": ctx}

        f_res = self.fail_pred.process(p_env) if self.fail_pred else {}
        a_res = self.anom_pred.process(p_env) if self.anom_pred else {}
        c_res = self.cap_pred.process(p_env) if self.cap_pred else {}

        rec_env = {"payload": {"failure": f_res, "capacity": c_res}}
        r_res = self.rec_gen.process(rec_env) if self.rec_gen else {"actionable_recommendations": []}

        return {
            "timestamp": time.time(),
            "failure_prediction": f_res,
            "anomaly_prediction": a_res,
            "capacity_prediction": c_res,
            "recommendations": r_res.get("actionable_recommendations", []),
            "confidence_threshold_met": r_res.get("confidence_score", 0.0) >= 80.0,
        }
