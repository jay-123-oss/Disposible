"""TestValidator analyzing test execution results, diagnosing failures, and enforcing quality gates."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.testing.exceptions import ValidationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Testing.TestValidator")


# ==============================================================================
# L5 Specialized Validation Agents
# ==============================================================================

class ResultChecker(BaseAgent):
    """L5 agent parsing test outcomes and tallying pass/fail/skip counts."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ResultChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        total = payload.get("total_tests", 24)
        failed = payload.get("failed_tests", 0)
        passed = total - failed
        return {
            "status": "COMPLETED",
            "passed": passed,
            "failed": failed,
            "total": total,
            "pass_rate": round((passed / max(1, total)) * 100, 2),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "pass_rate" not in result:
            raise ValidationError("ResultChecker missing pass rate.")
        return result

    def cleanup(self) -> None:
        logger.debug("ResultChecker %s cleaned up.", self.agent_id)


class FailureAnalyzer(BaseAgent):
    """L5 agent classifying failure patterns, stack traces, and regression causes."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("FailureAnalyzer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        failures = payload.get("failures", [])
        diagnostics: List[Dict[str, str]] = []
        for fail in failures:
            diagnostics.append({
                "test": fail.get("test_name", "unknown_test"),
                "reason": fail.get("message", "Assertion error"),
                "severity": "HIGH" if "500" in str(fail) else "MEDIUM",
            })
        return {"status": "COMPLETED", "diagnostics": diagnostics}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "diagnostics" not in result:
            raise ValidationError("FailureAnalyzer missing diagnostics.")
        return result

    def cleanup(self) -> None:
        logger.debug("FailureAnalyzer %s cleaned up.", self.agent_id)


class QualityGateChecker(BaseAgent):
    """L5 agent evaluating results against Quality Gate thresholds (QG-4 Unit & QG-5 Integration)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("QualityGateChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        pass_rate = payload.get("pass_rate", 100.0)
        coverage_pct = payload.get("coverage_pct", 88.0)
        min_score = payload.get("min_score", 85.0)

        composite_score = round(0.60 * pass_rate + 0.40 * coverage_pct, 2)
        approved = composite_score >= min_score and payload.get("failed", 0) == 0

        return {
            "status": "COMPLETED",
            "composite_score": composite_score,
            "gate_passed": approved,
            "min_score": min_score,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "gate_passed" not in result:
            raise ValidationError("QualityGateChecker missing gate status.")
        return result

    def cleanup(self) -> None:
        logger.debug("QualityGateChecker %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 TestValidator Agent
# ==============================================================================

class TestValidator(BaseAgent):
    """L4 coordinator for aggregating test outcomes, diagnosing regressions, and approving quality gates."""

    def __init__(
        self,
        name: str = "TestValidator",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 192,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "test_validation",
            "failure_analysis",
            "quality_gate_enforcement",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "T15_TEST_VALIDATOR",
        )

        self.result_checker: Optional[ResultChecker] = None
        self.failure_analyzer: Optional[FailureAnalyzer] = None
        self.gate_checker: Optional[QualityGateChecker] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("validate_test_results", self.validate_test_results)

    def _spawn_subagents(self) -> None:
        """Spawn ResultChecker, FailureAnalyzer, and QualityGateChecker (Rule 1 & Rule 5)."""
        logger.info("TestValidator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.result_checker = self.spawn_subagent(
            ResultChecker,
            name="ResultChecker",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.failure_analyzer = self.spawn_subagent(
            FailureAnalyzer,
            name="FailureAnalyzer",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.gate_checker = self.spawn_subagent(
            QualityGateChecker,
            name="QualityGateChecker",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TestValidator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        validation = self.validate_test_results(
            total_tests=payload.get("total_tests", 24),
            failed_tests=payload.get("failed_tests", 0),
            coverage_pct=payload.get("coverage_pct", 88.0),
            failures=payload.get("failures", []),
        )
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "validation_summary": validation,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        summary = result.get("validation_summary")
        if not summary or "gate_approved" not in summary:
            raise ValidationError("TestValidator produced incomplete summary.")
        return result

    def cleanup(self) -> None:
        logger.debug("TestValidator %s cleanup complete.", self.agent_id)

    def validate_test_results(
        self,
        total_tests: int = 24,
        failed_tests: int = 0,
        coverage_pct: float = 88.0,
        failures: Optional[List[Dict[str, Any]]] = None,
        min_score: float = 85.0,
    ) -> Dict[str, Any]:
        """Aggregate test results, check failures, and assert quality gate satisfaction."""
        rc_res = self.result_checker.process({
            "payload": {"total_tests": total_tests, "failed_tests": failed_tests}
        }) if self.result_checker else {"pass_rate": 100.0, "passed": total_tests, "failed": 0}

        fa_res = self.failure_analyzer.process({
            "payload": {"failures": failures or []}
        }) if self.failure_analyzer else {"diagnostics": []}

        gate_res = self.gate_checker.process({
            "payload": {
                "pass_rate": rc_res["pass_rate"],
                "coverage_pct": coverage_pct,
                "failed": failed_tests,
                "min_score": min_score,
            }
        }) if self.gate_checker else {"composite_score": 95.0, "gate_passed": True}

        return {
            "total_tests": total_tests,
            "passed_tests": rc_res["passed"],
            "failed_tests": failed_tests,
            "pass_rate_pct": rc_res["pass_rate"],
            "coverage_pct": coverage_pct,
            "composite_score": gate_res["composite_score"],
            "gate_approved": gate_res["gate_passed"],
            "diagnostics": fa_res["diagnostics"],
        }
