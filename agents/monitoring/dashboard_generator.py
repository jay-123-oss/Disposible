"""DashboardGenerator agent generating real-time UI dashboard specifications and widget models."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from agents.monitoring.exceptions import DashboardGenerationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Monitoring.DashboardGenerator")


# ==============================================================================
# L5 Atomic Dashboard Subagents
# ==============================================================================

class MetricsDashboardGenerator(BaseAgent):
    """L5 agent building metric widgets (CPU gauge, Memory bar, Throughput sparkline, Token utilization)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MetricsDashboardGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        metrics = payload.get("metrics", {})

        widgets = [
            {"widget_id": "w_cpu", "type": "GAUGE", "title": "CPU Utilization", "value": metrics.get("cpu_percent", 20.0), "unit": "%"},
            {"widget_id": "w_ram", "type": "BAR", "title": "RAM Usage", "value": metrics.get("ram_mb", 4096), "max": 8192, "unit": "MB"},
            {"widget_id": "w_tps", "type": "LINE", "title": "System Throughput", "value": metrics.get("throughput_rps", 120.0), "unit": "rps"},
            {"widget_id": "w_tok", "type": "PROGRESS", "title": "Token Quota", "value": metrics.get("tokens", 1200), "max": 4096, "unit": "tokens"},
        ]
        return {"status": "COMPLETED", "metrics_dashboard": {"widgets": widgets}}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("MetricsDashboardGenerator %s cleaned up.", self.agent_id)


class AlertsDashboardGenerator(BaseAgent):
    """L5 agent building alert feeds, incident status cards, and escalation boards."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AlertsDashboardGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        alerts = payload.get("alerts", [])

        crit_count = sum(1 for a in alerts if a.get("severity") == "CRITICAL")
        warn_count = sum(1 for a in alerts if a.get("severity") == "WARNING")

        dashboard = {
            "summary_cards": [
                {"title": "Critical Alerts", "count": crit_count, "status": "DANGER" if crit_count > 0 else "OK"},
                {"title": "Warnings", "count": warn_count, "status": "WARNING" if warn_count > 0 else "OK"},
            ],
            "active_alerts": alerts[:10],
        }
        return {"status": "COMPLETED", "alerts_dashboard": dashboard}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AlertsDashboardGenerator %s cleaned up.", self.agent_id)


class TraceDashboardGenerator(BaseAgent):
    """L5 agent generating flamegraphs, DAG topologies, and latency waterfall models."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TraceDashboardGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        traces = payload.get("traces", {})

        dashboard = {
            "view_type": "WATERFALL_FLAMEGRAPH",
            "root_operation": traces.get("root_op", "Orchestrator.dispatch"),
            "total_latency_ms": traces.get("total_duration_ms", 55.0),
            "spans_rendered": len(traces.get("spans", [])),
        }
        return {"status": "COMPLETED", "trace_dashboard": dashboard}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TraceDashboardGenerator %s cleaned up.", self.agent_id)


class HealthDashboardGenerator(BaseAgent):
    """L5 agent assembling overall cluster health gauges and subsystem status grids."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("HealthDashboardGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        subsystems = payload.get("subsystems", {
            "planning": "HEALTHY",
            "coding": "HEALTHY",
            "testing": "HEALTHY",
            "security": "HEALTHY",
            "quality": "HEALTHY",
            "infrastructure": "HEALTHY",
            "commstate": "HEALTHY",
            "monitoring": "HEALTHY",
        })

        all_ok = all(v == "HEALTHY" for v in subsystems.values())
        return {
            "status": "COMPLETED",
            "health_dashboard": {
                "overall_status": "PASSING" if all_ok else "DEGRADED",
                "subsystems": subsystems,
                "timestamp": time.time(),
            },
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("HealthDashboardGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 DashboardGenerator Agent
# ==============================================================================

class DashboardGenerator(BaseAgent):
    """L4 coordinator overseeing metrics, alerts, traces, and cluster health dashboard generation."""

    def __init__(
        self,
        name: str = "DashboardGenerator",
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
            "dashboard_generation",
            "metrics_dashboard",
            "alerts_dashboard",
            "trace_dashboard",
            "health_dashboard",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M11_DASHBOARD_GENERATOR",
        )

        self.metrics_dash: Optional[MetricsDashboardGenerator] = None
        self.alerts_dash: Optional[AlertsDashboardGenerator] = None
        self.trace_dash: Optional[TraceDashboardGenerator] = None
        self.health_dash: Optional[HealthDashboardGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_complete_dashboard", self.generate_complete_dashboard)

    def _spawn_subagents(self) -> None:
        """Spawn atomic dashboard subagents (Rule 1 & Rule 5)."""
        logger.info("DashboardGenerator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.metrics_dash = self.spawn_subagent(
            MetricsDashboardGenerator,
            name="MetricsDashboardGenerator",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.alerts_dash = self.spawn_subagent(
            AlertsDashboardGenerator,
            name="AlertsDashboardGenerator",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.trace_dash = self.spawn_subagent(
            TraceDashboardGenerator,
            name="TraceDashboardGenerator",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.health_dash = self.spawn_subagent(
            HealthDashboardGenerator,
            name="HealthDashboardGenerator",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DashboardGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        dash = self.generate_complete_dashboard(context=payload)
        return {"status": "COMPLETED", "dashboard": dash}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DashboardGenerator %s cleanup complete.", self.agent_id)

    def generate_complete_dashboard(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Aggregate all 4 dashboard views into a single unified dashboard payload."""
        ctx = context or {}
        p_env = {"payload": ctx}

        m_res = self.metrics_dash.process(p_env) if self.metrics_dash else {}
        a_res = self.alerts_dash.process(p_env) if self.alerts_dash else {}
        t_res = self.trace_dash.process(p_env) if self.trace_dash else {}
        h_res = self.health_dash.process(p_env) if self.health_dash else {}

        return {
            "title": "Fractal Multi-Agent Real-Time Observability",
            "auto_refresh_seconds": 30,
            "generated_at": time.time(),
            "metrics_view": m_res.get("metrics_dashboard"),
            "alerts_view": a_res.get("alerts_dashboard"),
            "traces_view": t_res.get("trace_dashboard"),
            "health_view": h_res.get("health_dashboard"),
        }
