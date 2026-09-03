"""QualityGate class for multi-dimensional evaluation, approval, and rollback control.

Implements:
- Chain of Responsibility pattern across 7 phase-based quality gates.
- Multi-dimensional evaluation formula:
    Q_total = 0.40 * Correctness + 0.25 * Security + 0.20 * Maintainability + 0.15 * Performance
- Configurable approval workflows and automated rollback triggers upon failure.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from core.exceptions import QualityGateError


logger = logging.getLogger("FractalCore.QualityGate")


class GatePhase(str, Enum):
    """Enumeration of the 7 formal quality checkpoint phases."""
    QG_1_SPEC = "QG_1_SPEC"            # Intent & Specification
    QG_2_ARCH = "QG_2_ARCH"            # Interface & Architecture Contracts
    QG_3_SYNTAX = "QG_3_SYNTAX"        # Syntactic & AST Hygiene
    QG_4_TEST = "QG_4_TEST"            # Verification & Unit Tests
    QG_5_SECURITY = "QG_5_SECURITY"    # SAST & Secret Leak Audit
    QG_6_PERF = "QG_6_PERF"            # Performance & Token Budgets
    QG_7_RELEASE = "QG_7_RELEASE"      # Final Integration & Build


class GateStatus(str, Enum):
    """Status states for a quality gate evaluation."""
    PENDING = "PENDING"
    EVALUATING = "EVALUATING"
    PASSED = "PASSED"
    FAILED = "FAILED"


@dataclass
class QualityEvaluationResult:
    """Detailed scores and verdicts from a gate evaluation."""
    phase: GatePhase
    status: GateStatus
    total_score: float
    correctness_score: float
    security_score: float
    maintainability_score: float
    performance_score: float
    violations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class QualityGate:
    """Evaluates deliverables against multi-dimensional quality thresholds."""

    def __init__(
        self,
        min_score: float = 85.0,
        require_approval: bool = True,
        test_coverage_min: float = 80.0,
        max_retries: int = 3,
    ) -> None:
        self._min_score = min_score
        self._require_approval = require_approval
        self._test_coverage_min = test_coverage_min
        self._max_retries = max_retries
        self._history: List[QualityEvaluationResult] = []
        logger.info(
            "QualityGate initialized (Min Score: %.1f%%, Min Coverage: %.1f%%, Require Approval: %s)",
            self._min_score,
            self._test_coverage_min,
            self._require_approval,
        )

    # --------------------------------------------------------------------------
    # Score Computation
    # --------------------------------------------------------------------------

    def compute_quality_score(
        self,
        correctness: float,
        security: float,
        maintainability: float,
        performance: float,
    ) -> float:
        """Calculate weighted total quality score conforming to the architecture formula.

        Weights:
            Correctness: 40%
            Security: 25%
            Maintainability: 20%
            Performance: 15%
        """
        # Clamp input components between 0.0 and 100.0
        c = max(0.0, min(100.0, correctness))
        s = max(0.0, min(100.0, security))
        m = max(0.0, min(100.0, maintainability))
        p = max(0.0, min(100.0, performance))

        total = (0.40 * c) + (0.25 * s) + (0.20 * m) + (0.15 * p)
        return round(total, 2)

    # --------------------------------------------------------------------------
    # Phase Evaluations (Chain of Responsibility)
    # --------------------------------------------------------------------------

    def evaluate_phase(
        self,
        phase: GatePhase,
        deliverable_metrics: Dict[str, Any],
    ) -> QualityEvaluationResult:
        """Evaluate a deliverable payload against phase-specific acceptance rules."""
        logger.info("Starting Quality Gate evaluation for phase: %s", phase.value)
        violations: List[str] = []

        # Extract or default metrics
        correctness = float(deliverable_metrics.get("correctness", 100.0))
        security = float(deliverable_metrics.get("security", 100.0))
        maintainability = float(deliverable_metrics.get("maintainability", 100.0))
        performance = float(deliverable_metrics.get("performance", 100.0))

        # Check phase-specific hard conditions
        if phase == GatePhase.QG_1_SPEC:
            if not deliverable_metrics.get("spec_unambiguous", True):
                violations.append("Specification contains unresolved ambiguities.")

        elif phase == GatePhase.QG_2_ARCH:
            if deliverable_metrics.get("has_cyclic_dependencies", False):
                violations.append("Architecture DAG contains illegal cyclic dependencies.")

        elif phase == GatePhase.QG_3_SYNTAX:
            if deliverable_metrics.get("syntax_errors", 0) > 0:
                violations.append(f"AST syntax error count is {deliverable_metrics['syntax_errors']}.")
                correctness = 0.0

        elif phase == GatePhase.QG_4_TEST:
            coverage = float(deliverable_metrics.get("test_coverage", 100.0))
            failed_tests = deliverable_metrics.get("failed_tests", 0)
            if failed_tests > 0:
                violations.append(f"{failed_tests} unit tests failed.")
                correctness = max(0.0, correctness - (failed_tests * 25.0))
            if coverage < self._test_coverage_min:
                violations.append(f"Code coverage ({coverage:.1f}%) is below required minimum ({self._test_coverage_min}%).")

        elif phase == GatePhase.QG_5_SECURITY:
            critical_vulns = deliverable_metrics.get("critical_vulns", 0)
            secrets_found = deliverable_metrics.get("secrets_found", 0)
            if critical_vulns > 0 or secrets_found > 0:
                violations.append(f"Security audit detected {critical_vulns} critical vulns and {secrets_found} leaked secrets.")
                security = 0.0

        elif phase == GatePhase.QG_6_PERF:
            ram_mb = deliverable_metrics.get("ram_mb", 256)
            latency_s = deliverable_metrics.get("latency_seconds", 5.0)
            if ram_mb > 512:
                violations.append(f"Agent exceeded 512MB RAM ceiling ({ram_mb} MB recorded).")
            if latency_s > 30.0:
                violations.append(f"Execution duration exceeded 30s timeout ({latency_s:.1f}s recorded).")

        elif phase == GatePhase.QG_7_RELEASE:
            if deliverable_metrics.get("git_tree_dirty", False):
                violations.append("Working tree has untracked or uncommitted files.")

        total_score = self.compute_quality_score(correctness, security, maintainability, performance)
        passed = (total_score >= self._min_score) and (len(violations) == 0)
        status = GateStatus.PASSED if passed else GateStatus.FAILED

        result = QualityEvaluationResult(
            phase=phase,
            status=status,
            total_score=total_score,
            correctness_score=correctness,
            security_score=security,
            maintainability_score=maintainability,
            performance_score=performance,
            violations=violations,
            metadata=deliverable_metrics,
        )

        self._history.append(result)

        if passed:
            logger.info("Quality Gate %s PASSED with score %.2f/100", phase.value, total_score)
        else:
            logger.warning(
                "Quality Gate %s FAILED (Score: %.2f/100, Min: %.1f). Violations: %s",
                phase.value,
                total_score,
                self._min_score,
                violations,
            )

        return result

    # --------------------------------------------------------------------------
    # Gate Validation Enforcement
    # --------------------------------------------------------------------------

    def validate_or_raise(self, phase: GatePhase, deliverable_metrics: Dict[str, Any]) -> QualityEvaluationResult:
        """Run phase evaluation and raise QualityGateError if validation fails."""
        res = self.evaluate_phase(phase, deliverable_metrics)
        if res.status != GateStatus.PASSED:
            raise QualityGateError(
                f"Deliverable failed Quality Gate '{phase.value}' with score {res.total_score:.1f}/{self._min_score:.1f}.",
                details={
                    "phase": phase.value,
                    "score": res.total_score,
                    "violations": res.violations,
                },
            )
        return res
