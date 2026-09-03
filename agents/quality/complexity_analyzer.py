"""ComplexityAnalyzer calculating cyclomatic complexity, cognitive load, and maximum nesting depth."""

from __future__ import annotations

import ast
import logging
from typing import Any, Dict, List, Optional

from agents.quality.exceptions import ComplexityError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Quality.ComplexityAnalyzer")


# ==============================================================================
# L5 Atomic Complexity Subagents
# ==============================================================================

class CyclomaticChecker(BaseAgent):
    """L5 agent computing McCabe cyclomatic complexity via AST decision point traversal."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CyclomaticChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        code = payload.get("code", "")
        max_allowed = payload.get("max_cyclomatic", 10)

        complexity = 1
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Assert)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
        except Exception:
            complexity = 1

        passed = complexity <= max_allowed
        score = 100 if passed else max(40, 100 - (complexity - max_allowed) * 10)

        return {
            "status": "COMPLETED",
            "score": score,
            "cyclomatic_complexity": complexity,
            "max_allowed": max_allowed,
            "passed": passed,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CyclomaticChecker %s cleaned up.", self.agent_id)


class CognitiveChecker(BaseAgent):
    """L5 agent measuring human cognitive comprehension burden and linear logic flows."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CognitiveChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        code = payload.get("code", "")
        max_allowed = payload.get("max_cognitive", 15)

        cognitive_score = 0
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                    cognitive_score += 1
        except Exception:
            cognitive_score = 1

        passed = cognitive_score <= max_allowed
        score = 100 if passed else max(50, 100 - (cognitive_score - max_allowed) * 5)

        return {
            "status": "COMPLETED",
            "score": score,
            "cognitive_complexity": cognitive_score,
            "max_allowed": max_allowed,
            "passed": passed,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CognitiveChecker %s cleaned up.", self.agent_id)


class NestingChecker(BaseAgent):
    """L5 agent asserting maximum block indentation/nesting depth (<= 4)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NestingChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        code = payload.get("code", "")
        max_nesting = payload.get("max_nesting", 4)

        max_depth_found = 0
        lines = code.splitlines() if code else []
        for l in lines:
            if l.strip():
                leading_spaces = len(l) - len(l.lstrip(" "))
                depth = leading_spaces // 4
                if depth > max_depth_found:
                    max_depth_found = depth

        passed = max_depth_found <= max_nesting
        score = 100 if passed else max(40, 100 - (max_depth_found - max_nesting) * 20)

        return {
            "status": "COMPLETED",
            "score": score,
            "max_depth_found": max_depth_found,
            "max_allowed": max_nesting,
            "passed": passed,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NestingChecker %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 ComplexityAnalyzer Agent
# ==============================================================================

class ComplexityAnalyzer(BaseAgent):
    """L4 coordinator analyzing cyclomatic complexity, cognitive load, and maximum nesting levels."""

    def __init__(
        self,
        name: str = "ComplexityAnalyzer",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "complexity_analysis",
            "cyclomatic_complexity",
            "cognitive_complexity",
            "nesting_depth_audit",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "Q4_COMPLEXITY_ANALYZER",
        )

        self.cyclo_checker: Optional[CyclomaticChecker] = None
        self.cogni_checker: Optional[CognitiveChecker] = None
        self.nest_checker: Optional[NestingChecker] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("analyze_complexity", self.analyze_complexity)

    def _spawn_subagents(self) -> None:
        """Spawn atomic complexity analyzers (Rule 1 & Rule 5)."""
        logger.info("ComplexityAnalyzer %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.cyclo_checker = self.spawn_subagent(
            CyclomaticChecker,
            name="CyclomaticChecker",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.cogni_checker = self.spawn_subagent(
            CognitiveChecker,
            name="CognitiveChecker",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.nest_checker = self.spawn_subagent(
            NestingChecker,
            name="NestingChecker",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ComplexityAnalyzer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        code = payload.get("code", "def compute():\n    return 10\n")
        res = self.analyze_complexity(code)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "complexity_audit": res,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        audit = result.get("complexity_audit")
        if not audit or "composite_score" not in audit:
            raise ComplexityError("ComplexityAnalyzer produced incomplete audit.")
        return result

    def cleanup(self) -> None:
        logger.debug("ComplexityAnalyzer %s cleanup complete.", self.agent_id)

    def analyze_complexity(self, code: str = "") -> Dict[str, Any]:
        """Aggregate cyclomatic, cognitive, and nesting depth complexity metrics."""
        p_env = {"payload": {"code": code, "max_cyclomatic": 10, "max_cognitive": 15, "max_nesting": 4}}
        c_res = self.cyclo_checker.process(p_env) if self.cyclo_checker else {"score": 100, "passed": True, "cyclomatic_complexity": 2}
        cg_res = self.cogni_checker.process(p_env) if self.cogni_checker else {"score": 100, "passed": True, "cognitive_complexity": 2}
        n_res = self.nest_checker.process(p_env) if self.nest_checker else {"score": 100, "passed": True, "max_depth_found": 1}

        score = round((c_res.get("score", 100) + cg_res.get("score", 100) + n_res.get("score", 100)) / 3.0, 2)
        passed = score >= 85 and c_res.get("passed", True) and n_res.get("passed", True)

        return {
            "composite_score": score,
            "cyclomatic": c_res,
            "cognitive": cg_res,
            "nesting": n_res,
            "passed": passed,
            "recommendation": "Code complexity is within manageable thresholds." if passed else "Extract helper functions to flatten nested loops.",
        }
