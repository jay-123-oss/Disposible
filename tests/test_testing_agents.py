"""Comprehensive Unit Test Suite for Testing Layer Agents (Session 5)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.testing import (
    APITester,
    AssertionBuilder,
    BranchCoverage,
    CoverageAnalyzer,
    DataMocker,
    DependencyMocker,
    EdgeCaseHunter,
    ErrorCaseTester,
    FailureAnalyzer,
    FixtureGenerator,
    FlowTester,
    FunctionCoverage,
    HappyPathTester,
    HtmlReport,
    InputGenerator,
    IntegrationTestCreator,
    JsonReport,
    LineCoverage,
    LoadTester,
    MarkdownReport,
    MockGenerator,
    OutputVerifier,
    PerformanceTester,
    QualityGateChecker,
    ReportGenerator,
    ResultChecker,
    SeedGenerator,
    StressTester,
    TestDataCreator,
    TestOrchestrator,
    TestValidator,
    UnitTestGenerator,
    register_all_testing_agents,
)
from core.registry import AgentRegistry


class TestTestingAgents(unittest.TestCase):
    """Test suite covering all 16 Testing domain agents and fractal subagent structures."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_test_orchestrator_spawns_subsystems(self) -> None:
        """Verify TestOrchestrator spawns all 8 L4 testing coordinators."""
        orch = TestOrchestrator(agent_id="TEST_ORCH", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(orch.unit_test_agent)
        self.assertIsNotNone(orch.integration_test_agent)
        self.assertIsNotNone(orch.mock_agent)
        self.assertIsNotNone(orch.test_data_agent)
        self.assertIsNotNone(orch.performance_agent)
        self.assertIsNotNone(orch.coverage_agent)
        self.assertIsNotNone(orch.validator_agent)
        self.assertIsNotNone(orch.report_agent)

        child_names = [c.name for c in orch.children.values()]
        self.assertIn("UnitTestGenerator", child_names)
        self.assertIn("IntegrationTestCreator", child_names)
        self.assertIn("MockGenerator", child_names)
        self.assertIn("TestDataCreator", child_names)
        self.assertIn("PerformanceTester", child_names)
        self.assertIn("CoverageAnalyzer", child_names)
        self.assertIn("TestValidator", child_names)
        self.assertIn("ReportGenerator", child_names)

    def test_unit_test_generator_spawns_scenarios(self) -> None:
        """Verify UnitTestGenerator spawns HappyPath, EdgeCase, and ErrorCase agents."""
        ut = UnitTestGenerator(agent_id="TEST_UT", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(ut.happy_path_agent)
        self.assertIsNotNone(ut.edge_case_agent)
        self.assertIsNotNone(ut.error_case_agent)

        self.assertIsInstance(ut.happy_path_agent, HappyPathTester)
        self.assertIsInstance(ut.edge_case_agent, EdgeCaseHunter)
        self.assertIsInstance(ut.error_case_agent, ErrorCaseTester)

    def test_happy_path_tester_spawns_atomic_workers(self) -> None:
        """Verify HappyPathTester spawns InputGenerator, OutputVerifier, and AssertionBuilder."""
        hp = HappyPathTester(agent_id="TEST_HP")
        self.assertIsNotNone(hp.input_gen)
        self.assertIsNotNone(hp.output_ver)
        self.assertIsNotNone(hp.assertion_bld)

        self.assertIsInstance(hp.input_gen, InputGenerator)
        self.assertIsInstance(hp.output_ver, OutputVerifier)
        self.assertIsInstance(hp.assertion_bld, AssertionBuilder)

    def test_integration_test_creator_spawns_subsystems(self) -> None:
        """Verify IntegrationTestCreator spawns APITester and FlowTester."""
        it = IntegrationTestCreator(agent_id="TEST_IT", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(it.api_tester)
        self.assertIsNotNone(it.flow_tester)

        self.assertIsInstance(it.api_tester, APITester)
        self.assertIsInstance(it.flow_tester, FlowTester)

    def test_mock_generator_spawns_mockers(self) -> None:
        """Verify MockGenerator spawns DataMocker and DependencyMocker."""
        mg = MockGenerator(agent_id="TEST_MG", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(mg.data_mocker)
        self.assertIsNotNone(mg.dependency_mocker)

        self.assertIsInstance(mg.data_mocker, DataMocker)
        self.assertIsInstance(mg.dependency_mocker, DependencyMocker)

    def test_test_data_creator_spawns_generators(self) -> None:
        """Verify TestDataCreator spawns FixtureGenerator and SeedGenerator."""
        td = TestDataCreator(agent_id="TEST_TD", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(td.fixture_generator)
        self.assertIsNotNone(td.seed_generator)

        self.assertIsInstance(td.fixture_generator, FixtureGenerator)
        self.assertIsInstance(td.seed_generator, SeedGenerator)

    def test_performance_tester_spawns_subsystems(self) -> None:
        """Verify PerformanceTester spawns LoadTester and StressTester."""
        pt = PerformanceTester(agent_id="TEST_PT", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(pt.load_tester)
        self.assertIsNotNone(pt.stress_tester)

        self.assertIsInstance(pt.load_tester, LoadTester)
        self.assertIsInstance(pt.stress_tester, StressTester)

    def test_coverage_analyzer_spawns_calculators(self) -> None:
        """Verify CoverageAnalyzer spawns LineCoverage, BranchCoverage, and FunctionCoverage."""
        ca = CoverageAnalyzer(agent_id="TEST_CA", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(ca.line_cov)
        self.assertIsNotNone(ca.branch_cov)
        self.assertIsNotNone(ca.func_cov)

        self.assertIsInstance(ca.line_cov, LineCoverage)
        self.assertIsInstance(ca.branch_cov, BranchCoverage)
        self.assertIsInstance(ca.func_cov, FunctionCoverage)

    def test_test_validator_spawns_subsystems(self) -> None:
        """Verify TestValidator spawns ResultChecker, FailureAnalyzer, and QualityGateChecker."""
        tv = TestValidator(agent_id="TEST_TV", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(tv.result_checker)
        self.assertIsNotNone(tv.failure_analyzer)
        self.assertIsNotNone(tv.gate_checker)

        self.assertIsInstance(tv.result_checker, ResultChecker)
        self.assertIsInstance(tv.failure_analyzer, FailureAnalyzer)
        self.assertIsInstance(tv.gate_checker, QualityGateChecker)

    def test_report_generator_spawns_exporters(self) -> None:
        """Verify ReportGenerator spawns HtmlReport, JsonReport, and MarkdownReport."""
        rg = ReportGenerator(agent_id="TEST_RG", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(rg.html_rep)
        self.assertIsNotNone(rg.json_rep)
        self.assertIsNotNone(rg.md_rep)

        self.assertIsInstance(rg.html_rep, HtmlReport)
        self.assertIsInstance(rg.json_rep, JsonReport)
        self.assertIsInstance(rg.md_rep, MarkdownReport)

    def test_test_orchestrator_end_to_end_pipeline(self) -> None:
        """Verify TestOrchestrator executes full pipeline, validates coverage, and outputs reports."""
        orch = TestOrchestrator(agent_id="TEST_ORCH_E2E", auto_spawn_subagents=True, max_depth=7)
        envelope = {
            "task_id": "T_TESTING_E2E",
            "payload": {"entity": "account", "functions": ["register_account", "login_account"]},
        }
        result = orch.execute_lifecycle(envelope)

        self.assertEqual(result["status"], "COMPLETED")
        pipeline = result["pipeline_results"]
        self.assertIn("unit_tests", pipeline)
        self.assertIn("integration_tests", pipeline)
        self.assertIn("mocks", pipeline)
        self.assertIn("fixtures", pipeline)
        self.assertIn("performance", pipeline)
        self.assertIn("coverage", pipeline)
        self.assertIn("validation", pipeline)
        self.assertIn("reports", pipeline)
        self.assertTrue(pipeline["validation"]["gate_approved"])
        self.assertIn("markdown", pipeline["reports"])

    def test_register_all_testing_agents(self) -> None:
        """Verify registration helper registers all testing agents into AgentRegistry."""
        res = register_all_testing_agents(self.registry, max_depth=7)
        total = res["total_registered"]
        self.assertGreaterEqual(total, 16)
        self.assertIsNotNone(self.registry.get_agent("T1_TEST_ORCHESTRATOR"))


if __name__ == "__main__":
    unittest.main()
