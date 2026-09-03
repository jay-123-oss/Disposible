"""Testing Domain Agents for the Fractal Multi-Agent Coding System.

Exports all 16 specialized testing agents and subagents across levels L3 to L6,
along with the registration helper `register_all_testing_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from agents.testing.coverage_analyzer import (
    BranchCoverage,
    CoverageAnalyzer,
    FunctionCoverage,
    LineCoverage,
)
from agents.testing.exceptions import (
    CoverageError,
    MockGenerationError,
    PerformanceTestError,
    ReportGenerationError,
    TestDataCreationError,
    TestExecutionError,
    TestGenerationError,
    TestingError,
    ValidationError,
)
from agents.testing.integration_test_creator import IntegrationTestCreator
from agents.testing.integration_tests import (
    APITester,
    FlowTester,
)
from agents.testing.mock_generator import MockGenerator
from agents.testing.mocks import (
    DataMocker,
    DependencyMocker,
)
from agents.testing.performance_tester import (
    LoadTester,
    PerformanceTester,
    StressTester,
)
from agents.testing.report_generator import (
    HtmlReport,
    JsonReport,
    MarkdownReport,
    ReportGenerator,
)
from agents.testing.test_data_creator import (
    FixtureGenerator,
    SeedGenerator,
    TestDataCreator,
)
from agents.testing.test_orchestrator import TestOrchestrator
from agents.testing.test_scenarios import (
    AssertionBuilder,
    EdgeCaseHunter,
    ErrorCaseTester,
    HappyPathTester,
    InputGenerator,
    OutputVerifier,
)
from agents.testing.test_validator import (
    FailureAnalyzer,
    QualityGateChecker,
    ResultChecker,
    TestValidator,
)
from agents.testing.unit_test_generator import UnitTestGenerator
from core.registry import AgentRegistry


logger = logging.getLogger("FractalCore.Testing")

__all__ = [
    # Orchestrator
    "TestOrchestrator",
    # Unit Testing
    "UnitTestGenerator",
    "HappyPathTester",
    "EdgeCaseHunter",
    "ErrorCaseTester",
    "InputGenerator",
    "OutputVerifier",
    "AssertionBuilder",
    # Integration Testing
    "IntegrationTestCreator",
    "APITester",
    "FlowTester",
    # Mocking
    "MockGenerator",
    "DataMocker",
    "DependencyMocker",
    # Test Data & Fixtures
    "TestDataCreator",
    "FixtureGenerator",
    "SeedGenerator",
    # Performance Testing
    "PerformanceTester",
    "LoadTester",
    "StressTester",
    # Coverage Analysis
    "CoverageAnalyzer",
    "LineCoverage",
    "BranchCoverage",
    "FunctionCoverage",
    # Validation & Quality Gates
    "TestValidator",
    "ResultChecker",
    "FailureAnalyzer",
    "QualityGateChecker",
    # Reporting
    "ReportGenerator",
    "HtmlReport",
    "JsonReport",
    "MarkdownReport",
    # Exceptions
    "TestingError",
    "TestGenerationError",
    "TestExecutionError",
    "MockGenerationError",
    "TestDataCreationError",
    "PerformanceTestError",
    "CoverageError",
    "ValidationError",
    "ReportGenerationError",
    # Registration Helper
    "register_all_testing_agents",
]


def register_all_testing_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Register all 16 testing layer agents into the AgentRegistry.

    Args:
        registry: The central AgentRegistry singleton.
        parent_agent: Optional supervising test coordinator agent.
        max_depth: Global depth ceiling for testing hierarchy.

    Returns:
        Dict mapping agent_id to instantiated agent instances.
    """
    logger.info("Registering all testing domain agents into AgentRegistry...")

    # Root Test Orchestrator (L3)
    test_orchestrator = TestOrchestrator(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="T1_TEST_ORCHESTRATOR",
        auto_spawn_subagents=True,
    )
    registry.register_agent(test_orchestrator)

    # Register all spawned children recursively
    registered_count = 1
    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(test_orchestrator)

    logger.info("Successfully registered %d testing domain agents into registry.", registered_count)
    return {
        "test_orchestrator": test_orchestrator,
        "total_registered": registered_count,
    }
