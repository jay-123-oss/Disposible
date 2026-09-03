"""Comprehensive Test Suite for Plugin System Layer Agents (Session 24)."""

import os
import sys
import unittest

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT_DIR in sys.path:
    sys.path.remove(_ROOT_DIR)
sys.path.insert(0, _ROOT_DIR)

from core.registry import AgentRegistry
from plugins import (
    PluginApiProvider,
    PluginDependencies,
    PluginDocumentation,
    PluginEventListener,
    PluginInstaller,
    PluginInterface,
    PluginLoader,
    PluginManager,
    PluginMarketplace,
    PluginOrchestrator,
    PluginSecurityScanner,
    PluginStore,
    PluginUninstaller,
    PluginValidator,
    PluginVersionManager,
    register_all_plugin_agents,
)
from plugins.builtin.code_formatter_plugin import CodeFormatterPlugin
from plugins.builtin.documentation_generator_plugin import DocumentationGeneratorPlugin
from plugins.builtin.performance_optimizer_plugin import PerformanceOptimizerPlugin
from plugins.builtin.security_scanner_plugin import SecurityScannerPlugin
from plugins.builtin.test_generator_plugin import TestGeneratorPlugin


class TestPluginSystemLayer(unittest.TestCase):
    """Covers all 14 plugin system agents, subagents, and built-in plugins."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_orchestrator_spawns_subsystems(self) -> None:
        orch = PluginOrchestrator(agent_id="TEST_PLUG_ORCH", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(orch.manager)
        self.assertIsNotNone(orch.loader)
        self.assertIsNotNone(orch.store)
        self.assertIsNotNone(orch.installer)
        self.assertIsNotNone(orch.uninstaller)
        self.assertIsNotNone(orch.validator)
        self.assertIsNotNone(orch.security_scanner)
        self.assertIsNotNone(orch.api_provider)
        self.assertIsNotNone(orch.event_listener)
        self.assertIsNotNone(orch.marketplace)
        self.assertIsNotNone(orch.version_manager)
        self.assertIsNotNone(orch.dependencies)
        self.assertIsNotNone(orch.documentation)
        self.assertEqual(len(orch.children), 13)

    def test_builtin_plugins_interface(self) -> None:
        plugins = [
            CodeFormatterPlugin(),
            TestGeneratorPlugin(),
            SecurityScannerPlugin(),
            PerformanceOptimizerPlugin(),
            DocumentationGeneratorPlugin(),
        ]
        for p in plugins:
            self.assertTrue(isinstance(p, PluginInterface))
            p.initialize(None)
            p.activate()
            self.assertTrue(p.active)
            self.assertIsInstance(p.get_hooks(), dict)
            self.assertIsInstance(p.get_events(), dict)
            self.assertIsInstance(p.get_filters(), dict)
            self.assertIsInstance(p.get_actions(), dict)
            p.deactivate()
            self.assertFalse(p.active)

    def test_plugin_validator_and_security(self) -> None:
        val = PluginValidator(agent_id="TEST_P_VAL", auto_spawn_subagents=True, max_depth=7)
        manifest = {
            "name": "sample_plugin",
            "version": "1.0.0",
            "author": "Fractal Team",
            "description": "A test sample plugin",
            "entry_point": "sample_plugin:SamplePlugin",
        }
        res = val.validate_plugin("def sample(): pass", manifest)
        self.assertTrue(res["valid"])

        sec = PluginSecurityScanner(agent_id="TEST_P_SEC", auto_spawn_subagents=True, max_depth=7)
        sec_res = sec.scan_plugin_security("def run(): return 42")
        self.assertTrue(sec_res["safe"])

    def test_plugin_store_and_marketplace(self) -> None:
        store = PluginStore(agent_id="TEST_P_STORE", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(store)
        mkt = PluginMarketplace(agent_id="TEST_P_MKT", auto_spawn_subagents=True, max_depth=7)
        search_res = mkt.browse_marketplace("code")
        self.assertIn("search_results", search_res)

    def test_register_all_plugin_agents(self) -> None:
        result = register_all_plugin_agents(self.registry)
        self.assertEqual(result["total_registered"], 66)


if __name__ == "__main__":
    unittest.main()
