"""MonitoringOrchestrator coordinating all 13 monitoring and observability subsystems."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.monitoring.alert_manager import AlertManager
from agents.monitoring.audit_logger import AuditLogger
from agents.monitoring.dashboard_generator import DashboardGenerator
from agents.monitoring.drift_detector import DriftDetector
from agents.monitoring.error_aggregator import ErrorAggregator
from agents.monitoring.exceptions import MonitoringError
from agents.monitoring.health_checker import HealthChecker
from agents.monitoring.live_debugger import LiveDebugger
from agents.monitoring.metrics_collector import MetricsCollector
from agents.monitoring.performance_tracker import PerformanceTracker
from agents.monitoring.predictive_analyzer import PredictiveAnalyzer
from agents.monitoring.report_generator import ReportGenerator
from agents.monitoring.resource_monitor import ResourceMonitor
from agents.monitoring.trace_collector import TraceCollector
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Monitoring.MonitoringOrchestrator")


class MonitoringOrchestrator(BaseAgent):
    """L3 Master Monitoring & Observability Orchestrator coordinating all 13 L4 subsystems."""

    def __init__(
        self,
        name: str = "MonitoringOrchestrator",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 256,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "monitoring",
            "observability",
            "monitoring_orchestration",
            "metrics_aggregation",
            "system_health_audit",
            "telemetry_coordination",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M1_MONITORING_ORCHESTRATOR",
        )

        self.debugger: Optional[LiveDebugger] = None
        self.metrics: Optional[MetricsCollector] = None
        self.alerts: Optional[AlertManager] = None
        self.drift: Optional[DriftDetector] = None
        self.audit: Optional[AuditLogger] = None
        self.performance: Optional[PerformanceTracker] = None
        self.resources: Optional[ResourceMonitor] = None
        self.errors: Optional[ErrorAggregator] = None
        self.traces: Optional[TraceCollector] = None
        self.dashboards: Optional[DashboardGenerator] = None
        self.reports: Optional[ReportGenerator] = None
        self.health: Optional[HealthChecker] = None
        self.predictive: Optional[PredictiveAnalyzer] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_monitoring_subsystems()

        self.register_tool("run_monitoring_pipeline", self.run_monitoring_pipeline)

    def _spawn_monitoring_subsystems(self) -> None:
        """Spawn the 13 L4 monitoring and observability coordinators (Rule 1 & Rule 5)."""
        logger.info("MonitoringOrchestrator %s spawning 13 subsystems...", self.agent_id)
        child_depth = self.depth + 2

        self.debugger = self.spawn_subagent(
            LiveDebugger,
            name="LiveDebugger",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.metrics = self.spawn_subagent(
            MetricsCollector,
            name="MetricsCollector",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.alerts = self.spawn_subagent(
            AlertManager,
            name="AlertManager",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.drift = self.spawn_subagent(
            DriftDetector,
            name="DriftDetector",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.audit = self.spawn_subagent(
            AuditLogger,
            name="AuditLogger",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.performance = self.spawn_subagent(
            PerformanceTracker,
            name="PerformanceTracker",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.resources = self.spawn_subagent(
            ResourceMonitor,
            name="ResourceMonitor",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.errors = self.spawn_subagent(
            ErrorAggregator,
            name="ErrorAggregator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.traces = self.spawn_subagent(
            TraceCollector,
            name="TraceCollector",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.dashboards = self.spawn_subagent(
            DashboardGenerator,
            name="DashboardGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.reports = self.spawn_subagent(
            ReportGenerator,
            name="ReportGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.health = self.spawn_subagent(
            HealthChecker,
            name="HealthChecker",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.predictive = self.spawn_subagent(
            PredictiveAnalyzer,
            name="PredictiveAnalyzer",
            max_depth=child_depth,
            resources_mb=128,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MonitoringOrchestrator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        report = self.run_monitoring_pipeline(context=payload)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "monitoring_report": report,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        rep = result.get("monitoring_report")
        if not rep or "all_subsystems_healthy" not in rep:
            raise MonitoringError("MonitoringOrchestrator produced incomplete evaluation report.")
        return result

    def cleanup(self) -> None:
        logger.debug("MonitoringOrchestrator %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def run_monitoring_pipeline(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute comprehensive monitoring cycle across all 13 observability subsystems."""
        ctx = context or {}
        logger.info("Executing comprehensive observability pipeline...")

        # 1. Live Debugger: inspect sample scope
        dbg_res = self.debugger.inspect_scope({"task_id": "TSK_SAMPLE", "active": True}) if self.debugger else {}

        # 2. Metrics Collector: snapshot metrics
        met_res = self.metrics.collect_all_metrics() if self.metrics else {}

        # 3. Alert Manager: evaluate CPU metric against thresholds
        alt_res = self.alerts.evaluate_metric("cpu_percent", value=ctx.get("cpu", 45.0)) if self.alerts else None

        # 4. Drift Detector: evaluate baseline vs current
        dft_res = self.drift.detect_drift() if self.drift else {}

        # 5. Audit Logger: record pipeline run
        aud_res = self.audit.log_event("ACTION", {"actor": self.agent_id, "action": "PIPELINE_RUN"}) if self.audit else {}

        # 6. Performance Tracker: profile latency & throughput
        prf_res = self.performance.track_performance() if self.performance else {"all_thresholds_met": True}

        # 7. Resource Monitor: check CPU, RAM, disk, network
        rsc_res = self.resources.check_resources() if self.resources else {"all_resources_healthy": True}

        # 8. Error Aggregator: classify test error
        err_res = self.errors.record_error("Test sample warning", source_agent=self.agent_id) if self.errors else {}

        # 9. Trace Collector: record operation span
        trc_res = self.traces.record_span("run_monitoring_pipeline", duration_ms=15.0) if self.traces else {}

        # 10. Dashboard Generator: produce unified dashboard
        dsh_res = self.dashboards.generate_complete_dashboard() if self.dashboards else {}

        # 11. Report Generator: synthesize daily report
        rpt_res = self.reports.generate_report("DAILY") if self.reports else {}

        # 12. Health Checker: evaluate system and agent health
        hlt_res = self.health.check_health() if self.health else {"overall_healthy": True}

        # 13. Predictive Analyzer: run failure & capacity models
        prd_res = self.predictive.run_predictive_analysis() if self.predictive else {}

        all_healthy = (
            prf_res.get("all_thresholds_met", True)
            and rsc_res.get("all_resources_healthy", True)
            and hlt_res.get("overall_healthy", True)
        )

        return {
            "all_subsystems_healthy": all_healthy,
            "debugger": dbg_res,
            "metrics": met_res,
            "alert": alt_res,
            "drift": dft_res,
            "audit": aud_res,
            "performance": prf_res,
            "resources": rsc_res,
            "error_aggregation": err_res,
            "trace": trc_res,
            "dashboard": dsh_res.get("title"),
            "report": rpt_res.get("period"),
            "health": hlt_res.get("overall_healthy"),
            "predictive": prd_res.get("recommendations"),
        }
