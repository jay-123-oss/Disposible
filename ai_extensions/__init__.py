"""AI & ML Extensions Layer Package.

Exports all 16 coordinators, 61 atomic subagents, domain exceptions, and registry helper.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from core.registry import AgentRegistry
from ai_extensions.ai_extensions_orchestrator import AIExtensionsOrchestrator
from ai_extensions.auto_completion_engine import (
    AcceptanceTracker,
    AutoCompletionEngine,
    ContextAnalyzer,
    SuggestionRanker,
    TokenPredictor,
)
from ai_extensions.bug_predictor import (
    BugPredictor,
    BugProbabilityCalculator,
    MitigationSuggester,
    PatternAnalyzer,
    VulnerabilityDetector,
)
from ai_extensions.code_embedder import (
    CodeEmbedder,
    CodeVectorizer,
    FileEmbedder,
    FunctionEmbedder,
    RepoEmbedder,
)
from ai_extensions.code_generator import (
    CodeGenerator,
    GoGenerator,
    JavaGenerator,
    NodeGenerator,
    PythonGenerator,
    RustGenerator,
)
from ai_extensions.code_reviewer_ai import (
    CodeAnalyzer,
    CodeReviewerAI,
    CommentGenerator,
    IssueDetector,
    ReviewSummarizer,
)
from ai_extensions.cost_optimizer import (
    BatchProcessor,
    CostOptimizer,
    ModelBudgetManager,
    SmartCacher,
    TokenUsageTracker,
)
from ai_extensions.documentation_generator_ai import (
    CodeUnderstander,
    DocGenerator,
    DocPlanner,
    DocumentationGeneratorAI,
    DocValidator,
)
from ai_extensions.exceptions import (
    AIExtensionError,
    AutoCompletionError,
    BugPredictionError,
    CodeGenerationError,
    CodeReviewError,
    CostOptimizationError,
    DocumentationError,
    EmbeddingError,
    FineTuningError,
    ModelSelectionError,
    MultiModalError,
    PerformancePredictionError,
    QualityPredictionError,
    RefactoringError,
    SemanticSearchError,
    TestGenerationError,
)
from ai_extensions.model_fine_tuner import (
    DataPreparer,
    ModelDeployer,
    ModelEvaluator,
    ModelFineTuner,
    TrainingExecutor,
)
from ai_extensions.model_selector import (
    ModelCapabilityChecker,
    ModelCostAnalyzer,
    ModelPerformanceAnalyzer,
    ModelRouter,
    ModelSelector,
)
from ai_extensions.multi_modal_processor import (
    AudioProcessor,
    ImageProcessor,
    MultiModalProcessor,
    TextExtractor,
    VideoProcessor,
)
from ai_extensions.performance_predictor import (
    BottleneckDetector,
    OptimizationSuggester,
    PerformancePredictor,
    SpaceComplexityAnalyzer,
    TimeComplexityAnalyzer,
)
from ai_extensions.quality_predictor import (
    ComplexityAnalyzer,
    MaintainabilityPredictor,
    QualityInsightsGenerator,
    QualityPredictor,
    ReadabilityScorer,
)
from ai_extensions.refactoring_suggester_ai import (
    ImpactAnalyzer,
    PatternMatcher,
    RefactoringPlanner,
    RefactoringSuggesterAI,
    SmellDetector,
)
from ai_extensions.semantic_searcher import (
    ContextRetriever,
    QueryParser,
    ResultRanker,
    SemanticSearcher,
    VectorSearcher,
)
from ai_extensions.test_generator_ai import (
    AssertionGenerator,
    MockGeneratorAI,
    TestDataGenerator,
    TestGeneratorAI,
    TestIntentAnalyzer,
)

logger = logging.getLogger("FractalCore.AIExtensions")

__all__ = [
    # Master Orchestrator (L3)
    "AIExtensionsOrchestrator",
    # Coordinators (L4)
    "ModelSelector",
    "CostOptimizer",
    "CodeEmbedder",
    "SemanticSearcher",
    "AutoCompletionEngine",
    "CodeGenerator",
    "QualityPredictor",
    "BugPredictor",
    "PerformancePredictor",
    "TestGeneratorAI",
    "RefactoringSuggesterAI",
    "CodeReviewerAI",
    "DocumentationGeneratorAI",
    "ModelFineTuner",
    "MultiModalProcessor",
    # Atomic Workers (L5)
    "ModelCapabilityChecker",
    "ModelPerformanceAnalyzer",
    "ModelCostAnalyzer",
    "ModelRouter",
    "TokenUsageTracker",
    "SmartCacher",
    "BatchProcessor",
    "ModelBudgetManager",
    "CodeVectorizer",
    "FunctionEmbedder",
    "FileEmbedder",
    "RepoEmbedder",
    "QueryParser",
    "VectorSearcher",
    "ResultRanker",
    "ContextRetriever",
    "ContextAnalyzer",
    "TokenPredictor",
    "SuggestionRanker",
    "AcceptanceTracker",
    "PythonGenerator",
    "NodeGenerator",
    "GoGenerator",
    "RustGenerator",
    "JavaGenerator",
    "ComplexityAnalyzer",
    "MaintainabilityPredictor",
    "ReadabilityScorer",
    "QualityInsightsGenerator",
    "PatternAnalyzer",
    "VulnerabilityDetector",
    "BugProbabilityCalculator",
    "MitigationSuggester",
    "TimeComplexityAnalyzer",
    "SpaceComplexityAnalyzer",
    "BottleneckDetector",
    "OptimizationSuggester",
    "TestIntentAnalyzer",
    "TestDataGenerator",
    "MockGeneratorAI",
    "AssertionGenerator",
    "SmellDetector",
    "PatternMatcher",
    "RefactoringPlanner",
    "ImpactAnalyzer",
    "CodeAnalyzer",
    "IssueDetector",
    "CommentGenerator",
    "ReviewSummarizer",
    "CodeUnderstander",
    "DocPlanner",
    "DocGenerator",
    "DocValidator",
    "DataPreparer",
    "TrainingExecutor",
    "ModelEvaluator",
    "ModelDeployer",
    "ImageProcessor",
    "AudioProcessor",
    "VideoProcessor",
    "TextExtractor",
    # Exceptions
    "AIExtensionError",
    "ModelSelectionError",
    "CostOptimizationError",
    "EmbeddingError",
    "SemanticSearchError",
    "AutoCompletionError",
    "CodeGenerationError",
    "QualityPredictionError",
    "BugPredictionError",
    "PerformancePredictionError",
    "TestGenerationError",
    "RefactoringError",
    "CodeReviewError",
    "DocumentationError",
    "FineTuningError",
    "MultiModalError",
    # Registry Helper
    "register_all_ai_extensions_agents",
]


def register_all_ai_extensions_agents(
    registry: AgentRegistry,
    parent_orchestrator: Optional[AIExtensionsOrchestrator] = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Instantiate and register all 16 AI Extensions coordinators and 61 subagents into registry."""
    orch = parent_orchestrator or AIExtensionsOrchestrator(
        agent_id="A1_AI_EXTENSIONS_ORCHESTRATOR",
        max_depth=max_depth,
        auto_spawn_subagents=True,
    )
    registry.register_agent(orch)
    registered_count = 1

    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(orch)

    logger.info("Successfully registered %d AI Extensions domain agents into registry.", registered_count)
    return {
        "ai_extensions_orchestrator": orch,
        "total_registered": registered_count,
    }
