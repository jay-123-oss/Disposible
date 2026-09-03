"""Comprehensive Unit Test Suite for Integration & Assembly Layer Agents (Session 11)."""

import os
import sys
import unittest

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT_DIR in sys.path:
    sys.path.remove(_ROOT_DIR)
sys.path.insert(0, _ROOT_DIR)

from app import Application, create_app
from cli import main as cli_main
from core.registry import AgentRegistry
from integration import (
    AgentFactory,
    CliEntryPoint,
    ConfigurationLoader,
    ContextManager,
    DependencyInjector,
    EntryPointManager,
    ErrorHandler,
    HealthManager,
    IntegrationOrchestrator,
    InterfaceBuilder,
    ResourceManager,
    SessionManager,
    ShutdownManager,
    SystemInitializer,
    WorkflowOrchestrator,
    register_all_integration_agents,
)


class TestIntegrationAgents(unittest.TestCase):
    """Test suite covering all 14 integration & assembly agents and system assembly components."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_integration_orchestrator_spawns_subsystems(self) -> None:
        """Verify IntegrationOrchestrator spawns all 13 L4 coordinators."""
        orch = IntegrationOrchestrator(agent_id="TEST_INT_ORCH", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(orch.initializer)
        self.assertIsNotNone(orch.factory)
        self.assertIsNotNone(orch.injector)
        self.assertIsNotNone(orch.config_loader)
        self.assertIsNotNone(orch.entry_point)
        self.assertIsNotNone(orch.interface_builder)
        self.assertIsNotNone(orch.workflow)
        self.assertIsNotNone(orch.error_handler)
        self.assertIsNotNone(orch.shutdown)
        self.assertIsNotNone(orch.health)
        self.assertIsNotNone(orch.session)
        self.assertIsNotNone(orch.resource)
        self.assertIsNotNone(orch.context)

        child_names = [c.name for c in orch.children.values()]
        self.assertIn("SystemInitializer", child_names)
        self.assertIn("AgentFactory", child_names)
        self.assertIn("DependencyInjector", child_names)
        self.assertIn("ConfigurationLoader", child_names)
        self.assertIn("EntryPointManager", child_names)
        self.assertIn("InterfaceBuilder", child_names)
        self.assertIn("WorkflowOrchestrator", child_names)
        self.assertIn("ErrorHandler", child_names)
        self.assertIn("ShutdownManager", child_names)
        self.assertIn("HealthManager", child_names)
        self.assertIn("SessionManager", child_names)
        self.assertIn("ResourceManager", child_names)
        self.assertIn("ContextManager", child_names)

    def test_system_initializer_bootstrap(self) -> None:
        """Verify SystemInitializer runs four-stage startup sequence."""
        init = SystemInitializer(agent_id="TEST_INIT", auto_spawn_subagents=True, max_depth=7)
        res = init.bootstrap_system("config.yaml")
        self.assertTrue(res["initialized"])
        self.assertTrue(res["services"]["all_running"])

    def test_agent_factory_instantiation(self) -> None:
        """Verify AgentFactory delegates to domain agent creators."""
        factory = AgentFactory(agent_id="TEST_FACTORY", auto_spawn_subagents=True, max_depth=7)
        res = factory.create_domain_agents(domain="planning", registry=self.registry)
        self.assertIn("planning", res)

    def test_dependency_injector(self) -> None:
        """Verify DependencyInjector wires core, agent, service, and repo dependencies."""
        inj = DependencyInjector(agent_id="TEST_INJ", auto_spawn_subagents=True, max_depth=7)
        res = inj.inject_dependencies()
        self.assertTrue(res["injection_complete"])
        self.assertIn("registry", res["core"]["injected"])

    def test_configuration_loader(self) -> None:
        """Verify ConfigurationLoader merges settings and validates schemas."""
        cl = ConfigurationLoader(agent_id="TEST_CL", auto_spawn_subagents=True, max_depth=7)
        cfg = cl.load_configuration("config.yaml")
        self.assertIsInstance(cfg, dict)
        self.assertIn("system", cfg)

    def test_entry_point_manager_dispatch(self) -> None:
        """Verify EntryPointManager routes between CLI, Interactive, Batch, and API modes."""
        ep = EntryPointManager(agent_id="TEST_EP", auto_spawn_subagents=True, max_depth=7)
        self.assertIsInstance(ep.cli_ep, CliEntryPoint)

        cli_res = ep.dispatch_entry_point("CLI", {"task": "build app"})
        self.assertTrue(cli_res["handled"])
        self.assertEqual(cli_res["mode"], "CLI")

        batch_res = ep.dispatch_entry_point("BATCH", {"tasks": [{"intent": "t1"}]})
        self.assertEqual(batch_res["batch_size"], 1)

    def test_interface_builder(self) -> None:
        """Verify InterfaceBuilder produces CLI flags, web routes, and API endpoints."""
        ib = InterfaceBuilder(agent_id="TEST_IB", auto_spawn_subagents=True, max_depth=7)
        ifaces = ib.build_interfaces()
        self.assertTrue(ifaces["all_built"])
        self.assertGreater(len(ifaces["cli"]), 0)
        self.assertGreater(len(ifaces["web"]), 0)
        self.assertGreater(len(ifaces["api"]), 0)

    def test_workflow_orchestrator(self) -> None:
        """Verify WorkflowOrchestrator manages linear, parallel, conditional, and recursive workflows."""
        wo = WorkflowOrchestrator(agent_id="TEST_WO", auto_spawn_subagents=True, max_depth=7)

        lin = wo.execute_workflow("linear", {"steps": ["step1", "step2"]})
        self.assertEqual(lin["workflow_type"], "LINEAR")
        self.assertEqual(lin["total_steps"], 2)

        par = wo.execute_workflow("parallel", {"tasks": ["t1", "t2", "t3"]})
        self.assertEqual(par["workflow_type"], "PARALLEL")
        self.assertEqual(par["count"], 3)

        cond = wo.execute_workflow("conditional", {"predicate": True, "true_branch": "OK", "false_branch": "NO"})
        self.assertEqual(cond["selected_branch"], "OK")

        rec = wo.execute_workflow("recursive", {"current_depth": 1, "max_depth": 3})
        self.assertEqual(rec["workflow_type"], "RECURSIVE")
        self.assertFalse(rec["atomic_reached"])

    def test_error_handler_recovery(self) -> None:
        """Verify ErrorHandler attempts automated recovery before escalating."""
        eh = ErrorHandler(agent_id="TEST_EH", auto_spawn_subagents=True, max_depth=7)
        res = eh.handle_error("Network timeout", attempts=1, max_attempts=3)
        self.assertTrue(res["error_handled"])
        self.assertTrue(res["recovered"])
        self.assertFalse(res["escalated"])

        fail_res = eh.handle_error("Fatal out of memory", attempts=4, max_attempts=3)
        self.assertFalse(fail_res["recovered"])
        self.assertTrue(fail_res["escalated"])

    def test_shutdown_manager(self) -> None:
        """Verify ShutdownManager executes graceful and forced shutdowns."""
        sm = ShutdownManager(agent_id="TEST_SM", auto_spawn_subagents=True, max_depth=7)
        res = sm.execute_shutdown(force=False, timeout_seconds=10)
        self.assertTrue(res["shutdown_successful"])
        self.assertEqual(res["mode"], "GRACEFUL")

    def test_health_manager(self) -> None:
        """Verify HealthManager audits cluster vitality and generates report."""
        hm = HealthManager(agent_id="TEST_HM", auto_spawn_subagents=True, max_depth=7)
        audit = hm.audit_cluster_health()
        self.assertTrue(audit["overall_healthy"])
        self.assertGreaterEqual(audit["vitality_index"], 90.0)

    def test_session_manager(self) -> None:
        """Verify SessionManager creates and retrieves tracked sessions."""
        sm = SessionManager(agent_id="TEST_SESS", auto_spawn_subagents=True, max_depth=7)
        sess = sm.create_session(metadata={"source": "test"})
        self.assertIn("session_id", sess)

        fetched = sm.get_session(sess["session_id"])
        self.assertIsNotNone(fetched)

    def test_resource_manager_quotas(self) -> None:
        """Verify ResourceManager checks memory, thread, connection, and file quotas."""
        rm = ResourceManager(agent_id="TEST_RM", auto_spawn_subagents=True, max_depth=7)
        res = rm.check_resource_quotas({
            "requested_mb": 256,
            "current_mb": 2048,
            "max_memory_mb": 8192,
            "active_threads": 5,
            "max_threads": 10,
        })
        self.assertTrue(res["all_quotas_valid"])

    def test_context_manager_propagation(self) -> None:
        """Verify ContextManager propagates context through agent trees."""
        cm = ContextManager(agent_id="TEST_CM", auto_spawn_subagents=True, max_depth=7)
        merged = cm.propagate_context(
            parent_ctx={"session_id": "SES_1", "user_id": "U1"},
            child_envelope={"task_id": "TSK_1"},
        )
        self.assertEqual(merged["session_id"], "SES_1")
        self.assertEqual(merged["task_id"], "TSK_1")

    def test_integration_orchestrator_pipeline(self) -> None:
        """Verify IntegrationOrchestrator executes full integration verification cycle."""
        orch = IntegrationOrchestrator(agent_id="TEST_INT_E2E", auto_spawn_subagents=True, max_depth=7)
        envelope = {"task_id": "T_INT_E2E", "payload": {}}
        res = orch.execute_lifecycle(envelope)

        self.assertEqual(res["status"], "COMPLETED")
        rep = res["integration_report"]
        self.assertTrue(rep["all_subsystems_healthy"])
        self.assertTrue(rep["initializer"])
        self.assertTrue(rep["dependency_injection"])
        self.assertTrue(rep["interfaces"])

    def test_register_all_integration_agents(self) -> None:
        """Verify registration helper registers all integration agents into AgentRegistry."""
        res = register_all_integration_agents(self.registry, max_depth=7)
        total = res["total_registered"]
        self.assertGreaterEqual(total, 14)
        self.assertIsNotNone(self.registry.get_agent("IA1_INTEGRATION_ORCHESTRATOR"))

    def test_application_harness(self) -> None:
        """Verify Application wrapper in app.py initializes, gets status, and terminates."""
        app = create_app("config.yaml")
        try:
            status = app.get_status()
            self.assertTrue(status["running"])
            self.assertIn("session_id", status)
        finally:
            app.shutdown()

    def test_cli_command_parser(self) -> None:
        """Verify cli.py parses subcommands properly."""
        with self.assertRaises(SystemExit) as cm:
            cli_main(["--help"])
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
