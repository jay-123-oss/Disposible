"""Unit tests for the User Acceptance Testing (UAT) Layer (UA1-UA14 + 52 subagents + test cases)."""

import json
from pathlib import Path
import unittest

from core.registry import AgentRegistry
from uat.acceptance_criteria_checker import AcceptanceCriteriaChecker
from uat.business_flow_tester import BusinessFlowTester
from uat.data_integrity_checker import DataIntegrityChecker
from uat.end_to_end_tester import EndToEndTester
from uat.exceptions import UATError
from uat.integration_validator import IntegrationValidator
from uat.performance_validator import PerformanceValidator
from uat.role_based_tester import RoleBasedTester
from uat.security_validator import SecurityValidator
from uat.uat_orchestrator import UATOrchestrator
from uat.use_case_validator import UseCaseValidator
from uat.user_feedback_collector import UserFeedbackCollector
from uat.user_interface_tester import UserInterfaceTester
from uat.user_scenario_tester import UserScenarioTester
from uat.workflow_validator import WorkflowValidator
from uat import register_all_uat_agents
from uat.test_cases import load_test_cases


class TestUATAUT(unittest.TestCase):
    """Test suite verifying all UAT coordinators, workers, test cases, and signoff criteria."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()
        self.orchestrator = UATOrchestrator(agent_id="UA1_TEST_ORCHESTRATOR")

    def tearDown(self) -> None:
        self.registry.clear()

    def test_01_all_24_files_exist(self) -> None:
        """Verify all 24 UAT layer files exist and are non-empty."""
        expected_files = [
            "uat/__init__.py",
            "uat/uat_orchestrator.py",
            "uat/end_to_end_tester.py",
            "uat/user_scenario_tester.py",
            "uat/business_flow_tester.py",
            "uat/role_based_tester.py",
            "uat/use_case_validator.py",
            "uat/acceptance_criteria_checker.py",
            "uat/user_interface_tester.py",
            "uat/workflow_validator.py",
            "uat/integration_validator.py",
            "uat/data_integrity_checker.py",
            "uat/security_validator.py",
            "uat/performance_validator.py",
            "uat/user_feedback_collector.py",
            "uat/uat_config.yaml",
            "uat/uat_acceptance_report_template.md",
            "uat/user_acceptance_checklist.md",
            "uat/uat_signoff_template.md",
            "uat/test_cases/__init__.py",
            "uat/test_cases/user_scenarios.json",
            "uat/test_cases/business_flows.json",
            "uat/test_cases/acceptance_criteria.json",
            "uat/test_cases/uat_test_suite.json",
            "uat/exceptions.py",
        ]
        base_dir = Path(__file__).parent.parent
        for rel_path in expected_files:
            p = base_dir / rel_path
            self.assertTrue(p.exists(), f"File does not exist: {rel_path}")
            self.assertGreater(p.stat().st_size, 0, f"File is empty: {rel_path}")

    def test_02_orchestrator_spawns_all_13_coordinators(self) -> None:
        """Verify UATOrchestrator instantiates all 13 coordinators."""
        coordinators = [
            self.orchestrator.e2e_tst,
            self.orchestrator.scen_tst,
            self.orchestrator.biz_tst,
            self.orchestrator.role_tst,
            self.orchestrator.use_val,
            self.orchestrator.crit_chk,
            self.orchestrator.ui_tst,
            self.orchestrator.wf_val,
            self.orchestrator.int_val,
            self.orchestrator.data_chk,
            self.orchestrator.sec_val,
            self.orchestrator.perf_val,
            self.orchestrator.feed_col,
        ]
        for coord in coordinators:
            self.assertIsNotNone(coord)
            self.assertEqual(coord.depth, 1)

    def test_03_each_coordinator_spawns_4_grandchild_agents(self) -> None:
        """Verify each of the 13 coordinators instantiates 4 atomic grandchild workers (depth=2)."""
        coordinators = [
            (self.orchestrator.e2e_tst, 4),
            (self.orchestrator.scen_tst, 4),
            (self.orchestrator.biz_tst, 4),
            (self.orchestrator.role_tst, 4),
            (self.orchestrator.use_val, 4),
            (self.orchestrator.crit_chk, 4),
            (self.orchestrator.ui_tst, 4),
            (self.orchestrator.wf_val, 4),
            (self.orchestrator.int_val, 4),
            (self.orchestrator.data_chk, 4),
            (self.orchestrator.sec_val, 4),
            (self.orchestrator.perf_val, 4),
            (self.orchestrator.feed_col, 4),
        ]
        for coord, expected_count in coordinators:
            self.assertEqual(len(coord.children), expected_count)
            for sub in coord.children.values():
                self.assertEqual(sub.depth, 2)

    def test_04_registry_registers_all_66_agents(self) -> None:
        """Verify registration helper registers exactly 66 agents (1 + 13 + 52) within memory limits."""
        res = register_all_uat_agents(self.registry, self.orchestrator)
        self.assertEqual(res["total_registered"], 66)
        all_agents = self.registry.get_all_agents()
        self.assertEqual(len(all_agents), 66)
        self.assertLessEqual(self.registry._allocated_ram_mb, 8192)

    def test_05_end_to_end_tester_execution(self) -> None:
        """Verify EndToEndTester runs register, login, crud, and admin flows."""
        res = self.orchestrator.e2e_tst.run_e2e_tests()
        self.assertTrue(res["all_e2e_passed"])

    def test_06_user_scenario_tester_execution(self) -> None:
        """Verify UserScenarioTester executes new, existing, admin, and guest journeys."""
        res = self.orchestrator.scen_tst.run_user_scenarios()
        self.assertTrue(res["all_scenarios_passed"])

    def test_07_business_flow_tester_execution(self) -> None:
        """Verify BusinessFlowTester executes order, payment, notification, and reporting flows."""
        res = self.orchestrator.biz_tst.run_business_flows()
        self.assertTrue(res["all_flows_passed"])

    def test_08_role_based_tester_execution(self) -> None:
        """Verify RoleBasedTester validates RBAC boundaries for admin, user, manager, guest."""
        res = self.orchestrator.role_tst.run_role_tests()
        self.assertTrue(res["all_roles_passed"])

    def test_09_use_case_validator_execution(self) -> None:
        """Verify UseCaseValidator checks primary, secondary, edge, and exceptional cases."""
        res = self.orchestrator.use_val.validate_use_cases()
        self.assertTrue(res["all_use_cases_passed"])

    def test_10_acceptance_criteria_checker_execution(self) -> None:
        """Verify AcceptanceCriteriaChecker validates functional, non-functional, UI, performance."""
        res = self.orchestrator.crit_chk.check_all_criteria()
        self.assertTrue(res["all_criteria_met"])

    def test_11_user_interface_tester_execution(self) -> None:
        """Verify UserInterfaceTester audits navigation, responsiveness, a11y, usability."""
        res = self.orchestrator.ui_tst.run_ui_tests()
        self.assertTrue(res["all_ui_passed"])

    def test_12_workflow_validator_execution(self) -> None:
        """Verify WorkflowValidator validates approval, review, publish, and archive lifecycles."""
        res = self.orchestrator.wf_val.validate_workflows()
        self.assertTrue(res["all_workflows_passed"])

    def test_13_integration_validator_execution(self) -> None:
        """Verify IntegrationValidator tests API, DB, external services, and event bus."""
        res = self.orchestrator.int_val.validate_integrations()
        self.assertTrue(res["all_integrations_passed"])

    def test_14_data_integrity_checker_execution(self) -> None:
        """Verify DataIntegrityChecker validates consistency, accuracy, completeness, validity."""
        res = self.orchestrator.data_chk.check_data_integrity()
        self.assertTrue(res["all_integrity_passed"])

    def test_15_security_validator_execution(self) -> None:
        """Verify SecurityValidator checks auth, authorization, data protection, compliance."""
        res = self.orchestrator.sec_val.validate_security()
        self.assertTrue(res["all_security_passed"])

    def test_16_performance_validator_execution(self) -> None:
        """Verify PerformanceValidator audits response time, throughput, resources, scaling."""
        res = self.orchestrator.perf_val.validate_performance()
        self.assertTrue(res["all_performance_passed"])

    def test_17_user_feedback_collector_execution(self) -> None:
        """Verify UserFeedbackCollector surveys, sentiment, satisfaction (>=4.5/5), suggestions."""
        res = self.orchestrator.feed_col.collect_user_feedback()
        self.assertTrue(res["all_feedback_passed"])
        self.assertGreaterEqual(res["satisfaction"]["average_score"], 4.5)

    def test_18_acceptance_criteria_matrix_and_signoff(self) -> None:
        """Verify UAT acceptance criteria verification matrix and approval."""
        matrix = self.orchestrator.verify_acceptance_criteria()
        self.assertTrue(matrix["overall_approved"])
        self.assertGreaterEqual(matrix["actual_composite_score"], 85)

    def test_19_full_uat_orchestrator_lifecycle(self) -> None:
        """Verify complete orchestrator run across all 13 subsystems and signoff receipt."""
        envelope = {"payload": {"uat_run_id": "UAT_RELEASE_1_0"}}
        self.orchestrator.initialize(envelope)
        result = self.orchestrator.process(envelope)
        validated = self.orchestrator.validate(result)
        self.assertEqual(validated["status"], "COMPLETED")
        self.assertTrue(validated["uat_report"]["uat_passed"])
        self.assertTrue(validated["uat_report"]["signoff_obtained"])
        self.orchestrator.cleanup()

    def test_20_load_json_test_cases(self) -> None:
        """Verify all JSON test suites can be loaded and are non-empty."""
        for filename in ["user_scenarios.json", "business_flows.json", "acceptance_criteria.json", "uat_test_suite.json"]:
            data = load_test_cases(filename)
            self.assertIsInstance(data, dict)
            self.assertGreater(len(data), 0)


if __name__ == "__main__":
    unittest.main()
