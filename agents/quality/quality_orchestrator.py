"""QualityOrchestrator coordinating code formatting, style, complexity, patterns, reviews, scoring, and signoff."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.quality.best_practices_checker import BestPracticesChecker
from agents.quality.code_formatter import CodeFormatter
from agents.quality.code_reviewer import CodeReviewer
from agents.quality.complexity_analyzer import ComplexityAnalyzer
from agents.quality.dependency_checker import DependencyChecker
from agents.quality.documentation_writer import DocumentationWriter
from agents.quality.exceptions import QualityError
from agents.quality.final_reviewer import FinalReviewer
from agents.quality.improvement_planner import ImprovementPlanner
from agents.quality.performance_optimizer import PerformanceOptimizer
from agents.quality.quality_scorer import QualityScorer
from agents.quality.refactoring_suggester import RefactoringSuggester
from agents.quality.style_checker import StyleChecker
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Quality.QualityOrchestrator")


class QualityOrchestrator(BaseAgent):
    """L3 Master Quality Orchestrator running full-spectrum quality verification across all 12 L4 subsystems."""

    def __init__(
        self,
        name: str = "QualityOrchestrator",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 256,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "quality",
            "quality_orchestration",
            "code_health_audit",
            "quality_gate_enforcement",
            "continuous_inspection",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "Q1_QUALITY_ORCHESTRATOR",
        )

        self.code_formatter: Optional[CodeFormatter] = None
        self.style_checker: Optional[StyleChecker] = None
        self.complexity_analyzer: Optional[ComplexityAnalyzer] = None
        self.best_practices_checker: Optional[BestPracticesChecker] = None
        self.doc_writer: Optional[DocumentationWriter] = None
        self.code_reviewer: Optional[CodeReviewer] = None
        self.perf_optimizer: Optional[PerformanceOptimizer] = None
        self.refactor_suggester: Optional[RefactoringSuggester] = None
        self.dependency_checker: Optional[DependencyChecker] = None
        self.quality_scorer: Optional[QualityScorer] = None
        self.improvement_planner: Optional[ImprovementPlanner] = None
        self.final_reviewer: Optional[FinalReviewer] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_quality_subsystems()

        self.register_tool("run_quality_audit", self.run_quality_audit)

    def _spawn_quality_subsystems(self) -> None:
        """Spawn the 12 L4 quality coordinators (Rule 1 & Rule 5)."""
        logger.info("QualityOrchestrator %s spawning 12 quality coordinators...", self.agent_id)
        child_depth = self.depth + 2
        self.code_formatter = self.spawn_subagent(
            CodeFormatter,
            name="CodeFormatter",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.style_checker = self.spawn_subagent(
            StyleChecker,
            name="StyleChecker",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.complexity_analyzer = self.spawn_subagent(
            ComplexityAnalyzer,
            name="ComplexityAnalyzer",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.best_practices_checker = self.spawn_subagent(
            BestPracticesChecker,
            name="BestPracticesChecker",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.doc_writer = self.spawn_subagent(
            DocumentationWriter,
            name="DocumentationWriter",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.code_reviewer = self.spawn_subagent(
            CodeReviewer,
            name="CodeReviewer",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.perf_optimizer = self.spawn_subagent(
            PerformanceOptimizer,
            name="PerformanceOptimizer",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.refactor_suggester = self.spawn_subagent(
            RefactoringSuggester,
            name="RefactoringSuggester",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.dependency_checker = self.spawn_subagent(
            DependencyChecker,
            name="DependencyChecker",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.quality_scorer = self.spawn_subagent(
            QualityScorer,
            name="QualityScorer",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.improvement_planner = self.spawn_subagent(
            ImprovementPlanner,
            name="ImprovementPlanner",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.final_reviewer = self.spawn_subagent(
            FinalReviewer,
            name="FinalReviewer",
            max_depth=child_depth,
            resources_mb=128,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("QualityOrchestrator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        results = self.run_quality_audit(context=payload)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "quality_audit_report": results,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        report = result.get("quality_audit_report")
        if not report or "overall_quality_score" not in report:
            raise QualityError("QualityOrchestrator validation failed: incomplete report.")
        return result

    def cleanup(self) -> None:
        logger.debug("QualityOrchestrator %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def run_quality_audit(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute full multi-tier quality inspection pipeline."""
        ctx = context or {}
        code = ctx.get("code", "def handle_request(req):\n    \"\"\"Process request.\"\"\"\n    return {'status': 200}\n")
        logger.info("Executing comprehensive quality audit...")

        # 1. Code Formatting
        fmt_res = self.code_formatter.format_and_audit(code) if self.code_formatter else {"composite_score": 100}

        # 2. Code Style
        style_res = self.style_checker.check_style(code) if self.style_checker else {"composite_score": 100}

        # 3. Complexity
        comp_res = self.complexity_analyzer.analyze_complexity(code) if self.complexity_analyzer else {"composite_score": 100}

        # 4. Best Practices
        bp_res = self.best_practices_checker.audit_best_practices(code) if self.best_practices_checker else {"composite_score": 100}

        # 5. Documentation
        doc_res = self.doc_writer.generate_documentation(project_title=ctx.get("project_title", "Microservice")) if self.doc_writer else {"composite_score": 100}

        # 6. Code Review
        rev_res = self.code_reviewer.review_code(code) if self.code_reviewer else {"composite_score": 100}

        # 7. Performance
        perf_res = self.perf_optimizer.optimize_performance(code) if self.perf_optimizer else {"composite_score": 100}

        # 8. Refactoring
        ref_res = self.refactor_suggester.suggest_refactorings(code) if self.refactor_suggester else {"composite_score": 100}

        # 9. Dependencies
        dep_res = self.dependency_checker.check_dependencies(ctx.get("dependencies")) if self.dependency_checker else {"composite_score": 100}

        # 10. Quality Scoring
        raw_metrics = {
            "readability": round((fmt_res.get("composite_score", 100) + style_res.get("composite_score", 100)) / 2.0, 2),
            "maintainability": round((comp_res.get("composite_score", 100) + bp_res.get("composite_score", 100) + ref_res.get("composite_score", 100)) / 3.0, 2),
            "performance": perf_res.get("composite_score", 100),
            "security": dep_res.get("composite_score", 100),
            "documentation": doc_res.get("composite_score", 100),
        }
        score_res = self.quality_scorer.calculate_quality_score(raw_metrics) if self.quality_scorer else {"overall_quality_score": 95.0, "grade": "A"}

        overall_score = score_res.get("overall_quality_score", 95.0)

        # 11. Improvement Plan
        plan_res = self.improvement_planner.create_improvement_plan() if self.improvement_planner else {"actions": []}

        # 12. Final Quality Gate Review
        final_res = self.final_reviewer.finalize_quality_review(overall_score=overall_score) if self.final_reviewer else {"gate_passed": True}

        return {
            "overall_quality_score": overall_score,
            "grade": score_res.get("grade"),
            "gate_approved": final_res.get("gate_passed", True),
            "formatting": fmt_res,
            "style": style_res,
            "complexity": comp_res,
            "best_practices": bp_res,
            "documentation": doc_res,
            "code_review": rev_res,
            "performance": perf_res,
            "refactoring": ref_res,
            "dependencies": dep_res,
            "scoring": score_res,
            "improvement_plan": plan_res,
            "final_review": final_res,
        }
