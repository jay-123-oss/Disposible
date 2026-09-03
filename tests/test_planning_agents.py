"""Automated test suite verifying all 10 Planning Layer agents and KnowledgeBase."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.planning import (
    AnswerValidator,
    ArchitectureDesigner,
    IntentClarifier,
    KnowledgeBase,
    OptionParser,
    PlanGenerator,
    QuestionGenerator,
    RequirementsDocumenter,
    RiskAssessor,
    TaskDecomposer,
    TechStackSelector,
    register_all_planning_agents,
)
from core.registry import AgentRegistry


class TestPlanningAgents(unittest.TestCase):
    """Test suite covering all 10 Planning Layer agents."""

    def setUp(self):
        self.kb = KnowledgeBase()
        self.registry = AgentRegistry()
        self.registry.clear()

    # 1. KnowledgeBase
    def test_knowledge_base(self):
        templates = self.kb.get_templates_for_category("project_type")
        self.assertTrue(len(templates) > 0)

        py_info = self.kb.get_tech_stack_info("python")
        self.assertIsNotNone(py_info)
        self.assertIn("FastAPI", py_info["frameworks"])

        arch_pat = self.kb.get_architecture_pattern("monolithic")
        self.assertIsNotNone(arch_pat)
        self.assertEqual(arch_pat["complexity"], "LOW")

        risk_pat = self.kb.get_risk_pattern("security")
        self.assertIsNotNone(risk_pat)
        self.assertIn("mitigation", risk_pat)

    # 2. IntentClarifier & Subagent Spawning
    def test_intent_clarifier(self):
        ic = IntentClarifier(name="IntentClarifier", max_depth=2)
        self.assertEqual(ic.depth, 0)
        self.assertIsNotNone(ic.question_generator)
        self.assertIsNotNone(ic.option_parser)
        self.assertIsNotNone(ic.answer_validator)
        self.assertEqual(ic.question_generator.depth, 1)

        # Clarify user intent
        res = ic.clarify_intent("Build a secure REST API in Python with JWT auth and SQLite database")
        self.assertIn("build_api", res["detected_intents"])
        self.assertIn("authentication", res["detected_intents"])
        self.assertEqual(res["entities"]["project_type"], "API")
        self.assertEqual(res["entities"]["language"], "python")
        self.assertGreaterEqual(res["confidence_score"], 70.0)

        # Test BaseAgent lifecycle
        lifecycle_res = ic.execute_lifecycle({"task_id": "T_IC_01", "intent": "Build a REST API in Python"})
        self.assertEqual(lifecycle_res["status"], "COMPLETED")

    # 3. QuestionGenerator
    def test_question_generator(self):
        qg = QuestionGenerator()
        context = {"project_type": "API"}
        questions = qg.generate_questions(context)
        self.assertTrue(len(questions) > 0)
        # Should ask for missing language
        self.assertTrue(any(q["id"] == "Q_TECH_STACK" for q in questions))

        followups = qg.generate_followup("I need auth and database", {})
        self.assertTrue(len(followups) >= 2)

    # 4. OptionParser
    def test_option_parser(self):
        op = OptionParser()

        # Parse boolean
        p_bool = op.parse_response("yes, definitely", expected_type="bool")
        self.assertTrue(p_bool["parsed_value"])

        # Parse choices
        p_choices = op.parse_response("auth, crud, file upload", expected_type="list")
        self.assertEqual(len(p_choices["parsed_value"]), 3)

        # Map to options
        matched = op.map_to_options("fastapi", ["Flask", "FastAPI", "Django"])
        self.assertEqual(matched, "FastAPI")

    # 5. AnswerValidator
    def test_answer_validator(self):
        av = AnswerValidator()
        self.assertTrue(av.validate_response("API", "project_type"))
        self.assertFalse(av.validate_response("QuantumComputer", "project_type"))

        self.assertTrue(av.validate_response("Python with FastAPI", "tech_stack"))
        self.assertTrue(av.validate_response("auth, payments", "features"))

        responses = [
            {"category": "project type", "answer": "API"},
            {"category": "tech stack", "answer": "Python"},
        ]
        self.assertFalse(av.check_completeness(responses))
        missing = av.get_missing_fields(responses)
        self.assertIn("features", missing)

    # 6. RequirementsDocumenter
    def test_requirements_documenter(self):
        rd = RequirementsDocumenter()
        reqs_input = {
            "project_type": "API",
            "language": "python",
            "framework": "FastAPI",
            "features": ["User Registration", "JWT Login"],
        }
        md_doc = rd.document_requirements(reqs_input, output_format="markdown")
        self.assertIn("Requirements Specification", md_doc)
        self.assertIn("Functional Requirements", md_doc)
        self.assertIn("FastAPI", md_doc)

        json_doc = rd.document_requirements(reqs_input, output_format="json")
        self.assertIn('"project_type": "API"', json_doc)

    # 7. TechStackSelector
    def test_tech_stack_selector(self):
        tss = TechStackSelector()
        lang_res = tss.select_language({"project_type": "API"})
        self.assertIn("language", lang_res)
        self.assertEqual(lang_res["language"], "python")

        fw_res = tss.select_framework("python", {})
        self.assertEqual(fw_res["framework"], "FastAPI")

        libs = tss.suggest_libraries(["auth", "validation"], "python")
        self.assertTrue(len(libs) > 0)
        lib_names = [l["library"] for l in libs]
        self.assertTrue(any(lib in ["pyjwt", "pydantic", "passlib", "bcrypt"] for lib in lib_names))

    # 8. ArchitectureDesigner
    def test_architecture_designer(self):
        ad = ArchitectureDesigner()
        arch = ad.design_architecture({"project_type": "API", "language": "python"})
        self.assertIn("layers", arch)
        self.assertIn("components", arch)
        self.assertIn("interfaces", arch)
        self.assertIn("data_flow", arch)
        self.assertTrue(len(arch["layers"]) >= 3)

    # 9. TaskDecomposer
    def test_task_decomposer(self):
        td = TaskDecomposer()
        tasks = td.decompose_tasks({"name": "UserAPI"})
        self.assertTrue(len(tasks) >= 5)
        # Check task structure
        first_task = tasks[0]
        self.assertIn("id", first_task)
        self.assertIn("phase", first_task)
        self.assertIn("priority", first_task)
        self.assertIn("dependencies", first_task)
        self.assertIn("estimated_tokens", first_task)

    # 10. RiskAssessor
    def test_risk_assessor(self):
        ra = RiskAssessor()
        risks = ra.assess_risks({"name": "UserAPI"})
        self.assertTrue(len(risks) >= 3)
        for r in risks:
            self.assertIn("score", r)
            self.assertIn("mitigation", r)
            self.assertGreaterEqual(r["score"], 0.0)

    # 11. PlanGenerator
    def test_plan_generator(self):
        pg = PlanGenerator()
        td = TaskDecomposer()
        ra = RiskAssessor()

        tasks = td.decompose_tasks({})
        risks = ra.assess_risks({})

        plan = pg.generate_plan({
            "project_name": "AuthService",
            "tasks": tasks,
            "risks": risks,
        })
        self.assertEqual(plan["project_name"], "AuthService")
        self.assertIn("phases", plan)
        self.assertEqual(plan["total_tasks"], len(tasks))
        self.assertIn("resource_requirements", plan)
        self.assertIn("success_criteria", plan)

    # 12. Complete Registration of all 10 Planning Agents
    def test_register_all_planning_agents(self):
        reg_dict = register_all_planning_agents(self.registry)
        self.assertEqual(len(reg_dict), 10)
        self.assertEqual(len(self.registry.get_all_agents()), 10)

        # Verify all agents respect depth bounds
        for agent in self.registry.get_all_agents():
            self.assertLessEqual(agent.depth, 2)


if __name__ == "__main__":
    unittest.main()
