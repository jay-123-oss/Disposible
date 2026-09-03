"""Performance & Load Testing Layer Package.

Exports all 14 performance agents, 52 subagents, domain exceptions, and registry helper.
"""

from __future__ import annotations

import logging
from typing import Optional

from core.registry import AgentRegistry
from performance.benchmark_runner import (
    AgentBenchmark,
    ApiBenchmark,
    BenchmarkRunner,
    DatabaseBenchmark,
    SystemBenchmark,
)
from performance.comparison_engine import (
    BaselineComparator,
    ComparisonEngine,
    ExpectedVsActual,
    PreviousRunComparator,
    TrendAnalyzer,
)
from performance.exceptions import (
    AnalysisError,
    BenchmarkError,
    ComparisonError,
    LoadTestError,
    MetricsError,
    MonitoringError,
    PerformanceTestError,
    RecommendationError,
    ReportError,
    ScalabilityTestError,
    SoakTestError,
    SpikeTestError,
    StressTestError,
    ThresholdError,
)
from performance.load_tester import (
    ConcurrentUserTester,
    ConstantLoadTester,
    LoadTester,
    RampUpTester,
    VariableLoadTester,
)
from performance.metrics_collector import (
    ErrorCounter,
    MetricsCollector,
    RequestCounter,
    ResponseTimer,
    SuccessRateTracker,
)
from performance.performance_analyzer import (
    ErrorRateAnalyzer,
    LatencyAnalyzer,
    PerformanceAnalyzer,
    ResponseTimeAnalyzer,
    ThroughputAnalyzer,
)
from performance.performance_orchestrator import PerformanceTestOrchestrator
from performance.recommendation_engine import (
    ConfigurationRecommendations,
    OptimizationPrioritizer,
    PerformanceRecommendations,
    RecommendationEngine,
    ScalingRecommendations,
)
from performance.report_generator import (
    CsvReport,
    GraphReport,
    HtmlReport,
    JsonReport,
    ReportGenerator,
)
from performance.resource_monitor import (
    CpuMonitor,
    DiskMonitor,
    MemoryMonitor,
    NetworkMonitor,
    ResourceMonitor,
)
from performance.scalability_tester import (
    ElasticityTester,
    HorizontalScalingTester,
    ScalabilityTester,
    ScalingEfficiencyTester,
    VerticalScalingTester,
)
from performance.soak_tester import (
    CacheTester,
    ExtendedDurationTester,
    MemoryLeakTester,
    PerformanceDegradationTester,
    SoakTester,
)
from performance.spike_tester import (
    OscillationTester,
    SpikeTester,
    StabilityTester,
    SuddenDropTester,
    SuddenSurgeTester,
)
from performance.stress_tester import (
    BreakpointFinder,
    FailoverTester,
    RecoveryTester,
    ResourceExhaustionTester,
    StressTester,
)
from performance.threshold_validator import (
    ErrorRateValidator,
    ResourceUsageValidator,
    ResponseTimeValidator,
    ThresholdValidator,
    ThroughputValidator,
)

logger = logging.getLogger("FractalCore.Performance")

__all__ = [
    # Master Orchestrator (L3)
    "PerformanceTestOrchestrator",
    # Coordinators (L4)
    "LoadTester",
    "StressTester",
    "SpikeTester",
    "SoakTester",
    "ScalabilityTester",
    "BenchmarkRunner",
    "PerformanceAnalyzer",
    "ResourceMonitor",
    "MetricsCollector",
    "ReportGenerator",
    "ComparisonEngine",
    "ThresholdValidator",
    "RecommendationEngine",
    # Atomic Workers (L5)
    "ConcurrentUserTester",
    "RampUpTester",
    "ConstantLoadTester",
    "VariableLoadTester",
    "BreakpointFinder",
    "ResourceExhaustionTester",
    "FailoverTester",
    "RecoveryTester",
    "SuddenSurgeTester",
    "SuddenDropTester",
    "OscillationTester",
    "StabilityTester",
    "ExtendedDurationTester",
    "MemoryLeakTester",
    "CacheTester",
    "PerformanceDegradationTester",
    "HorizontalScalingTester",
    "VerticalScalingTester",
    "ElasticityTester",
    "ScalingEfficiencyTester",
    "SystemBenchmark",
    "AgentBenchmark",
    "ApiBenchmark",
    "DatabaseBenchmark",
    "ResponseTimeAnalyzer",
    "ThroughputAnalyzer",
    "LatencyAnalyzer",
    "ErrorRateAnalyzer",
    "CpuMonitor",
    "MemoryMonitor",
    "DiskMonitor",
    "NetworkMonitor",
    "RequestCounter",
    "ResponseTimer",
    "ErrorCounter",
    "SuccessRateTracker",
    "HtmlReport",
    "JsonReport",
    "CsvReport",
    "GraphReport",
    "BaselineComparator",
    "PreviousRunComparator",
    "ExpectedVsActual",
    "TrendAnalyzer",
    "ResponseTimeValidator",
    "ThroughputValidator",
    "ErrorRateValidator",
    "ResourceUsageValidator",
    "PerformanceRecommendations",
    "ScalingRecommendations",
    "ConfigurationRecommendations",
    "OptimizationPrioritizer",
    # Exceptions
    "PerformanceTestError",
    "LoadTestError",
    "StressTestError",
    "SpikeTestError",
    "SoakTestError",
    "ScalabilityTestError",
    "BenchmarkError",
    "AnalysisError",
    "MonitoringError",
    "MetricsError",
    "ReportError",
    "ComparisonError",
    "ThresholdError",
    "RecommendationError",
    # Helper
    "register_all_performance_agents",
]


def register_all_performance_agents(
    registry: AgentRegistry,
    parent_orchestrator: Optional[PerformanceTestOrchestrator] = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Instantiate and register all 14 performance coordinators and 52 subagents into registry."""
    orch = parent_orchestrator or PerformanceTestOrchestrator(
        agent_id="PL1_PERFORMANCE_TEST_ORCHESTRATOR",
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

    logger.info("Successfully registered %d performance & load testing domain agents into registry.", registered_count)
    return {
        "performance_orchestrator": orch,
        "total_registered": registered_count,
    }
