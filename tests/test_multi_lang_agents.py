"""Comprehensive Test Suite for Multi-Language Support Layer Agents (Session 23)."""

import os
import sys
import unittest

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT_DIR in sys.path:
    sys.path.remove(_ROOT_DIR)
sys.path.insert(0, _ROOT_DIR)

from core.registry import AgentRegistry
from multi_lang import (
    CodeFormatter,
    CrossLanguageValidator,
    LanguageDetector,
    LanguageTranslator,
    GoGenerator,
    JavaGenerator,
    MultiLanguageOrchestrator,
    NodeGenerator,
    PythonGenerator,
    RustGenerator,
    register_all_multi_lang_agents,
)


class TestMultiLangLayer(unittest.TestCase):
    """Covers all 14 multi-language agents, subagents, and generation flows."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_orchestrator_spawns_13_subsystems(self) -> None:
        orch = MultiLanguageOrchestrator(agent_id="TEST_ML_ORCH", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(orch.python_gen)
        self.assertIsNotNone(orch.node_gen)
        self.assertIsNotNone(orch.go_gen)
        self.assertIsNotNone(orch.rust_gen)
        self.assertIsNotNone(orch.java_gen)
        self.assertIsNotNone(orch.detector)
        self.assertIsNotNone(orch.translator)
        self.assertIsNotNone(orch.validator)
        self.assertIsNotNone(orch.package_mgr)
        self.assertIsNotNone(orch.framework_sel)
        self.assertIsNotNone(orch.dependency_res)
        self.assertIsNotNone(orch.formatter)
        self.assertIsNotNone(orch.doc_gen)
        self.assertEqual(len(orch.children), 13)

    def test_python_generator(self) -> None:
        gen = PythonGenerator(agent_id="TEST_PY_GEN", auto_spawn_subagents=True, max_depth=7)
        res = gen.generate_python_project({"module_name": "billing", "model_name": "Invoice"})
        self.assertTrue(res["all_generated"])
        self.assertEqual(res["framework"], "fastapi")
        self.assertTrue(res["api"]["syntax_valid"])
        self.assertTrue(res["model"]["syntax_valid"])

    def test_node_generator(self) -> None:
        gen = NodeGenerator(agent_id="TEST_NODE_GEN", auto_spawn_subagents=True, max_depth=7)
        res = gen.generate_node_project({"module_name": "billing", "model_name": "Invoice"})
        self.assertTrue(res["all_generated"])
        self.assertTrue(res["package_json"]["json_valid"])

    def test_go_generator(self) -> None:
        gen = GoGenerator(agent_id="TEST_GO_GEN", auto_spawn_subagents=True, max_depth=7)
        res = gen.generate_go_project({"module_name": "billing", "model_name": "Invoice"})
        self.assertTrue(res["all_generated"])
        self.assertIn("package main", res["api"]["generated_code"])
        self.assertIn("go 1.21", res["go_mod"]["generated_content"])

    def test_rust_generator(self) -> None:
        gen = RustGenerator(agent_id="TEST_RUST_GEN", auto_spawn_subagents=True, max_depth=7)
        res = gen.generate_rust_project({"module_name": "billing", "model_name": "Invoice"})
        self.assertTrue(res["all_generated"])
        self.assertIn("actix_web", res["api"]["generated_code"])

    def test_java_generator(self) -> None:
        gen = JavaGenerator(agent_id="TEST_JAVA_GEN", auto_spawn_subagents=True, max_depth=7)
        res = gen.generate_java_project({"package_name": "com.billing", "model_name": "Invoice"})
        self.assertTrue(res["all_generated"])
        self.assertIn("RestController", res["api"]["generated_code"])
        self.assertIn("spring-boot", res["pom_xml"]["generated_content"])

    def test_language_detector(self) -> None:
        det = LanguageDetector(agent_id="TEST_DETECTOR", auto_spawn_subagents=True, max_depth=7)
        res = det.detect_language("def handler(): return 1", "handler.py")
        self.assertTrue(res["accepted"])
        self.assertEqual(res["detected_language"], "python")

    def test_language_translator(self) -> None:
        trans = LanguageTranslator(agent_id="TEST_TRANSLATOR", auto_spawn_subagents=True, max_depth=7)
        res = trans.translate_language("python", "node", "def add(a, b):\n    return a + b")
        self.assertTrue(res["success"])
        self.assertIn("function", res["translated_code"])

    def test_formatter_and_validator(self) -> None:
        fmt = CodeFormatter(agent_id="TEST_FORMATTER", auto_spawn_subagents=True, max_depth=7)
        formatted = fmt.format_code("python", "def foo():\n    pass\n")
        self.assertEqual(formatted["formatter"], "black")
        val = CrossLanguageValidator(agent_id="TEST_VALIDATOR", auto_spawn_subagents=True, max_depth=7)
        res = val.validate_code("def foo():\n    return 1\n", "python")
        self.assertTrue(res["all_passed"])

    def test_register_all(self) -> None:
        result = register_all_multi_lang_agents(self.registry)
        self.assertEqual(result["total_registered"], 71)


if __name__ == "__main__":
    unittest.main()