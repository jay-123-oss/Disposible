"""Testing & Validation Layer for the Fractal Multi-Agent System.

Exports all 14 specialized testing & validation agents and atomic subagents across L3 to L5,
along with custom exceptions and the registration helper `register_all_testing_validation_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from core.registry import AgentRegistry
from tests.coverage.coverage_reporter import (
    BranchCoverage,
    CoverageReporter,
    FileCoverage,
    FunctionCoverage,
    LineCoverage,
)
from tests.data.test_cleanup import (
    CacheCleaner,
    DataCleaner,
    FileCleaner,
    SessionCleaner,
    TestCleanup,
)
from tests.data.test_data_setup import (
    EnvSetup,
    FixtureLoader,
    MockDataGenerator,
    SeedDataGenerator,
    TestDataSetup,
)
from tests.exceptions import (
    AggregationError,
    CoverageError,
    IntegrationTestError,
    MockServerError,
    PerformanceTestError,
    QualityTestError,
    ReportGenerationError,
    SecurityTestError,
    SystemTestError,
    TestDataError,
    TestError,
    UnitTestError,
    ValidationError,
)
from tests.integration.test_integration_runner import (
    ApiTester,
    DatabaseTester,
    EventTester,
    ExternalServiceTester,
    IntegrationTestRunner,
)
from tests.mock.mock_server import (
    ApiMocker,
    DatabaseMocker,
    MockServer,
    ResponseMocker,
    ServiceMocker,
)
from tests.performance.test_performance_runner import (
    LatencyTester,
    LoadTester,
    PerformanceTestRunner,
    StressTester,
    ThroughputTester,
)
from tests.quality.test_quality_runner import (
    CodeQualityTester,
    ComplexityTester,
    DocumentationTester,
    QualityTestRunner,
    StyleTester,
)
from tests.reports.report_generator import (
    HtmlReport,
    JsonReport,
    JunitReport,
    MarkdownReport,
    ReportGenerator,
)
from tests.results.result_aggregator import (
    ResultAggregator,
    ResultsAnalyzer,
    ResultsCollector,
    ResultsGrouper,
    ResultsSummarizer,
)
from tests.security.test_security_runner import (
    AuthTester,
    ComplianceTester,
    InjectionTester,
    SecurityTestRunner,
    XssTester,
)
from tests.system.test_system_runner import (
    AdminFlowTester,
    EndToEndTester,
    ErrorFlowTester,
    SystemTestRunner,
    UserFlowTester,
)
from tests.test_orchestrator import TestOrchestrator
from tests.unit.test_unit_runner import (
    AgentTester,
    HelperTester,
    ModelTester,
    UnitTestRunner,
    UtilityTester,
)
from tests.validation.validation_engine import (
    ConsistencyChecker,
    EdgeCaseValidator,
    ExpectationChecker,
    ResultValidator,
    ValidationEngine,
)


logger = logging.getLogger("FractalCore.Testing")

__all__ = [
    # Master Test Orchestrator
    "TestOrchestrator",
    # System Test Runner
    "SystemTestRunner",
    "EndToEndTester",
    "UserFlowTester",
    "AdminFlowTester",
    "ErrorFlowTester",
    # Integration Test Runner
    "IntegrationTestRunner",
    "ApiTester",
    "DatabaseTester",
    "ExternalServiceTester",
    "EventTester",
    # Unit Test Runner
    "UnitTestRunner",
    "AgentTester",
    "UtilityTester",
    "ModelTester",
    "HelperTester",
    # Performance Test Runner
    "PerformanceTestRunner",
    "LoadTester",
    "StressTester",
    "LatencyTester",
    "ThroughputTester",
    # Security Test Runner
    "SecurityTestRunner",
    "AuthTester",
    "InjectionTester",
    "XssTester",
    "ComplianceTester",
    # Quality Test Runner
    "QualityTestRunner",
    "CodeQualityTester",
    "DocumentationTester",
    "StyleTester",
    "ComplexityTester",
    # Validation Engine
    "ValidationEngine",
    "ResultValidator",
    "ExpectationChecker",
    "EdgeCaseValidator",
    "ConsistencyChecker",
    # Coverage Reporter
    "CoverageReporter",
    "LineCoverage",
    "BranchCoverage",
    "FunctionCoverage",
    "FileCoverage",
    # Test Data Setup
    "TestDataSetup",
    "FixtureLoader",
    "SeedDataGenerator",
    "MockDataGenerator",
    "EnvSetup",
    # Test Cleanup
    "TestCleanup",
    "DataCleaner",
    "FileCleaner",
    "SessionCleaner",
    "CacheCleaner",
    # Mock Server
    "MockServer",
    "ApiMocker",
    "DatabaseMocker",
    "ServiceMocker",
    "ResponseMocker",
    # Result Aggregator
    "ResultAggregator",
    "ResultsCollector",
    "ResultsAnalyzer",
    "ResultsGrouper",
    "ResultsSummarizer",
    # Report Generator
    "ReportGenerator",
    "HtmlReport",
    "JsonReport",
    "MarkdownReport",
    "JunitReport",
    # Exceptions
    "TestError",
    "SystemTestError",
    "IntegrationTestError",
    "UnitTestError",
    "PerformanceTestError",
    "SecurityTestError",
    "QualityTestError",
    "ValidationError",
    "CoverageError",
    "TestDataError",
    "MockServerError",
    "AggregationError",
    "ReportGenerationError",
    # Registration Helper
    "register_all_testing_validation_agents",
]


def register_all_testing_validation_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Register all Testing & Validation layer agents into the central AgentRegistry.

    Args:
        registry: The central AgentRegistry singleton.
        parent_agent: Optional supervising orchestrator coordinator.
        max_depth: Global depth ceiling.

    Returns:
        Dict mapping root agent and count of registered agents.
    """
    logger.info("Registering all testing & validation domain agents into AgentRegistry...")

    test_orchestrator = TestOrchestrator(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="TV1_TEST_ORCHESTRATOR",
        auto_spawn_subagents=True,
    )
    registry.register_agent(test_orchestrator)

    registered_count = 1

    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(test_orchestrator)

    logger.info("Successfully registered %d testing & validation domain agents into registry.", registered_count)
    return {
        "test_orchestrator": test_orchestrator,
        "total_registered": registered_count,
    }
