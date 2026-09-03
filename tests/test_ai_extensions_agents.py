"""Unit tests for the AI & ML Extensions Layer (A1-A16 + 61 subagents + prompts + configs)."""

from pathlib import Path
import unittest

from core.registry import AgentRegistry
from ai_extensions import (
    AIExtensionsOrchestrator,
    AutoCompletionEngine,
    BugPredictor,
    CodeEmbedder,
    CodeGenerator,
    CodeReviewerAI,
    CostOptimizer,
    DocumentationGeneratorAI,
    ModelFineTuner,
    ModelSelector,
    MultiModalProcessor,
    PerformancePredictor,
    QualityPredictor,
    RefactoringSuggesterAI,
    SemanticSearcher,
    TestGeneratorAI,
    register_all_ai_extensions_agents,
)
from ai_extensions.prompts import load_prompt


class TestAIExtensions(unittest.TestCase):
    """Test suite verifying all AI & ML extension coordinators, workers, prompts, and inference benchmarks."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()
        self.orchestrator = AIExtensionsOrchestrator(agent_id="A1_TEST_ORCHESTRATOR")

    def tearDown(self) -> None:
        self.registry.clear()

    def test_01_all_25_files_exist(self) -> None:
        """Verify all 25 AI & ML extension files exist and are non-empty."""
        expected_files = [
            "ai_extensions/__init__.py",
            "ai_extensions/ai_extensions_orchestrator.py",
            "ai_extensions/model_selector.py",
            "ai_extensions/cost_optimizer.py",
            "ai_extensions/code_embedder.py",
            "ai_extensions/semantic_searcher.py",
            "ai_extensions/auto_completion_engine.py",
            "ai_extensions/code_generator.py",
            "ai_extensions/quality_predictor.py",
            "ai_extensions/bug_predictor.py",
            "ai_extensions/performance_predictor.py",
            "ai_extensions/test_generator_ai.py",
            "ai_extensions/refactoring_suggester_ai.py",
            "ai_extensions/code_reviewer_ai.py",
            "ai_extensions/documentation_generator_ai.py",
            "ai_extensions/model_fine_tuner.py",
            "ai_extensions/multi_modal_processor.py",
            "ai_extensions/models_config.yaml",
            "ai_extensions/embeddings_config.yaml",
            "ai_extensions/prompts/__init__.py",
            "ai_extensions/prompts/code_generation.txt",
            "ai_extensions/prompts/test_generation.txt",
            "ai_extensions/prompts/code_review.txt",
            "ai_extensions/prompts/refactoring.txt",
            "ai_extensions/prompts/documentation.txt",
        ]
        base_dir = Path(__file__).parent.parent
        for rel_path in expected_files:
            p = base_dir / rel_path
            self.assertTrue(p.exists(), f"File does not exist: {rel_path}")
            self.assertGreater(p.stat().st_size, 0, f"File is empty: {rel_path}")

    def test_02_orchestrator_spawns_all_15_coordinators(self) -> None:
        """Verify AIExtensionsOrchestrator instantiates all 15 coordinators."""
        coordinators = [
            self.orchestrator.mod_sel,
            self.orchestrator.cst_opt,
            self.orchestrator.cde_emb,
            self.orchestrator.sem_src,
            self.orchestrator.aut_cmp,
            self.orchestrator.cde_gen,
            self.orchestrator.qlt_prd,
            self.orchestrator.bug_prd,
            self.orchestrator.prf_prd,
            self.orchestrator.tst_gen,
            self.orchestrator.ref_sug,
            self.orchestrator.cde_rev,
            self.orchestrator.doc_gen,
            self.orchestrator.mdl_ftn,
            self.orchestrator.mul_mod,
        ]
        for coord in coordinators:
            self.assertIsNotNone(coord)
            self.assertEqual(coord.depth, 1)

    def test_03_coordinators_spawn_appropriate_subagents(self) -> None:
        """Verify each coordinator instantiates its atomic grandchild workers (depth=2)."""
        coordinators = [
            (self.orchestrator.mod_sel, 4),
            (self.orchestrator.cst_opt, 4),
            (self.orchestrator.cde_emb, 4),
            (self.orchestrator.sem_src, 4),
            (self.orchestrator.aut_cmp, 4),
            (self.orchestrator.cde_gen, 5),  # 5 multi-language generators
            (self.orchestrator.qlt_prd, 4),
            (self.orchestrator.bug_prd, 4),
            (self.orchestrator.prf_prd, 4),
            (self.orchestrator.tst_gen, 4),
            (self.orchestrator.ref_sug, 4),
            (self.orchestrator.cde_rev, 4),
            (self.orchestrator.doc_gen, 4),
            (self.orchestrator.mdl_ftn, 4),
            (self.orchestrator.mul_mod, 4),
        ]
        for coord, expected_count in coordinators:
            self.assertEqual(len(coord.children), expected_count)
            for sub in coord.children.values():
                self.assertEqual(sub.depth, 2)

    def test_04_registry_registers_all_77_agents(self) -> None:
        """Verify registration helper registers exactly 77 agents (1 + 15 + 61) within memory limits."""
        res = register_all_ai_extensions_agents(self.registry, self.orchestrator)
        self.assertEqual(res["total_registered"], 77)
        all_agents = self.registry.get_all_agents()
        self.assertEqual(len(all_agents), 77)
        self.assertLessEqual(self.registry._allocated_ram_mb, 8192)

    def test_05_prompts_loader(self) -> None:
        """Verify all 5 prompt templates load and contain required instruction tokens."""
        prompt_names = ["code_generation", "test_generation", "code_review", "refactoring", "documentation"]
        for p in prompt_names:
            content = load_prompt(p)
            self.assertGreater(len(content), 50)
            self.assertIn("You are", content)

    def test_06_model_selector_execution(self) -> None:
        """Verify ModelSelector chooses optimal LLM in < 10ms."""
        res = self.orchestrator.mod_sel.select_optimal_model()
        self.assertTrue(res["model_selected"])
        self.assertTrue(res["latency_under_10ms"])
        self.assertIn(res["optimal_model"], ["qwen2.5-coder:3b", "llama3.2:3b", "mistral:7b"])

    def test_07_cost_optimizer_execution(self) -> None:
        """Verify CostOptimizer tracks tokens, caches, and exceeds 50% cost reduction."""
        res = self.orchestrator.cst_opt.optimize_inference_cost()
        self.assertTrue(res["cost_optimized"])
        self.assertTrue(res["target_50_percent_exceeded"])
        self.assertGreaterEqual(res["cost_reduction_percentage"], 50.0)

    def test_08_code_embedder_execution(self) -> None:
        """Verify CodeEmbedder produces 768-dim vectors in < 100ms."""
        res = self.orchestrator.cde_emb.generate_code_embeddings()
        self.assertTrue(res["embeddings_generated"])
        self.assertTrue(res["latency_under_100ms"])
        self.assertEqual(res["vectorizer"]["embedding_dimension"], 768)

    def test_09_semantic_searcher_execution(self) -> None:
        """Verify SemanticSearcher searches vector index in < 100ms with min similarity > 0.7."""
        res = self.orchestrator.sem_src.search_codebase_semantically()
        self.assertTrue(res["search_successful"])
        self.assertTrue(res["latency_under_100ms"])
        self.assertGreaterEqual(res["ranking"]["top_match_score"], 0.7)

    def test_10_auto_completion_engine_execution(self) -> None:
        """Verify AutoCompletionEngine generates suggestions in < 50ms."""
        res = self.orchestrator.aut_cmp.generate_completion()
        self.assertTrue(res["completion_generated"])
        self.assertTrue(res["latency_under_50ms"])
        self.assertGreater(len(res["top_suggestion"]), 0)

    def test_11_code_generator_execution(self) -> None:
        """Verify CodeGenerator generates Python, Node, Go, Rust, Java in < 5s."""
        res = self.orchestrator.cde_gen.generate_code_for_language()
        self.assertTrue(res["all_languages_supported"])
        self.assertTrue(res["latency_under_5s"])
        self.assertTrue(res["python"]["syntax_valid"])
        self.assertTrue(res["rust"]["syntax_valid"])

    def test_12_quality_predictor_execution(self) -> None:
        """Verify QualityPredictor predicts maintainability and readability with >85% accuracy."""
        res = self.orchestrator.qlt_prd.predict_code_quality()
        self.assertTrue(res["prediction_completed"])
        self.assertTrue(res["accuracy_exceeds_85_percent"])
        self.assertGreaterEqual(res["accuracy_percent"], 85.0)

    def test_13_bug_predictor_execution(self) -> None:
        """Verify BugPredictor analyzes vulnerability patterns with >80% accuracy."""
        res = self.orchestrator.bug_prd.predict_bugs_and_vulnerabilities()
        self.assertTrue(res["prediction_completed"])
        self.assertTrue(res["accuracy_exceeds_80_percent"])
        self.assertGreaterEqual(res["accuracy_percent"], 80.0)

    def test_14_performance_predictor_execution(self) -> None:
        """Verify PerformancePredictor analyzes O(n) bounds with >85% accuracy."""
        res = self.orchestrator.prf_prd.predict_performance_profile()
        self.assertTrue(res["prediction_completed"])
        self.assertTrue(res["accuracy_exceeds_85_percent"])
        self.assertGreaterEqual(res["accuracy_percent"], 85.0)

    def test_15_test_generator_ai_execution(self) -> None:
        """Verify TestGeneratorAI generates test fixtures and mocks with >90% coverage."""
        res = self.orchestrator.tst_gen.generate_test_suite()
        self.assertTrue(res["tests_generated"])
        self.assertTrue(res["coverage_exceeds_90_percent"])
        self.assertGreaterEqual(res["projected_coverage_percent"], 90.0)

    def test_16_refactoring_suggester_ai_execution(self) -> None:
        """Verify RefactoringSuggesterAI plans refactoring with >70% projected acceptance."""
        res = self.orchestrator.ref_sug.suggest_refactoring_plan()
        self.assertTrue(res["refactoring_planned"])
        self.assertTrue(res["acceptance_exceeds_70_percent"])
        self.assertGreaterEqual(res["projected_acceptance_rate"], 70.0)

    def test_17_code_reviewer_ai_execution(self) -> None:
        """Verify CodeReviewerAI reviews diffs with >85% review accuracy."""
        res = self.orchestrator.cde_rev.execute_code_review()
        self.assertTrue(res["review_completed"])
        self.assertTrue(res["accuracy_exceeds_85_percent"])
        self.assertGreaterEqual(res["accuracy_percent"], 85.0)

    def test_18_documentation_generator_ai_execution(self) -> None:
        """Verify DocumentationGeneratorAI achieves 100% documentation coverage."""
        res = self.orchestrator.doc_gen.generate_documentation()
        self.assertTrue(res["documentation_generated"])
        self.assertTrue(res["coverage_is_100_percent"])
        self.assertEqual(res["coverage_percent"], 100.0)

    def test_19_model_fine_tuner_execution(self) -> None:
        """Verify ModelFineTuner schedules LoRA training completed in under 24h."""
        res = self.orchestrator.mdl_ftn.fine_tune_and_deploy_model()
        self.assertTrue(res["fine_tuning_completed"])
        self.assertTrue(res["under_24_hours"])
        self.assertLessEqual(res["training_duration_hours"], 24.0)

    def test_20_multi_modal_processor_execution(self) -> None:
        """Verify MultiModalProcessor processes inputs with >90% accuracy."""
        res = self.orchestrator.mul_mod.process_multimodal_inputs()
        self.assertTrue(res["multimodal_processed"])
        self.assertTrue(res["accuracy_exceeds_90_percent"])
        self.assertGreaterEqual(res["overall_accuracy_percent"], 90.0)

    def test_21_full_orchestrator_lifecycle(self) -> None:
        """Verify complete orchestrator execution across all 15 subsystems."""
        envelope = {"payload": {"cycle": "AI_EXTENSIONS_SWEEP"}}
        self.orchestrator.initialize(envelope)
        result = self.orchestrator.process(envelope)
        validated = self.orchestrator.validate(result)
        self.assertEqual(validated["status"], "COMPLETED")
        self.assertTrue(validated["ai_extensions_report"]["ai_suite_healthy"])
        self.assertEqual(validated["ai_extensions_report"]["system_status"], "AI_EXTENSIONS_OPERATIONAL")
        self.orchestrator.cleanup()


if __name__ == "__main__":
    unittest.main()
