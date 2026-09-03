"""Production Monitoring & Support Layer Package.

Exports all 14 agents, 52 subagents, domain exceptions, and registry helper.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from core.registry import AgentRegistry
from monitoring_support.alert_manager import (
    AlertCloser,
    AlertDistributor,
    AlertEscalator,
    AlertGenerator,
    AlertManager,
)
from monitoring_support.continuous_improver import (
    ContinuousImprover,
    ImprovementExecutor,
    ImprovementPrioritizer,
    MetricAnalyzer,
    OptimizationFinder,
)
from monitoring_support.error_aggregator import (
    ErrorAggregator,
    ErrorAnalyzer,
    ErrorClassifier,
    ErrorCollector,
    TrendDetector,
)
from monitoring_support.escalation_manager import (
    EscalationChecker,
    EscalationExecutor,
    EscalationManager,
    EscalationNotifier,
    EscalationTracker,
)
from monitoring_support.exceptions import (
    AlertManagementError,
    ContinuousImprovementError,
    ErrorAggregationError,
    EscalationError,
    IncidentDetectionError,
    IncidentResponseError,
    LogAnalysisError,
    MonitoringSupportError,
    PerformanceMonitoringError,
    RealTimeMonitoringError,
    ResourceMonitoringError,
    RootCauseAnalysisError,
    TicketManagementError,
    UserFeedbackError,
)
from monitoring_support.incident_detector import (
    AnomalyDetector,
    IncidentDetector,
    PatternRecognizer,
    PredictiveDetector,
    ThresholdChecker,
)
from monitoring_support.incident_responder import (
    IncidentCloser,
    IncidentResponder,
    ResolutionExecutor,
    ResponseCoordinator,
    TriageHandler,
)
from monitoring_support.log_analyzer import (
    LogAnalyzer,
    LogIndexer,
    LogParser,
    LogSearcher,
    LogVisualizer,
)
from monitoring_support.performance_monitor import (
    LatencyMonitor,
    PerformanceMonitor,
    ThroughputMonitor,
    TrendAnalyzer,
    UsageMonitor,
)
from monitoring_support.production_monitoring_orchestrator import ProductionMonitoringOrchestrator
from monitoring_support.real_time_monitor import (
    AgentMetricsMonitor,
    BusinessMetricsMonitor,
    RealTimeMonitor,
    ServiceMetricsMonitor,
    SystemMetricsMonitor,
)
from monitoring_support.resource_monitor import (
    CpuMonitor,
    DiskMonitor,
    MemoryMonitor,
    NetworkMonitor,
    ResourceMonitor,
)
from monitoring_support.root_cause_analyzer import (
    CauseFinder,
    PatternAnalyzer,
    PreventionPlanner,
    RecommendationGenerator,
    RootCauseAnalyzer,
)
from monitoring_support.support_ticket_manager import (
    SupportTicketManager,
    TicketAssigner,
    TicketClassifier,
    TicketCreator,
    TicketResolver,
)
from monitoring_support.user_feedback_monitor import (
    ActionGenerator,
    FeedbackAnalyzer,
    FeedbackCollector,
    SentimentAnalyzer,
    UserFeedbackMonitor,
)

logger = logging.getLogger("FractalCore.MonitoringSupport")

__all__ = [
    # Master Orchestrator (L3)
    "ProductionMonitoringOrchestrator",
    # Coordinators (L4)
    "RealTimeMonitor",
    "IncidentDetector",
    "AlertManager",
    "IncidentResponder",
    "SupportTicketManager",
    "EscalationManager",
    "RootCauseAnalyzer",
    "PerformanceMonitor",
    "ResourceMonitor",
    "ErrorAggregator",
    "LogAnalyzer",
    "UserFeedbackMonitor",
    "ContinuousImprover",
    # Atomic Workers (L5)
    "SystemMetricsMonitor",
    "AgentMetricsMonitor",
    "ServiceMetricsMonitor",
    "BusinessMetricsMonitor",
    "AnomalyDetector",
    "PatternRecognizer",
    "ThresholdChecker",
    "PredictiveDetector",
    "AlertGenerator",
    "AlertDistributor",
    "AlertEscalator",
    "AlertCloser",
    "TriageHandler",
    "ResponseCoordinator",
    "ResolutionExecutor",
    "IncidentCloser",
    "TicketCreator",
    "TicketClassifier",
    "TicketAssigner",
    "TicketResolver",
    "EscalationChecker",
    "EscalationExecutor",
    "EscalationNotifier",
    "EscalationTracker",
    "CauseFinder",
    "PatternAnalyzer",
    "RecommendationGenerator",
    "PreventionPlanner",
    "LatencyMonitor",
    "ThroughputMonitor",
    "UsageMonitor",
    "TrendAnalyzer",
    "CpuMonitor",
    "MemoryMonitor",
    "DiskMonitor",
    "NetworkMonitor",
    "ErrorCollector",
    "ErrorClassifier",
    "ErrorAnalyzer",
    "TrendDetector",
    "LogParser",
    "LogIndexer",
    "LogSearcher",
    "LogVisualizer",
    "FeedbackCollector",
    "FeedbackAnalyzer",
    "SentimentAnalyzer",
    "ActionGenerator",
    "MetricAnalyzer",
    "OptimizationFinder",
    "ImprovementPrioritizer",
    "ImprovementExecutor",
    # Exceptions
    "MonitoringSupportError",
    "RealTimeMonitoringError",
    "IncidentDetectionError",
    "AlertManagementError",
    "IncidentResponseError",
    "TicketManagementError",
    "EscalationError",
    "RootCauseAnalysisError",
    "PerformanceMonitoringError",
    "ResourceMonitoringError",
    "ErrorAggregationError",
    "LogAnalysisError",
    "UserFeedbackError",
    "ContinuousImprovementError",
    # Registry Helper
    "register_all_monitoring_support_agents",
]


def register_all_monitoring_support_agents(
    registry: AgentRegistry,
    parent_orchestrator: Optional[ProductionMonitoringOrchestrator] = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Instantiate and register all 14 Production Monitoring coordinators and 52 subagents into registry."""
    orch = parent_orchestrator or ProductionMonitoringOrchestrator(
        agent_id="PM1_PRODUCTION_MONITORING_ORCHESTRATOR",
        max_depth=max_depth,
        auto_spawn_subagents=True,
    )
    registry.register_agent(orch)
    registered_count = 1

    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(orch)

    logger.info("Successfully registered %d Production Monitoring domain agents into registry.", registered_count)
    return {
        "production_monitoring_orchestrator": orch,
        "total_registered": registered_count,
    }
