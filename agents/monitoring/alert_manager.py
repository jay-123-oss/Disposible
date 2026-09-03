"""AlertManager agent evaluating thresholds, classifying alert severity, and executing escalation policies."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from agents.monitoring.exceptions import AlertError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Monitoring.AlertManager")


# ==============================================================================
# L5 Atomic Alert Subagents
# ==============================================================================

class CriticalAlertGenerator(BaseAgent):
    """L5 agent synthesizing high-severity critical alarms for outages or threshold violations (>90%)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CriticalAlertGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        title = payload.get("title", "Critical Threshold Breach")
        metric_value = payload.get("metric_value", 95.0)

        alert = {
            "alert_id": f"CRIT_{uuid.uuid4().hex[:8]}",
            "severity": "CRITICAL",
            "title": title,
            "metric_value": metric_value,
            "created_at": time.time(),
            "status": "FIRING",
        }
        return {"status": "COMPLETED", "alert": alert}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CriticalAlertGenerator %s cleaned up.", self.agent_id)


class WarningAlertGenerator(BaseAgent):
    """L5 agent generating intermediate alarms for degradation or threshold breaches (>70%)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("WarningAlertGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        title = payload.get("title", "Resource Warning")
        metric_value = payload.get("metric_value", 75.0)

        alert = {
            "alert_id": f"WARN_{uuid.uuid4().hex[:8]}",
            "severity": "WARNING",
            "title": title,
            "metric_value": metric_value,
            "created_at": time.time(),
            "status": "FIRING",
        }
        return {"status": "COMPLETED", "alert": alert}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("WarningAlertGenerator %s cleaned up.", self.agent_id)


class InfoAlertGenerator(BaseAgent):
    """L5 agent generating informational telemetry alerts for notable lifecycle occurrences (>50%)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("InfoAlertGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        title = payload.get("title", "Routine Informational Event")
        metric_value = payload.get("metric_value", 55.0)

        alert = {
            "alert_id": f"INFO_{uuid.uuid4().hex[:8]}",
            "severity": "INFO",
            "title": title,
            "metric_value": metric_value,
            "created_at": time.time(),
            "status": "FIRING",
        }
        return {"status": "COMPLETED", "alert": alert}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("InfoAlertGenerator %s cleaned up.", self.agent_id)


class AlertEscalator(BaseAgent):
    """L5 agent bumping unacknowledged warnings to critical when unhandled beyond escalation interval."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AlertEscalator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        alert = payload.get("alert", {})
        escalation_interval = payload.get("escalation_interval", 300)

        age = time.time() - alert.get("created_at", time.time())
        should_escalate = age >= escalation_interval and alert.get("severity") != "CRITICAL"

        escalated_alert = dict(alert)
        if should_escalate:
            escalated_alert["severity"] = "CRITICAL"
            escalated_alert["escalated"] = True
            escalated_alert["escalated_at"] = time.time()

        return {
            "status": "COMPLETED",
            "escalated": should_escalate,
            "alert": escalated_alert,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AlertEscalator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 AlertManager Agent
# ==============================================================================

class AlertManager(BaseAgent):
    """L4 coordinator overseeing threshold evaluations, alert generation, and automated escalation."""

    def __init__(
        self,
        name: str = "AlertManager",
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
            "alert_management",
            "critical_alerting",
            "warning_alerting",
            "info_alerting",
            "alert_escalation",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M4_ALERT_MANAGER",
        )

        self.crit_gen: Optional[CriticalAlertGenerator] = None
        self.warn_gen: Optional[WarningAlertGenerator] = None
        self.info_gen: Optional[InfoAlertGenerator] = None
        self.escalator: Optional[AlertEscalator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("evaluate_metric", self.evaluate_metric)
        self.register_tool("escalate_alert", self.escalate_alert)

    def _spawn_subagents(self) -> None:
        """Spawn atomic alert subagents (Rule 1 & Rule 5)."""
        logger.info("AlertManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.crit_gen = self.spawn_subagent(
            CriticalAlertGenerator,
            name="CriticalAlertGenerator",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.warn_gen = self.spawn_subagent(
            WarningAlertGenerator,
            name="WarningAlertGenerator",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.info_gen = self.spawn_subagent(
            InfoAlertGenerator,
            name="InfoAlertGenerator",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.escalator = self.spawn_subagent(
            AlertEscalator,
            name="AlertEscalator",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AlertManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        metric_name = payload.get("metric_name", "cpu_percent")
        metric_val = payload.get("metric_value", 75.0)

        alert = self.evaluate_metric(metric_name=metric_name, value=metric_val)
        return {"status": "COMPLETED", "evaluated_alert": alert}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AlertManager %s cleanup complete.", self.agent_id)

    def evaluate_metric(
        self,
        metric_name: str,
        value: float,
        critical_threshold: float = 90.0,
        warning_threshold: float = 70.0,
        info_threshold: float = 50.0,
    ) -> Optional[Dict[str, Any]]:
        """Evaluate numeric metric against alert thresholds."""
        if value >= critical_threshold:
            p_env = {"payload": {"title": f"Critical breach on {metric_name}", "metric_value": value}}
            res = self.crit_gen.process(p_env) if self.crit_gen else {"alert": {"severity": "CRITICAL"}}
            return res.get("alert")
        elif value >= warning_threshold:
            p_env = {"payload": {"title": f"Warning threshold on {metric_name}", "metric_value": value}}
            res = self.warn_gen.process(p_env) if self.warn_gen else {"alert": {"severity": "WARNING"}}
            return res.get("alert")
        elif value >= info_threshold:
            p_env = {"payload": {"title": f"Notice on {metric_name}", "metric_value": value}}
            res = self.info_gen.process(p_env) if self.info_gen else {"alert": {"severity": "INFO"}}
            return res.get("alert")
        return None

    def escalate_alert(self, alert: Dict[str, Any], escalation_interval_seconds: int = 300) -> Dict[str, Any]:
        """Check and escalate stale alerts."""
        p_env = {"payload": {"alert": alert, "escalation_interval": escalation_interval_seconds}}
        res = self.escalator.process(p_env) if self.escalator else {"alert": alert}
        return res.get("alert", alert)
