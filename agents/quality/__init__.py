"""Quality Domain Agents for the Fractal Multi-Agent Coding System.

Exports all 14 specialized quality agents and atomic subagents across levels L3 to L5,
along with the registration helper `register_all_quality_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from agents.quality.best_practices_checker import (
    BestPracticesChecker,
    DryChecker,
    PatternValidator,
    SolidChecker,
)
from agents.quality.code_formatter import (
    CodeFormatter,
    IndentationChecker,
    LineLengthChecker,
    SpacingChecker,
)
from agents.quality.code_reviewer import (
    BugFinder,
    CodeReviewer,
    EdgeCaseReviewer,
    LogicChecker,
)
from agents.quality.complexity_analyzer import (
    CognitiveChecker,
    ComplexityAnalyzer,
    CyclomaticChecker,
    NestingChecker,
)
from agents.quality.dependency_checker import (
    CompatibilityChecker,
    DependencyChecker,
    DependencySecurityChecker,
    VersionChecker,
)
from agents.quality.documentation_writer import (
    DocumentationWriter,
    JsdocGenerator,
    ReadmeGenerator,
    SwaggerGenerator,
)
from agents.quality.exceptions import (
    BestPracticeError,
    ComplexityError,
    DependencyError,
    DocumentationError,
    FormattingError,
    PerformanceError,
    QualityError,
    RefactoringError,
    ReviewError,
    ScoringError,
    StyleError,
)
from agents.quality.final_reviewer import (
    ApprovalGenerator,
    FinalReviewer,
    GateChecker,
    ReportFinalizer,
)
from agents.quality.improvement_planner import (
    ActionGenerator,
    ImprovementPlanner,
    PrioritySetting,
    TimelineEstimator,
)
from agents.quality.performance_optimizer import (
    AlgorithmAnalyzer,
    CacheSuggester,
    PerformanceOptimizer,
    QueryOptimizer,
)
from agents.quality.quality_orchestrator import QualityOrchestrator
from agents.quality.quality_scorer import (
    BenchmarkComparator,
    MetricCollector,
    QualityScorer,
    WeightedCalculator,
)
from agents.quality.refactoring_suggester import (
    DuplicationFinder,
    MergeSuggester,
    RefactoringSuggester,
    SplitSuggester,
)
from agents.quality.style_checker import (
    CommentChecker,
    ImportChecker,
    NamingChecker,
    StyleChecker,
)
from core.registry import AgentRegistry


logger = logging.getLogger("FractalCore.Quality")

__all__ = [
    # Master Orchestrator
    "QualityOrchestrator",
    # Formatting
    "CodeFormatter",
    "IndentationChecker",
    "SpacingChecker",
    "LineLengthChecker",
    # Style
    "StyleChecker",
    "NamingChecker",
    "CommentChecker",
    "ImportChecker",
    # Complexity
    "ComplexityAnalyzer",
    "CyclomaticChecker",
    "CognitiveChecker",
    "NestingChecker",
    # Best Practices
    "BestPracticesChecker",
    "PatternValidator",
    "SolidChecker",
    "DryChecker",
    # Documentation
    "DocumentationWriter",
    "JsdocGenerator",
    "SwaggerGenerator",
    "ReadmeGenerator",
    # Code Review
    "CodeReviewer",
    "LogicChecker",
    "BugFinder",
    "EdgeCaseReviewer",
    # Performance Optimization
    "PerformanceOptimizer",
    "AlgorithmAnalyzer",
    "CacheSuggester",
    "QueryOptimizer",
    # Refactoring Suggestions
    "RefactoringSuggester",
    "DuplicationFinder",
    "SplitSuggester",
    "MergeSuggester",
    # Dependency Checking
    "DependencyChecker",
    "VersionChecker",
    "DependencySecurityChecker",
    "CompatibilityChecker",
    # Quality Scoring
    "QualityScorer",
    "MetricCollector",
    "WeightedCalculator",
    "BenchmarkComparator",
    # Improvement Planning
    "ImprovementPlanner",
    "PrioritySetting",
    "ActionGenerator",
    "TimelineEstimator",
    # Final Review & Gates
    "FinalReviewer",
    "GateChecker",
    "ApprovalGenerator",
    "ReportFinalizer",
    # Exceptions
    "QualityError",
    "FormattingError",
    "StyleError",
    "ComplexityError",
    "BestPracticeError",
    "DocumentationError",
    "ReviewError",
    "PerformanceError",
    "RefactoringError",
    "DependencyError",
    "ScoringError",
    # Registration Helper
    "register_all_quality_agents",
]


def register_all_quality_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Register all quality layer agents into the AgentRegistry.

    Args:
        registry: The central AgentRegistry singleton.
        parent_agent: Optional supervising quality domain coordinator.
        max_depth: Global depth ceiling for quality hierarchy.

    Returns:
        Dict mapping agent_id to instantiated agent instances.
    """
    logger.info("Registering all quality domain agents into AgentRegistry...")

    # Root Quality Orchestrator (L3)
    quality_orchestrator = QualityOrchestrator(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="Q1_QUALITY_ORCHESTRATOR",
        auto_spawn_subagents=True,
    )
    registry.register_agent(quality_orchestrator)

    # Register all spawned children recursively
    registered_count = 1
    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(quality_orchestrator)

    logger.info("Successfully registered %d quality domain agents into registry.", registered_count)
    return {
        "quality_orchestrator": quality_orchestrator,
        "total_registered": registered_count,
    }
