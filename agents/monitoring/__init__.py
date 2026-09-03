"""Monitoring & Observability Domain Agents for the Fractal Multi-Agent Coding System.

Exports all 14 specialized monitoring agents and atomic subagents across levels L3 to L5,
along with the registration helper `register_all_monitoring_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from agents.monitoring.alert_manager import (
    AlertEscalator,
    AlertManager,
    CriticalAlertGenerator,
    InfoAlertGenerator,
    WarningAlertGenerator,
)
from agents.monitoring.audit_logger import (
    ActionLogger,
    AuditLogger,
    ErrorLogger,
    PerformanceLogger,
    SecurityLogger,
)
from agents.monitoring.dashboard_generator import (
    AlertsDashboardGenerator,
    DashboardGenerator,
    HealthDashboardGenerator,
    MetricsDashboardGenerator,
    TraceDashboardGenerator,
)
from agents.monitoring.drift_detector import (
    AccuracyDriftDetector,
    BehaviorDriftDetector,
    DriftDetector,
    DriftReporter,
    PerformanceDriftDetector,
)
from agents.monitoring.error_aggregator import (
    ErrorAggregator,
    ErrorAnalyzer,
    ErrorClassifier,
    ErrorCollector,
    ErrorPatternDetector,
)
from agents.monitoring.exceptions import (
    AlertError,
    AuditLogError,
    DashboardGenerationError,
    DebuggerError,
    DriftDetectionError,
    ErrorAggregationError,
    HealthCheckError,
    MetricsCollectionError,
    MonitoringError,
    PerformanceTrackingError,
    PredictiveAnalysisError,
    ReportGenerationError,
    ResourceMonitoringError,
    TraceCollectionError,
)
from agents.monitoring.health_checker import (
    AgentHealthChecker,
    DependencyHealthChecker,
    HealthChecker,
    ServiceHealthChecker,
    SystemHealthChecker,
)
from agents.monitoring.live_debugger import (
    BreakpointManager,
    InteractiveDebugger,
    LiveDebugger,
    StackTraceAnalyzer,
    VariableInspector,
)
from agents.monitoring.metrics_collector import (
    AgentMetricsCollector,
    ApplicationMetricsCollector,
    MetricsCollector,
    SystemMetricsCollector,
    TokenMetricsCollector,
)
from agents.monitoring.monitoring_orchestrator import MonitoringOrchestrator
from agents.monitoring.performance_tracker import (
    LatencyTracker,
    PerformanceTracker,
    ResponseTimeTracker,
    ScalabilityTracker,
    ThroughputTracker,
)
from agents.monitoring.predictive_analyzer import (
    AnomalyPredictor,
    CapacityPredictor,
    FailurePredictor,
    PredictiveAnalyzer,
    RecommendationGenerator,
)
from agents.monitoring.report_generator import (
    CustomReportGenerator,
    DailyReportGenerator,
    MonthlyReportGenerator,
    ReportGenerator,
    WeeklyReportGenerator,
)
from agents.monitoring.resource_monitor import (
    CpuMonitor,
    DiskMonitor,
    MemoryMonitor,
    NetworkMonitor,
    ResourceMonitor,
)
from agents.monitoring.trace_collector import (
    LatencyBreakdownGenerator,
    SpanAnalyzer,
    TraceCollector,
    TraceExtractor,
    TraceGraphGenerator,
)
from core.registry import AgentRegistry


logger = logging.getLogger("FractalCore.Monitoring")

__all__ = [
    # Master Orchestrator
    "MonitoringOrchestrator",
    # Live Debugger
    "LiveDebugger",
    "BreakpointManager",
    "VariableInspector",
    "StackTraceAnalyzer",
    "InteractiveDebugger",
    # Metrics Collector
    "MetricsCollector",
    "SystemMetricsCollector",
    "ApplicationMetricsCollector",
    "AgentMetricsCollector",
    "TokenMetricsCollector",
    # Alert Manager
    "AlertManager",
    "CriticalAlertGenerator",
    "WarningAlertGenerator",
    "InfoAlertGenerator",
    "AlertEscalator",
    # Drift Detector
    "DriftDetector",
    "PerformanceDriftDetector",
    "AccuracyDriftDetector",
    "BehaviorDriftDetector",
    "DriftReporter",
    # Audit Logger
    "AuditLogger",
    "ActionLogger",
    "SecurityLogger",
    "PerformanceLogger",
    "ErrorLogger",
    # Performance Tracker
    "PerformanceTracker",
    "ResponseTimeTracker",
    "ThroughputTracker",
    "LatencyTracker",
    "ScalabilityTracker",
    # Resource Monitor
    "ResourceMonitor",
    "CpuMonitor",
    "MemoryMonitor",
    "DiskMonitor",
    "NetworkMonitor",
    # Error Aggregator
    "ErrorAggregator",
    "ErrorCollector",
    "ErrorClassifier",
    "ErrorAnalyzer",
    "ErrorPatternDetector",
    # Trace Collector
    "TraceCollector",
    "TraceExtractor",
    "SpanAnalyzer",
    "TraceGraphGenerator",
    "LatencyBreakdownGenerator",
    # Dashboard Generator
    "DashboardGenerator",
    "MetricsDashboardGenerator",
    "AlertsDashboardGenerator",
    "TraceDashboardGenerator",
    "HealthDashboardGenerator",
    # Report Generator
    "ReportGenerator",
    "DailyReportGenerator",
    "WeeklyReportGenerator",
    "MonthlyReportGenerator",
    "CustomReportGenerator",
    # Health Checker
    "HealthChecker",
    "SystemHealthChecker",
    "AgentHealthChecker",
    "ServiceHealthChecker",
    "DependencyHealthChecker",
    # Predictive Analyzer
    "PredictiveAnalyzer",
    "FailurePredictor",
    "AnomalyPredictor",
    "CapacityPredictor",
    "RecommendationGenerator",
    # Exceptions
    "MonitoringError",
    "DebuggerError",
    "MetricsCollectionError",
    "AlertError",
    "DriftDetectionError",
    "AuditLogError",
    "PerformanceTrackingError",
    "ResourceMonitoringError",
    "ErrorAggregationError",
    "TraceCollectionError",
    "DashboardGenerationError",
    "ReportGenerationError",
    "HealthCheckError",
    "PredictiveAnalysisError",
    # Registration Helper
    "register_all_monitoring_agents",
]


def register_all_monitoring_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Register all monitoring and observability layer agents into the AgentRegistry.

    Args:
        registry: The central AgentRegistry singleton.
        parent_agent: Optional supervising orchestrator coordinator.
        max_depth: Global depth ceiling for monitoring hierarchy.

    Returns:
        Dict mapping agent_id to instantiated agent instances.
    """
    logger.info("Registering all monitoring & observability domain agents into AgentRegistry...")

    # Root Monitoring Orchestrator (L3)
    monitoring_orchestrator = MonitoringOrchestrator(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="M1_MONITORING_ORCHESTRATOR",
        auto_spawn_subagents=True,
    )
    registry.register_agent(monitoring_orchestrator)

    registered_count = 1
    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(monitoring_orchestrator)

    logger.info("Successfully registered %d monitoring domain agents into registry.", registered_count)
    return {
        "monitoring_orchestrator": monitoring_orchestrator,
        "total_registered": registered_count,
    }
