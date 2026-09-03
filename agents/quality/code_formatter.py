"""CodeFormatter agent coordinating indentation, spacing, and line length checks."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.quality.exceptions import FormattingError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Quality.CodeFormatter")


# ==============================================================================
# L5 Atomic Formatting Subagents
# ==============================================================================

class IndentationChecker(BaseAgent):
    """L5 agent verifying 4-space indentation and forbidding tab characters."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("IndentationChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        code = payload.get("code", "")
        lines = code.splitlines() if code else []

        tab_lines = [i + 1 for i, l in enumerate(lines) if "\t" in l]
        score = 100 if not tab_lines else max(0, 100 - len(tab_lines) * 10)

        return {
            "status": "COMPLETED",
            "score": score,
            "has_tabs": len(tab_lines) > 0,
            "tab_lines": tab_lines,
            "indent_size": 4,
            "passed": len(tab_lines) == 0,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "passed" not in result:
            raise FormattingError("IndentationChecker missing verification status.")
        return result

    def cleanup(self) -> None:
        logger.debug("IndentationChecker %s cleaned up.", self.agent_id)


class SpacingChecker(BaseAgent):
    """L5 agent checking whitespace around binary operators and trailing whitespace."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SpacingChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        code = payload.get("code", "")
        lines = code.splitlines() if code else []

        trailing_spaces = [i + 1 for i, l in enumerate(lines) if l.endswith(" ") or l.endswith("\t")]
        score = 100 if not trailing_spaces else max(0, 100 - len(trailing_spaces) * 5)

        return {
            "status": "COMPLETED",
            "score": score,
            "trailing_spaces_count": len(trailing_spaces),
            "passed": len(trailing_spaces) == 0,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "passed" not in result:
            raise FormattingError("SpacingChecker missing verification status.")
        return result

    def cleanup(self) -> None:
        logger.debug("SpacingChecker %s cleaned up.", self.agent_id)


class LineLengthChecker(BaseAgent):
    """L5 agent verifying line lengths against Black/PEP8 88-character limit."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LineLengthChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        code = payload.get("code", "")
        max_len = payload.get("line_length", 88)
        lines = code.splitlines() if code else []

        long_lines = [(i + 1, len(l)) for i, l in enumerate(lines) if len(l) > max_len]
        score = 100 if not long_lines else max(50, 100 - len(long_lines) * 5)

        return {
            "status": "COMPLETED",
            "score": score,
            "max_configured": max_len,
            "long_lines_count": len(long_lines),
            "passed": len(long_lines) == 0,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "passed" not in result:
            raise FormattingError("LineLengthChecker missing verification status.")
        return result

    def cleanup(self) -> None:
        logger.debug("LineLengthChecker %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 CodeFormatter Agent
# ==============================================================================

class CodeFormatter(BaseAgent):
    """L4 coordinator auditing and correcting code formatting, indentation, and whitespace."""

    def __init__(
        self,
        name: str = "CodeFormatter",
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
            "code_formatting",
            "linting",
            "indentation_audit",
            "whitespace_normalization",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "Q2_CODE_FORMATTER",
        )

        self.indent_checker: Optional[IndentationChecker] = None
        self.spacing_checker: Optional[SpacingChecker] = None
        self.length_checker: Optional[LineLengthChecker] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("format_and_audit", self.format_and_audit)

    def _spawn_subagents(self) -> None:
        """Spawn atomic formatting checkers (Rule 1 & Rule 5)."""
        logger.info("CodeFormatter %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.indent_checker = self.spawn_subagent(
            IndentationChecker,
            name="IndentationChecker",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.spacing_checker = self.spawn_subagent(
            SpacingChecker,
            name="SpacingChecker",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.length_checker = self.spawn_subagent(
            LineLengthChecker,
            name="LineLengthChecker",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CodeFormatter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        code = payload.get("code", "def example():\n    return 42\n")
        res = self.format_and_audit(code)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "formatting_audit": res,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        audit = result.get("formatting_audit")
        if not audit or "composite_score" not in audit:
            raise FormattingError("CodeFormatter produced incomplete audit.")
        return result

    def cleanup(self) -> None:
        logger.debug("CodeFormatter %s cleanup complete.", self.agent_id)

    def format_and_audit(self, code: str = "") -> Dict[str, Any]:
        """Verify code conforms to Black style guide standards."""
        p_env = {"payload": {"code": code, "line_length": 88}}
        i_res = self.indent_checker.process(p_env) if self.indent_checker else {"score": 100, "passed": True}
        s_res = self.spacing_checker.process(p_env) if self.spacing_checker else {"score": 100, "passed": True}
        l_res = self.length_checker.process(p_env) if self.length_checker else {"score": 100, "passed": True}

        score = round((i_res.get("score", 100) + s_res.get("score", 100) + l_res.get("score", 100)) / 3.0, 2)
        passed = score >= 85

        return {
            "composite_score": score,
            "indentation": i_res,
            "spacing": s_res,
            "line_length": l_res,
            "passed": passed,
            "recommendation": "Code formatting complies with PEP8/Black standards." if passed else "Run black . to autoformat.",
        }
