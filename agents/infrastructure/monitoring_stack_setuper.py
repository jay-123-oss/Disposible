"""MonitoringStackSetuper agent synthesizing Prometheus, Grafana, and AlertManager configurations."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from agents.infrastructure.exceptions import MonitoringError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Infrastructure.MonitoringStackSetuper")


# ==============================================================================
# L5 Atomic Monitoring Subagents
# ==============================================================================

class PrometheusConfigGenerator(BaseAgent):
    """L5 agent authoring prometheus.yml scrape job definitions."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PrometheusConfigGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        prom_yaml = (
            "global:\n"
            "  scrape_interval: 15s\n"
            "  evaluation_interval: 15s\n\n"
            "rule_files:\n"
            "  - 'alert_rules.yml'\n\n"
            "scrape_configs:\n"
            "  - job_name: 'microservice-api'\n"
            "    metrics_path: '/metrics'\n"
            "    static_configs:\n"
            "      - targets: ['api:8000']\n"
        )
        return {"status": "COMPLETED", "prometheus_yaml": prom_yaml}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PrometheusConfigGenerator %s cleaned up.", self.agent_id)


class GrafanaDashboardGenerator(BaseAgent):
    """L5 agent authoring Grafana dashboard JSON models for latency, throughput, and error rates."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("GrafanaDashboardGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        dashboard = {
            "title": "Fractal Microservice Operational Overview",
            "panels": [
                {"title": "Request Rate (req/sec)", "type": "graph", "targets": [{"expr": "rate(http_requests_total[1m])"}]},
                {"title": "p95 Latency (ms)", "type": "graph", "targets": [{"expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))"}]},
                {"title": "Error Rate (5xx)", "type": "singlestat", "targets": [{"expr": "sum(rate(http_requests_total{status=~'5..'}[5m]))"}]},
            ],
        }
        return {"status": "COMPLETED", "dashboard_json": json.dumps(dashboard, indent=2)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("GrafanaDashboardGenerator %s cleaned up.", self.agent_id)


class AlertManagerConfigurer(BaseAgent):
    """L5 agent authoring Prometheus alert rules for high latency and service outages."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AlertManagerConfigurer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        alerts_yaml = (
            "groups:\n"
            "  - name: service_alerts\n"
            "    rules:\n"
            "      - alert: ServiceDown\n"
            "        expr: up == 0\n"
            "        for: 1m\n"
            "        labels:\n"
            "          severity: critical\n"
            "        annotations:\n"
            "          summary: \"Instance {{ $labels.instance }} down\"\n\n"
            "      - alert: HighLatencyP95\n"
            "        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 0.5\n"
            "        for: 2m\n"
            "        labels:\n"
            "          severity: warning\n"
        )
        return {"status": "COMPLETED", "alerts_yaml": alerts_yaml}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AlertManagerConfigurer %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 MonitoringStackSetuper Agent
# ==============================================================================

class MonitoringStackSetuper(BaseAgent):
    """L4 coordinator synthesizing Prometheus scrape jobs, Grafana dashboards, and AlertManager rules."""

    def __init__(
        self,
        name: str = "MonitoringStackSetuper",
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
            "monitoring_stack_setup",
            "prometheus_configuration",
            "grafana_dashboards",
            "alertmanager_rules",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "I10_MONITORING_STACK_SETUPER",
        )

        self.prom_gen: Optional[PrometheusConfigGenerator] = None
        self.graf_gen: Optional[GrafanaDashboardGenerator] = None
        self.alert_cfg: Optional[AlertManagerConfigurer] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_monitoring_bundle", self.generate_monitoring_bundle)

    def _spawn_subagents(self) -> None:
        """Spawn atomic monitoring subagents (Rule 1 & Rule 5)."""
        logger.info("MonitoringStackSetuper %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.prom_gen = self.spawn_subagent(
            PrometheusConfigGenerator,
            name="PrometheusConfigGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.graf_gen = self.spawn_subagent(
            GrafanaDashboardGenerator,
            name="GrafanaDashboardGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.alert_cfg = self.spawn_subagent(
            AlertManagerConfigurer,
            name="AlertManagerConfigurer",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MonitoringStackSetuper %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        bundle = self.generate_monitoring_bundle()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "monitoring_bundle": bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        bundle = result.get("monitoring_bundle")
        if not bundle or "prometheus" not in bundle:
            raise MonitoringError("MonitoringStackSetuper produced incomplete bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("MonitoringStackSetuper %s cleanup complete.", self.agent_id)

    def generate_monitoring_bundle(self) -> Dict[str, str]:
        """Synthesize Prometheus, Grafana, and AlertManager configurations."""
        p = self.prom_gen.process({}) if self.prom_gen else {"prometheus_yaml": ""}
        g = self.graf_gen.process({}) if self.graf_gen else {"dashboard_json": ""}
        a = self.alert_cfg.process({}) if self.alert_cfg else {"alerts_yaml": ""}

        return {
            "prometheus": p.get("prometheus_yaml", ""),
            "grafana_dashboard": g.get("dashboard_json", ""),
            "alertmanager_rules": a.get("alerts_yaml", ""),
            "passed": True,
        }
