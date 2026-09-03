"""Comprehensive Unit Test Suite for Quality Layer Agents (Session 7)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.quality import (
    BestPracticesChecker,
    BugFinder,
    CodeFormatter,
    CodeReviewer,
    ComplexityAnalyzer,
    CyclomaticChecker,
    DependencyChecker,
    DocumentationWriter,
    FinalReviewer,
    ImprovementPlanner,
    IndentationChecker,
    JsdocGenerator,
    NamingChecker,
    PerformanceOptimizer,
    QualityOrchestrator,
    QualityScorer,
    RefactoringSuggester,
    SplitSuggester,
    StyleChecker,
    SwaggerGenerator,
    register_all_quality_agents,
)
from core.registry import AgentRegistry


class TestQualityAgents(unittest.TestCase):
    """Test suite covering all 14 Quality domain agents and fractal subagent structures."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_quality_orchestrator_spawns_subsystems(self) -> None:
        """Verify QualityOrchestrator spawns all 12 L4 quality coordinators."""
        orch = QualityOrchestrator(agent_id="TEST_Q_ORCH", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(orch.code_formatter)
        self.assertIsNotNone(orch.style_checker)
        self.assertIsNotNone(orch.complexity_analyzer)
        self.assertIsNotNone(orch.best_practices_checker)
        self.assertIsNotNone(orch.doc_writer)
        self.assertIsNotNone(orch.code_reviewer)
        self.assertIsNotNone(orch.perf_optimizer)
        self.assertIsNotNone(orch.refactor_suggester)
        self.assertIsNotNone(orch.dependency_checker)
        self.assertIsNotNone(orch.quality_scorer)
        self.assertIsNotNone(orch.improvement_planner)
        self.assertIsNotNone(orch.final_reviewer)

        child_names = [c.name for c in orch.children.values()]
        self.assertIn("CodeFormatter", child_names)
        self.assertIn("StyleChecker", child_names)
        self.assertIn("ComplexityAnalyzer", child_names)
        self.assertIn("BestPracticesChecker", child_names)
        self.assertIn("DocumentationWriter", child_names)
        self.assertIn("CodeReviewer", child_names)
        self.assertIn("PerformanceOptimizer", child_names)
        self.assertIn("RefactoringSuggester", child_names)
        self.assertIn("DependencyChecker", child_names)
        self.assertIn("QualityScorer", child_names)
        self.assertIn("ImprovementPlanner", child_names)
        self.assertIn("FinalReviewer", child_names)

    def test_code_formatter_spawns_checkers(self) -> None:
        """Verify CodeFormatter spawns IndentationChecker, SpacingChecker, LineLengthChecker."""
        cf = CodeFormatter(agent_id="TEST_CF", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(cf.indent_checker)
        self.assertIsNotNone(cf.spacing_checker)
        self.assertIsNotNone(cf.length_checker)
        self.assertIsInstance(cf.indent_checker, IndentationChecker)

    def test_style_checker_spawns_checkers(self) -> None:
        """Verify StyleChecker spawns NamingChecker, CommentChecker, ImportChecker."""
        sc = StyleChecker(agent_id="TEST_SC", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(sc.naming_checker)
        self.assertIsNotNone(sc.comment_checker)
        self.assertIsNotNone(sc.import_checker)
        self.assertIsInstance(sc.naming_checker, NamingChecker)

    def test_complexity_analyzer_spawns_checkers(self) -> None:
        """Verify ComplexityAnalyzer spawns CyclomaticChecker, CognitiveChecker, NestingChecker."""
        ca = ComplexityAnalyzer(agent_id="TEST_CA", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(ca.cyclo_checker)
        self.assertIsNotNone(ca.cogni_checker)
        self.assertIsNotNone(ca.nest_checker)
        self.assertIsInstance(ca.cyclo_checker, CyclomaticChecker)

    def test_best_practices_checker_spawns_checkers(self) -> None:
        """Verify BestPracticesChecker spawns PatternValidator, SolidChecker, DryChecker."""
        bp = BestPracticesChecker(agent_id="TEST_BP", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(bp.pattern_validator)
        self.assertIsNotNone(bp.solid_checker)
        self.assertIsNotNone(bp.dry_checker)

    def test_documentation_writer_spawns_generators(self) -> None:
        """Verify DocumentationWriter spawns JsdocGenerator, SwaggerGenerator, ReadmeGenerator."""
        dw = DocumentationWriter(agent_id="TEST_DW", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(dw.jsdoc_gen)
        self.assertIsNotNone(dw.swagger_gen)
        self.assertIsNotNone(dw.readme_gen)
        self.assertIsInstance(dw.jsdoc_gen, JsdocGenerator)
        self.assertIsInstance(dw.swagger_gen, SwaggerGenerator)

    def test_code_reviewer_spawns_checkers(self) -> None:
        """Verify CodeReviewer spawns LogicChecker, BugFinder, EdgeCaseReviewer."""
        cr = CodeReviewer(agent_id="TEST_CR", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(cr.logic_checker)
        self.assertIsNotNone(cr.bug_finder)
        self.assertIsNotNone(cr.edge_reviewer)
        self.assertIsInstance(cr.bug_finder, BugFinder)

    def test_performance_optimizer_spawns_analyzers(self) -> None:
        """Verify PerformanceOptimizer spawns AlgorithmAnalyzer, CacheSuggester, QueryOptimizer."""
        po = PerformanceOptimizer(agent_id="TEST_PO", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(po.algo_analyzer)
        self.assertIsNotNone(po.cache_suggester)
        self.assertIsNotNone(po.query_optimizer)

    def test_refactoring_suggester_spawns_subagents(self) -> None:
        """Verify RefactoringSuggester spawns DuplicationFinder, SplitSuggester, MergeSuggester."""
        rs = RefactoringSuggester(agent_id="TEST_RS", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(rs.dup_finder)
        self.assertIsNotNone(rs.split_suggester)
        self.assertIsNotNone(rs.merge_suggester)
        self.assertIsInstance(rs.split_suggester, SplitSuggester)

    def test_dependency_checker_spawns_subagents(self) -> None:
        """Verify DependencyChecker spawns VersionChecker, SecurityChecker, CompatibilityChecker."""
        dc = DependencyChecker(agent_id="TEST_DC", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(dc.version_checker)
        self.assertIsNotNone(dc.security_checker)
        self.assertIsNotNone(dc.compatibility_checker)

    def test_quality_scorer_weighted_calculation(self) -> None:
        """Verify QualityScorer computes weighted composite score and assigns benchmark grade."""
        qs = QualityScorer(agent_id="TEST_QS", auto_spawn_subagents=True, max_depth=7)
        res = qs.calculate_quality_score({
            "readability": 95.0,
            "maintainability": 90.0,
            "performance": 92.0,
            "security": 96.0,
            "documentation": 90.0,
        })
        self.assertIn("overall_quality_score", res)
        self.assertIn("grade", res)
        self.assertGreaterEqual(res["overall_quality_score"], 90.0)
        self.assertTrue(res["passed"])

    def test_quality_orchestrator_end_to_end_audit(self) -> None:
        """Verify QualityOrchestrator executes full audit, passes quality gate, and compiles signoff."""
        orch = QualityOrchestrator(agent_id="TEST_Q_E2E", auto_spawn_subagents=True, max_depth=7)
        code = "def add(a: int, b: int) -> int:\n    \"\"\"Sum numbers.\"\"\"\n    return a + b\n"
        envelope = {
            "task_id": "T_QUALITY_E2E",
            "payload": {"code": code, "project_title": "Calculator Service"},
        }
        result = orch.execute_lifecycle(envelope)

        self.assertEqual(result["status"], "COMPLETED")
        report = result["quality_audit_report"]
        self.assertIn("overall_quality_score", report)
        self.assertIn("gate_approved", report)
        self.assertTrue(report["gate_approved"])
        self.assertIn("final_review", report)
        self.assertEqual(report["final_review"]["final_verdict"], "APPROVED FOR PRODUCTION")

    def test_register_all_quality_agents(self) -> None:
        """Verify registration helper registers all quality agents into AgentRegistry."""
        res = register_all_quality_agents(self.registry, max_depth=7)
        total = res["total_registered"]
        self.assertGreaterEqual(total, 13)
        self.assertIsNotNone(self.registry.get_agent("Q1_QUALITY_ORCHESTRATOR"))


if __name__ == "__main__":
    unittest.main()
