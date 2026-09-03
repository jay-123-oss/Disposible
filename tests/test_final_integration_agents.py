"""Unit tests for the Final System Integration & Deployment Layer (FI1-FI14 + 52 subagents + scripts)."""

from pathlib import Path
import subprocess
import sys
import unittest

from core.registry import AgentRegistry
from final_integration import (
    CodeValidator,
    ComplianceCheckerUtil,
    ConfigurationMerger,
    DependencyResolver,
    DeploymentExecutor,
    FinalIntegrationError,
    FinalIntegrationOrchestrator,
    FinalSignoffCollector,
    GoLiveManager,
    HandoverManager,
    HealthVerifier,
    PostDeploymentVerifier,
    QualityCheckerUtil,
    RollbackCoordinator,
    ServiceOrchestrator,
    SmokeTester,
    SystemAssembler,
    register_all_final_integration_agents,
)


class TestFinalIntegration(unittest.TestCase):
    """Test suite verifying all final integration coordinators, workers, scripts, and signoff criteria."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()
        self.orchestrator = FinalIntegrationOrchestrator(agent_id="FI1_TEST_ORCHESTRATOR")

    def tearDown(self) -> None:
        self.registry.clear()

    def test_01_all_28_files_exist(self) -> None:
        """Verify all 28 final integration files exist and are non-empty."""
        expected_files = [
            "final_integration/__init__.py",
            "final_integration/final_integration_orchestrator.py",
            "final_integration/system_assembler.py",
            "final_integration/dependency_resolver.py",
            "final_integration/configuration_merger.py",
            "final_integration/code_validator.py",
            "final_integration/quality_checker.py",
            "final_integration/compliance_checker.py",
            "final_integration/deployment_executor.py",
            "final_integration/service_orchestrator.py",
            "final_integration/health_verifier.py",
            "final_integration/go_live_manager.py",
            "final_integration/smoke_tester.py",
            "final_integration/rollback_coordinator.py",
            "final_integration/post_deployment_verifier.py",
            "final_integration/handover_manager.py",
            "final_integration/final_signoff_collector.py",
            "deploy.py",
            "deploy.sh",
            "deploy.bat",
            "verify_deployment.py",
            "smoke_test.py",
            "rollback.py",
            "go_live.py",
            "final_integration/deployment_config.yaml",
            "final_integration/checklist.md",
            "final_integration/signoff_template.md",
            "final_integration/handover_documentation_template.md",
        ]
        base_dir = Path(__file__).parent.parent
        for rel_path in expected_files:
            p = base_dir / rel_path
            self.assertTrue(p.exists(), f"File does not exist: {rel_path}")
            self.assertGreater(p.stat().st_size, 0, f"File is empty: {rel_path}")

    def test_02_orchestrator_spawns_all_13_coordinators(self) -> None:
        """Verify FinalIntegrationOrchestrator instantiates all 13 coordinators."""
        coordinators = [
            self.orchestrator.sys_asm,
            self.orchestrator.dep_res,
            self.orchestrator.cfg_mrg,
            self.orchestrator.code_val,
            self.orchestrator.dep_exec,
            self.orchestrator.srv_orch,
            self.orchestrator.hlth_ver,
            self.orchestrator.golive_mgr,
            self.orchestrator.smk_tst,
            self.orchestrator.rlb_coord,
            self.orchestrator.post_ver,
            self.orchestrator.hnd_mgr,
            self.orchestrator.sig_col,
        ]
        for coord in coordinators:
            self.assertIsNotNone(coord)
            self.assertEqual(coord.depth, 1)

    def test_03_each_coordinator_spawns_4_grandchild_agents(self) -> None:
        """Verify each of the 13 coordinators instantiates 4 atomic grandchild workers (depth=2)."""
        coordinators = [
            (self.orchestrator.sys_asm, 4),
            (self.orchestrator.dep_res, 4),
            (self.orchestrator.cfg_mrg, 4),
            (self.orchestrator.code_val, 4),
            (self.orchestrator.dep_exec, 4),
            (self.orchestrator.srv_orch, 4),
            (self.orchestrator.hlth_ver, 4),
            (self.orchestrator.golive_mgr, 4),
            (self.orchestrator.smk_tst, 4),
            (self.orchestrator.rlb_coord, 4),
            (self.orchestrator.post_ver, 4),
            (self.orchestrator.hnd_mgr, 4),
            (self.orchestrator.sig_col, 4),
        ]
        for coord, expected_count in coordinators:
            self.assertEqual(len(coord.children), expected_count)
            for sub in coord.children.values():
                self.assertEqual(sub.depth, 2)

    def test_04_registry_registers_all_66_agents(self) -> None:
        """Verify registration helper registers exactly 66 agents (1 + 13 + 52) within memory limits."""
        res = register_all_final_integration_agents(self.registry, self.orchestrator)
        self.assertEqual(res["total_registered"], 66)
        all_agents = self.registry.get_all_agents()
        self.assertEqual(len(all_agents), 66)
        self.assertLessEqual(self.registry._allocated_ram_mb, 8192)

    def test_05_system_assembler_execution(self) -> None:
        """Verify SystemAssembler gathers components, validates, and checks integrity."""
        res = self.orchestrator.sys_asm.assemble_system()
        self.assertTrue(res["all_assembly_passed"])

    def test_06_dependency_resolver_execution(self) -> None:
        """Verify DependencyResolver extracts imports, pins versions, resolves conflicts."""
        res = self.orchestrator.dep_res.resolve_dependencies()
        self.assertTrue(res["all_dependencies_resolved"])

    def test_07_configuration_merger_execution(self) -> None:
        """Verify ConfigurationMerger collects, validates, merges, and tests config maps."""
        res = self.orchestrator.cfg_mrg.merge_configurations()
        self.assertTrue(res["all_configurations_merged"])

    def test_08_code_validator_execution(self) -> None:
        """Verify CodeValidator checks syntax, types, linting, and quality metrics."""
        res = self.orchestrator.code_val.validate_all_code()
        self.assertTrue(res["all_code_valid"])

    def test_09_quality_and_compliance_utilities(self) -> None:
        """Verify QualityCheckerUtil and ComplianceCheckerUtil static evaluations."""
        q_res = QualityCheckerUtil.evaluate_quality()
        self.assertTrue(q_res["quality_passed"])
        c_res = ComplianceCheckerUtil.audit_compliance()
        self.assertTrue(c_res["compliance_passed"])

    def test_10_deployment_executor_execution(self) -> None:
        """Verify DeploymentExecutor triggers Docker, K8s, Cloud, and Local targets."""
        res = self.orchestrator.dep_exec.execute_deployment()
        self.assertTrue(res["all_deployments_successful"])

    def test_11_service_orchestrator_execution(self) -> None:
        """Verify ServiceOrchestrator manages starting, connecting, health probing, and monitoring."""
        res = self.orchestrator.srv_orch.orchestrate_services()
        self.assertTrue(res["all_services_orchestrated"])

    def test_12_health_verifier_execution(self) -> None:
        """Verify HealthVerifier audits system resources, agent heartbeat, services, and latency."""
        res = self.orchestrator.hlth_ver.verify_system_health()
        self.assertTrue(res["all_health_verified"])

    def test_13_go_live_manager_execution(self) -> None:
        """Verify GoLiveManager performs readiness check, approvals, cutover, and announcements."""
        res = self.orchestrator.golive_mgr.manage_go_live()
        self.assertTrue(res["go_live_successful"])

    def test_14_smoke_tester_execution(self) -> None:
        """Verify SmokeTester checks critical flows, APIs, UI, and integration paths."""
        res = self.orchestrator.smk_tst.run_smoke_tests()
        self.assertTrue(res["all_smoke_tests_passed"])

    def test_15_rollback_coordinator_execution(self) -> None:
        """Verify RollbackCoordinator plans, executes, verifies, and communicates rollback."""
        res = self.orchestrator.rlb_coord.coordinate_rollback()
        self.assertTrue(res["rollback_successful"])

    def test_16_post_deployment_verifier_execution(self) -> None:
        """Verify PostDeploymentVerifier tests functional, performance, security, and user pillars."""
        res = self.orchestrator.post_ver.verify_post_deployment()
        self.assertTrue(res["all_post_deployment_verified"])

    def test_17_handover_manager_execution(self) -> None:
        """Verify HandoverManager prepares docs, training materials, ops guides, and meetings."""
        res = self.orchestrator.hnd_mgr.manage_handover()
        self.assertTrue(res["handover_successful"])

    def test_18_final_signoff_collector_execution(self) -> None:
        """Verify FinalSignoffCollector checklists, approvals, signatures, and final release certificate."""
        res = self.orchestrator.sig_col.collect_final_signoff()
        self.assertTrue(res["final_signoff_obtained"])

    def test_19_full_orchestrator_lifecycle(self) -> None:
        """Verify full lifecycle run across all 13 subsystems yielding PRODUCTION_READY."""
        envelope = {"payload": {"deploy_type": "docker"}}
        self.orchestrator.initialize(envelope)
        result = self.orchestrator.process(envelope)
        validated = self.orchestrator.validate(result)
        self.assertEqual(validated["status"], "COMPLETED")
        self.assertTrue(validated["final_integration_report"]["integration_successful"])
        self.assertEqual(validated["final_integration_report"]["overall_status"], "PRODUCTION_READY")
        self.orchestrator.cleanup()

    def test_20_standalone_scripts_execution(self) -> None:
        """Verify standalone execution of deploy.py, verify_deployment.py, smoke_test.py, rollback.py, go_live.py."""
        base_dir = Path(__file__).parent.parent
        scripts = ["deploy.py", "verify_deployment.py", "smoke_test.py", "rollback.py", "go_live.py"]
        for s in scripts:
            script_path = base_dir / s
            proc = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, f"Script failed: {s}\nStdout: {proc.stdout}\nStderr: {proc.stderr}")


if __name__ == "__main__":
    unittest.main()
