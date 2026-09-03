"""Comprehensive Test Suite for Testing & Validation Layer Agents (Session 12)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.registry import AgentRegistry
from tests import (
    CoverageReporter,
    IntegrationTestRunner,
    MockServer,
    PerformanceTestRunner,
    QualityTestRunner,
    ReportGenerator,
    ResultAggregator,
    SecurityTestRunner,
    SystemTestRunner,
    TestCleanup,
    TestDataSetup,
    TestOrchestrator,
    UnitTestRunner,
    ValidationEngine,
    register_all_testing_validation_agents,
)


class TestTestingValidationLayer(unittest.TestCase):
    """Test suite covering all 14 testing & validation agents, subagents, and execution flows."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_test_orchestrator_spawns_subsystems(self) -> None:
        """Verify TestOrchestrator spawns all 13 L4 testing coordinators."""
        orch = TestOrchestrator(agent_id="TEST_TV_ORCH", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(orch.system_runner)
        self.assertIsNotNone(orch.integration_runner)
        self.assertIsNotNone(orch.unit_runner)
        self.assertIsNotNone(orch.perf_runner)
        self.assertIsNotNone(orch.security_runner)
        self.assertIsNotNone(orch.quality_runner)
        self.assertIsNotNone(orch.validation_engine)
        self.assertIsNotNone(orch.coverage_reporter)
        self.assertIsNotNone(orch.data_setup)
        self.assertIsNotNone(orch.cleanup_mgr)
        self.assertIsNotNone(orch.mock_server)
        self.assertIsNotNone(orch.aggregator)
        self.assertIsNotNone(orch.report_gen)

        child_names = [c.name for c in orch.children.values()]
        self.assertIn("SystemTestRunner", child_names)
        self.assertIn("IntegrationTestRunner", child_names)
        self.assertIn("UnitTestRunner", child_names)
        self.assertIn("PerformanceTestRunner", child_names)
        self.assertIn("SecurityTestRunner", child_names)
        self.assertIn("QualityTestRunner", child_names)
        self.assertIn("ValidationEngine", child_names)
        self.assertIn("CoverageReporter", child_names)
        self.assertIn("TestDataSetup", child_names)
        self.assertIn("TestCleanup", child_names)
        self.assertIn("MockServer", child_names)
        self.assertIn("ResultAggregator", child_names)
        self.assertIn("ReportGenerator", child_names)

    def test_system_test_runner(self) -> None:
        """Verify SystemTestRunner coordinates E2E, User Flow, Admin Flow, and Error Flow."""
        runner = SystemTestRunner(agent_id="TEST_SYS", auto_spawn_subagents=True, max_depth=7)
        res = runner.run_system_tests({"target": "core_workflow"})
        self.assertTrue(res["all_passed"])
        self.assertTrue(res["e2e"]["passed"])
        self.assertTrue(res["user_flow"]["passed"])
        self.assertTrue(res["admin_flow"]["passed"])
        self.assertTrue(res["error_flow"]["passed"])

    def test_integration_test_runner(self) -> None:
        """Verify IntegrationTestRunner coordinates API, DB, External Service, and Event testing."""
        runner = IntegrationTestRunner(agent_id="TEST_INT", auto_spawn_subagents=True, max_depth=7)
        res = runner.run_integration_tests({"endpoint": "/api/v1/status"})
        self.assertTrue(res["all_passed"])
        self.assertTrue(res["api"]["passed"])
        self.assertTrue(res["database"]["passed"])
        self.assertTrue(res["external_services"]["passed"])
        self.assertTrue(res["events"]["passed"])

    def test_unit_test_runner(self) -> None:
        """Verify UnitTestRunner coordinates Agent, Utility, Model, and Helper testing."""
        runner = UnitTestRunner(agent_id="TEST_UNT", auto_spawn_subagents=True, max_depth=7)
        res = runner.run_unit_tests({"target_agent": "Orchestrator"})
        self.assertTrue(res["all_passed"])
        self.assertTrue(res["agents"]["passed"])
        self.assertTrue(res["utilities"]["passed"])
        self.assertTrue(res["models"]["passed"])
        self.assertTrue(res["helpers"]["passed"])

    def test_performance_test_runner(self) -> None:
        """Verify PerformanceTestRunner benchmarks load, stress, latency, and throughput."""
        runner = PerformanceTestRunner(agent_id="TEST_PERF", auto_spawn_subagents=True, max_depth=7)
        res = runner.run_performance_tests({"max_response_time_ms": 200, "concurrency": 50})
        self.assertTrue(res["all_passed"])
        self.assertTrue(res["load"]["passed"])
        self.assertTrue(res["stress"]["passed"])
        self.assertTrue(res["latency"]["passed"])
        self.assertTrue(res["throughput"]["passed"])

    def test_security_test_runner(self) -> None:
        """Verify SecurityTestRunner audits auth, injection, XSS, and compliance."""
        runner = SecurityTestRunner(agent_id="TEST_SEC", auto_spawn_subagents=True, max_depth=7)
        res = runner.run_security_tests({"compliance_standards": ["gdpr"]})
        self.assertTrue(res["all_passed"])
        self.assertTrue(res["auth"]["passed"])
        self.assertTrue(res["injection"]["passed"])
        self.assertTrue(res["xss"]["passed"])
        self.assertTrue(res["compliance"]["passed"])

    def test_quality_test_runner(self) -> None:
        """Verify QualityTestRunner audits code quality, docstrings, style, and complexity."""
        runner = QualityTestRunner(agent_id="TEST_QLT", auto_spawn_subagents=True, max_depth=7)
        res = runner.run_quality_tests({"code_quality_threshold": 85, "max_complexity": 10})
        self.assertTrue(res["all_passed"])
        self.assertTrue(res["code_quality"]["passed"])
        self.assertTrue(res["documentation"]["passed"])
        self.assertTrue(res["style"]["passed"])
        self.assertTrue(res["complexity"]["passed"])

    def test_validation_engine(self) -> None:
        """Verify ValidationEngine validates outputs, expectations, edge cases, and consistency."""
        engine = ValidationEngine(agent_id="TEST_VAL", auto_spawn_subagents=True, max_depth=7)
        res = engine.validate_execution({
            "result": {"status": "COMPLETED", "code": 0},
            "expected": {"status": "COMPLETED"},
            "actual": {"status": "COMPLETED"},
        })
        self.assertTrue(res["all_passed"])
        self.assertTrue(res["result_validation"]["passed"])
        self.assertTrue(res["expectation_check"]["passed"])
        self.assertTrue(res["edge_case_validation"]["passed"])
        self.assertTrue(res["consistency_check"]["passed"])

    def test_coverage_reporter(self) -> None:
        """Verify CoverageReporter checks line, branch, function, and file coverage."""
        reporter = CoverageReporter(agent_id="TEST_COV", auto_spawn_subagents=True, max_depth=7)
        res = reporter.generate_coverage_report({
            "line_coverage_min": 80,
            "branch_coverage_min": 70,
            "function_coverage_min": 90,
        })
        self.assertTrue(res["all_thresholds_met"])
        self.assertGreaterEqual(res["overall_coverage_pct"], 80.0)
        self.assertTrue(res["line_coverage"]["passed"])
        self.assertTrue(res["branch_coverage"]["passed"])
        self.assertTrue(res["function_coverage"]["passed"])

    def test_test_data_setup_and_cleanup(self) -> None:
        """Verify TestDataSetup provisions environment and TestCleanup releases artifacts."""
        setup_mgr = TestDataSetup(agent_id="TEST_SETUP", auto_spawn_subagents=True, max_depth=7)
        s_res = setup_mgr.setup_test_environment({"fixtures_path": "./tests/fixtures/"})
        self.assertTrue(s_res["all_setup_successful"])
        self.assertTrue(s_res["fixtures"]["passed"])
        self.assertTrue(s_res["seeds"]["passed"])
        self.assertTrue(s_res["mocks"]["passed"])
        self.assertTrue(s_res["environment"]["passed"])

        cleanup_mgr = TestCleanup(agent_id="TEST_CLEAN", auto_spawn_subagents=True, max_depth=7)
        c_res = cleanup_mgr.cleanup_test_artifacts()
        self.assertTrue(c_res["all_cleaned"])
        self.assertTrue(c_res["data"]["passed"])
        self.assertTrue(c_res["files"]["passed"])
        self.assertTrue(c_res["sessions"]["passed"])
        self.assertTrue(c_res["cache"]["passed"])

    def test_mock_server(self) -> None:
        """Verify MockServer provisions API, Database, Service, and Response mocks."""
        mock = MockServer(agent_id="TEST_MOCK", auto_spawn_subagents=True, max_depth=7)
        res = mock.provision_mock_environment({"api_mock_port": 8080, "service_mock_timeout": 30})
        self.assertTrue(res["mock_server_ready"])
        self.assertTrue(res["api_mock"]["running"])
        self.assertTrue(res["database_mock"]["ready"])
        self.assertTrue(res["service_mock"]["ready"])

    def test_result_aggregator(self) -> None:
        """Verify ResultAggregator collects, analyzes, groups, and summarizes test outcomes."""
        agg = ResultAggregator(agent_id="TEST_AGG", auto_spawn_subagents=True, max_depth=7)
        res = agg.aggregate_results({"suites": [{"status": "COMPLETED", "passed": True}]})
        self.assertEqual(res["verdict"], "PASSED")
        self.assertGreaterEqual(res["score"], 90.0)
        self.assertIn("system", res["groups"])

    def test_report_generator(self) -> None:
        """Verify ReportGenerator compiles HTML, JSON, Markdown, and JUnit reports."""
        gen = ReportGenerator(agent_id="TEST_REP", auto_spawn_subagents=True, max_depth=7)
        res = gen.generate_all_reports({"title": "Fractal Test Run"})
        self.assertTrue(res["all_reports_generated"])
        self.assertTrue(res["html"]["generated"])
        self.assertTrue(res["json"]["generated"])
        self.assertTrue(res["markdown"]["generated"])
        self.assertTrue(res["junit"]["generated"])

    def test_test_orchestrator_full_cycle(self) -> None:
        """Verify TestOrchestrator runs full lifecycle across all 13 subsystems."""
        orch = TestOrchestrator(agent_id="TEST_FULL_CYCLE", auto_spawn_subagents=True, max_depth=7)
        envelope = {"task_id": "T_FULL_TEST", "payload": {}}
        res = orch.execute_lifecycle(envelope)

        self.assertEqual(res["status"], "COMPLETED")
        rep = res["overall_test_report"]
        self.assertTrue(rep["all_tests_passed"])
        self.assertEqual(rep["verdict"], "PASSED")
        self.assertTrue(rep["setup"])
        self.assertTrue(rep["mock"])
        self.assertTrue(rep["system"])
        self.assertTrue(rep["integration"])
        self.assertTrue(rep["unit"])
        self.assertTrue(rep["performance"])
        self.assertTrue(rep["security"])
        self.assertTrue(rep["quality"])
        self.assertTrue(rep["validation"])
        self.assertTrue(rep["cleanup"])

    def test_register_all_testing_validation_agents(self) -> None:
        """Verify register_all_testing_validation_agents registers all agents into AgentRegistry."""
        res = register_all_testing_validation_agents(self.registry, max_depth=7)
        total = res["total_registered"]
        self.assertGreaterEqual(total, 14)
        self.assertIsNotNone(self.registry.get_agent("TV1_TEST_ORCHESTRATOR"))


if __name__ == "__main__":
    unittest.main()
