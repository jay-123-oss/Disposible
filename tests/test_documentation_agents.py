"""Comprehensive Test Suite for Documentation Layer Agents (Session 13)."""

import os
import sys
import unittest

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT_DIR in sys.path:
    sys.path.remove(_ROOT_DIR)
sys.path.insert(0, _ROOT_DIR)

from agents.documentation import (
    AgentReference,
    ApiDocumentation,
    ConfigurationGuide,
    DeploymentGuide,
    DeveloperGuide,
    DocumentationOrchestrator,
    ExampleRepository,
    FaqGenerator,
    InstallationGuide,
    SystemDocumentation,
    TroubleshootingGuide,
    UserGuide,
    register_all_documentation_agents,
)
from core.registry import AgentRegistry


class TestDocumentationLayer(unittest.TestCase):
    """Test suite covering all 12 documentation agents, subagents, and generated files."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_doc_orchestrator_spawns_subsystems(self) -> None:
        """Verify DocumentationOrchestrator spawns all 11 L4 documentation coordinators."""
        orch = DocumentationOrchestrator(agent_id="TEST_DOC_ORCH", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(orch.sys_doc)
        self.assertIsNotNone(orch.api_doc)
        self.assertIsNotNone(orch.user_gd)
        self.assertIsNotNone(orch.dev_gd)
        self.assertIsNotNone(orch.install_gd)
        self.assertIsNotNone(orch.config_gd)
        self.assertIsNotNone(orch.deploy_gd)
        self.assertIsNotNone(orch.agent_ref)
        self.assertIsNotNone(orch.example_repo)
        self.assertIsNotNone(orch.trouble_gd)
        self.assertIsNotNone(orch.faq_gen)

        child_names = [c.name for c in orch.children.values()]
        self.assertEqual(len(child_names), 11)
        self.assertIn("SystemDocumentation", child_names)
        self.assertIn("ApiDocumentation", child_names)
        self.assertIn("UserGuide", child_names)
        self.assertIn("DeveloperGuide", child_names)
        self.assertIn("InstallationGuide", child_names)
        self.assertIn("ConfigurationGuide", child_names)
        self.assertIn("DeploymentGuide", child_names)
        self.assertIn("AgentReference", child_names)
        self.assertIn("ExampleRepository", child_names)
        self.assertIn("TroubleshootingGuide", child_names)
        self.assertIn("FaqGenerator", child_names)

    def test_system_documentation_coordinator(self) -> None:
        """Verify SystemDocumentation coordinates architecture, component, data flow, and diagrams."""
        doc = SystemDocumentation(agent_id="TEST_SYS_DOC", auto_spawn_subagents=True, max_depth=7)
        res = doc.generate_system_docs()
        self.assertTrue(res["all_generated"])
        self.assertTrue(res["architecture"]["generated"])
        self.assertTrue(res["components"]["generated"])
        self.assertTrue(res["data_flow"]["generated"])
        self.assertTrue(res["diagrams"]["generated"])

    def test_api_documentation_coordinator(self) -> None:
        """Verify ApiDocumentation coordinates OpenAPI, Swagger, endpoints, and schemas."""
        doc = ApiDocumentation(agent_id="TEST_API_DOC", auto_spawn_subagents=True, max_depth=7)
        res = doc.generate_api_docs()
        self.assertTrue(res["all_generated"])
        self.assertTrue(res["openapi"]["generated"])
        self.assertTrue(res["swagger"]["generated"])
        self.assertTrue(res["endpoints"]["generated"])
        self.assertTrue(res["schemas"]["generated"])

    def test_user_guide_coordinator(self) -> None:
        """Verify UserGuide coordinates getting started, features, use cases, and best practices."""
        doc = UserGuide(agent_id="TEST_USER_GD", auto_spawn_subagents=True, max_depth=7)
        res = doc.generate_user_guide()
        self.assertTrue(res["all_generated"])
        self.assertTrue(res["getting_started"]["generated"])
        self.assertTrue(res["features"]["generated"])
        self.assertTrue(res["use_cases"]["generated"])
        self.assertTrue(res["best_practices"]["generated"])

    def test_developer_guide_coordinator(self) -> None:
        """Verify DeveloperGuide coordinates code structure, extension, contributing, and debugging."""
        doc = DeveloperGuide(agent_id="TEST_DEV_GD", auto_spawn_subagents=True, max_depth=7)
        res = doc.generate_developer_guide()
        self.assertTrue(res["all_generated"])
        self.assertTrue(res["code_structure"]["generated"])
        self.assertTrue(res["extension"]["generated"])
        self.assertTrue(res["contributing"]["generated"])
        self.assertTrue(res["debugging"]["generated"])

    def test_installation_guide_coordinator(self) -> None:
        """Verify InstallationGuide coordinates prerequisites, steps, troubleshooting, and verification."""
        doc = InstallationGuide(agent_id="TEST_INST_GD", auto_spawn_subagents=True, max_depth=7)
        res = doc.generate_installation_guide()
        self.assertTrue(res["all_generated"])
        self.assertTrue(res["prerequisites"]["generated"])
        self.assertTrue(res["steps"]["generated"])
        self.assertTrue(res["troubleshooting"]["generated"])
        self.assertTrue(res["verification"]["generated"])

    def test_configuration_guide_coordinator(self) -> None:
        """Verify ConfigurationGuide coordinates config reference, env vars, custom config, and validation."""
        doc = ConfigurationGuide(agent_id="TEST_CFG_GD", auto_spawn_subagents=True, max_depth=7)
        res = doc.generate_configuration_guide()
        self.assertTrue(res["all_generated"])
        self.assertTrue(res["reference"]["generated"])
        self.assertTrue(res["environment_variables"]["generated"])
        self.assertTrue(res["custom_config"]["generated"])
        self.assertTrue(res["validation"]["generated"])

    def test_deployment_guide_coordinator(self) -> None:
        """Verify DeploymentGuide coordinates Docker, K8s, Cloud, and CI/CD guides."""
        doc = DeploymentGuide(agent_id="TEST_DEP_GD", auto_spawn_subagents=True, max_depth=7)
        res = doc.generate_deployment_guide()
        self.assertTrue(res["all_generated"])
        self.assertTrue(res["docker"]["generated"])
        self.assertTrue(res["kubernetes"]["generated"])
        self.assertTrue(res["cloud"]["generated"])
        self.assertTrue(res["cicd"]["generated"])

    def test_agent_reference_coordinator(self) -> None:
        """Verify AgentReference coordinates API reference, capabilities, lifecycle, and custom agents."""
        doc = AgentReference(agent_id="TEST_AGENT_REF", auto_spawn_subagents=True, max_depth=7)
        res = doc.generate_agent_reference()
        self.assertTrue(res["all_generated"])
        self.assertTrue(res["api_reference"]["generated"])
        self.assertTrue(res["capabilities"]["generated"])
        self.assertTrue(res["lifecycle"]["generated"])
        self.assertTrue(res["custom_guide"]["generated"])

    def test_example_repository_coordinator(self) -> None:
        """Verify ExampleRepository coordinates basic, advanced, use cases, and integrations."""
        doc = ExampleRepository(agent_id="TEST_EX_REPO", auto_spawn_subagents=True, max_depth=7)
        res = doc.generate_examples()
        self.assertTrue(res["all_generated"])
        self.assertTrue(res["basic"]["generated"])
        self.assertTrue(res["advanced"]["generated"])
        self.assertTrue(res["use_cases"]["generated"])
        self.assertTrue(res["integrations"]["generated"])

    def test_troubleshooting_guide_coordinator(self) -> None:
        """Verify TroubleshootingGuide coordinates common issues, error codes, solution steps, and escalation."""
        doc = TroubleshootingGuide(agent_id="TEST_TRB_GD", auto_spawn_subagents=True, max_depth=7)
        res = doc.generate_troubleshooting_guide()
        self.assertTrue(res["all_generated"])
        self.assertTrue(res["common_issues"]["generated"])
        self.assertTrue(res["error_codes"]["generated"])
        self.assertTrue(res["solution_steps"]["generated"])
        self.assertTrue(res["escalation"]["generated"])

    def test_faq_generator_coordinator(self) -> None:
        """Verify FaqGenerator coordinates general, technical, configuration, and troubleshooting FAQs."""
        doc = FaqGenerator(agent_id="TEST_FAQ_GEN", auto_spawn_subagents=True, max_depth=7)
        res = doc.generate_faqs()
        self.assertTrue(res["all_generated"])
        self.assertTrue(res["general"]["generated"])
        self.assertTrue(res["technical"]["generated"])
        self.assertTrue(res["configuration"]["generated"])
        self.assertTrue(res["troubleshooting"]["generated"])

    def test_doc_orchestrator_lifecycle(self) -> None:
        """Verify DocumentationOrchestrator runs full lifecycle across all 11 coordinators."""
        orch = DocumentationOrchestrator(agent_id="TEST_LIFECYCLE", auto_spawn_subagents=True, max_depth=7)
        envelope = {"task_id": "T_DOC_FULL", "payload": {}}
        res = orch.execute_lifecycle(envelope)

        self.assertEqual(res["status"], "COMPLETED")
        manifest = res["documentation_manifest"]
        self.assertTrue(manifest["all_docs_generated"])
        self.assertEqual(manifest["total_subsystems"], 11)

    def test_register_all_documentation_agents(self) -> None:
        """Verify register_all_documentation_agents registers root, coordinators, and subagents."""
        res = register_all_documentation_agents(self.registry, max_depth=7)
        total = res["total_registered"]
        self.assertGreaterEqual(total, 56)  # 1 + 11 + 44 = 56
        self.assertIsNotNone(self.registry.get_agent("D1_DOCUMENTATION_ORCHESTRATOR"))

    def test_all_50_documentation_files_exist(self) -> None:
        """Verify that all 50 required documentation files exist and are populated."""
        docs_dir = os.path.join(_ROOT_DIR, "docs")
        self.assertTrue(os.path.isdir(docs_dir))

        expected_files = [
            "README.md", "ARCHITECTURE.md", "COMPONENTS.md", "DATA_FLOW.md", "SYSTEM_DIAGRAM.md",
            "API_REFERENCE.md", "OPENAPI.yaml", "SWAGGER.md", "ENDPOINTS.md", "SCHEMAS.md",
            "USER_GUIDE.md", "GETTING_STARTED.md", "FEATURES.md", "USE_CASES.md", "BEST_PRACTICES.md",
            "DEVELOPER_GUIDE.md", "CODE_STRUCTURE.md", "EXTENSION_GUIDE.md", "CONTRIBUTING.md", "DEBUGGING_GUIDE.md",
            "INSTALLATION.md", "PREREQUISITES.md", "VERIFICATION.md", "DEPLOYMENT.md", "DOCKER_DEPLOYMENT.md", "K8S_DEPLOYMENT.md", "CLOUD_DEPLOYMENT.md",
            "CONFIGURATION.md", "ENVIRONMENT_VARIABLES.md", "CUSTOM_CONFIG.md", "VALIDATION.md",
            "AGENT_REFERENCE.md", "AGENT_CAPABILITIES.md", "AGENT_LIFECYCLE.md", "CUSTOM_AGENT_GUIDE.md",
            "EXAMPLES.md", "BASIC_EXAMPLES.md", "ADVANCED_EXAMPLES.md", "USE_CASE_EXAMPLES.md", "INTEGRATION_EXAMPLES.md",
            "TROUBLESHOOTING.md", "COMMON_ISSUES.md", "ERROR_CODES.md", "SOLUTION_STEPS.md", "ESCALATION_GUIDE.md",
            "FAQ.md", "GENERAL_FAQ.md", "TECHNICAL_FAQ.md", "CONFIGURATION_FAQ.md", "TROUBLESHOOTING_FAQ.md"
        ]

        self.assertEqual(len(expected_files), 50)
        for fname in expected_files:
            fpath = os.path.join(docs_dir, fname)
            self.assertTrue(os.path.isfile(fpath), f"Missing file: {fname}")
            self.assertGreater(os.path.getsize(fpath), 20, f"File too small: {fname}")


if __name__ == "__main__":
    unittest.main()
