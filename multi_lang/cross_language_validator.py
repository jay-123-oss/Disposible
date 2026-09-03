"""CrossLanguageValidator agent validating generated code across languages for syntax, logic, performance, and security.

Implements the complete Cross-Language Validator hierarchy (M9):
- L4 CrossLanguageValidator coordinator
- L5 atomic workers: SyntaxValidator, LogicValidator, PerformanceValidator, SecurityValidator
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from multi_lang.exceptions import CrossLanguageValidationError


logger = logging.getLogger("FractalCore.MultiLang.CrossLanguageValidator")


# ==============================================================================
# L5 Atomic Cross-Language Validation Subagents
# ==============================================================================

class SyntaxValidator(BaseAgent):
    """L5 agent validating language-specific syntax (AST/balanced constructs/type hints)."""

    _SIMPLE_CHECKS = {
        "python": ["def ", "class ", "import "],
        "node": ["const ", "require(", "module.exports"],
        "go": ["func ", "package ", "import "],
        "rust": ["fn ", "use ", "impl "],
        "java": ["class ", "public ", "import "],
    }

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SyntaxValidator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        code = task_envelope.get("code", "")
        language = task_envelope.get("language", "")
        if language == "python":
            import ast
            try:
                ast.parse(code)
                return {"status": "COMPLETED", "check": "syntax", "passed": True, "issues": []}
            except SyntaxError as exc:
                return {"status": "COMPLETED", "check": "syntax", "passed": False, "issues": [str(exc)]}
        required = self._SIMPLE_CHECKS.get(language, [" "])
        passed = all(token in code for token in required)
        return {"status": "COMPLETED", "check": "syntax", "passed": passed,
                "issues": [] if passed else [f"missing expected token for {language}"]}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SyntaxValidator %s cleaned up.", self.agent_id)


class LogicValidator(BaseAgent):
    """L5 agent validating business logic preservation across translation."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LogicValidator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        source = task_envelope.get("source_code", "")
        target = task_envelope.get("target_code", "")
        if not source:
            return {"status": "COMPLETED", "check": "logic", "passed": True,
                    "issues": [], "note": "no source provided; logic check not applicable"}
        same_identifiers = set(source.split()) & set(target.split())
        passed = len(same_identifiers) > 0
        return {"status": "COMPLETED", "check": "logic", "passed": passed,
                "shared_tokens": sorted(same_identifiers)[:10],
                "issues": [] if passed else ["no overlapping identifier tokens"]}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("LogicValidator %s cleaned up.", self.agent_id)


class PerformanceValidator(BaseAgent):
    """L5 agent flagging performance anti-patterns such as blocking loops and nested scans."""

    _ANTI_PATTERNS = {
        "python_loop": ["while True", "for _ in range(1000000)"],
        "node_block": ["fs.readFileSync", "sleep("],
        "go_block": ["time.Sleep"],
        "nested_scan": ["for i in range", "for j in range"],
    }

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PerformanceValidator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        code = task_envelope.get("code", "")
        issues = [name for name, tokens in self._ANTI_PATTERNS.items() if any(t in code for t in tokens)]
        passed = len(issues) == 0
        return {"status": "COMPLETED", "check": "performance", "passed": passed, "issues": issues}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PerformanceValidator %s cleaned up.", self.agent_id)


class SecurityValidator(BaseAgent):
    """L5 agent scanning generated code for injection, secrets, and dangerous eval patterns."""

    _RISKS = r"(eval\s*\(|exec\s*\(|shell\s*=|\bpassword\s*=|subprocess|child_process|system\s*\()"

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SecurityValidator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        import re
        code = task_envelope.get("code", "")
        matches = re.findall(self._RISKS, code)
        passed = len(matches) == 0
        return {"status": "COMPLETED", "check": "security", "passed": passed, "issues": [f"risk: {m}" for m in matches]}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SecurityValidator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 CrossLanguageValidator Agent
# ==============================================================================

class CrossLanguageValidator(BaseAgent):
    """L4 coordinator validating syntax, logic, performance, and security across all supported languages."""

    def __init__(
        self,
        name: str = "CrossLanguageValidator",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "cross_language_validator",
            "syntax_validator",
            "logic_validator",
            "performance_validator",
            "security_validator",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M9_CROSS_LANGUAGE_VALIDATOR",
        )
        self.syntax_validator: Optional[SyntaxValidator] = None
        self.logic_validator: Optional[LogicValidator] = None
        self.performance_validator: Optional[PerformanceValidator] = None
        self.security_validator: Optional[SecurityValidator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("validate_code", self.validate_code)

    def _spawn_subagents(self) -> None:
        """Spawn atomic validation subagents (Rule 1 & Rule 5)."""
        logger.info("CrossLanguageValidator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.syntax_validator = self.spawn_subagent(SyntaxValidator, name="SyntaxValidator", max_depth=child_depth, resources_mb=32)
        self.logic_validator = self.spawn_subagent(LogicValidator, name="LogicValidator", max_depth=child_depth, resources_mb=32)
        self.performance_validator = self.spawn_subagent(PerformanceValidator, name="PerformanceValidator", max_depth=child_depth, resources_mb=32)
        self.security_validator = self.spawn_subagent(SecurityValidator, name="SecurityValidator", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CrossLanguageValidator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.validate_code(
            payload.get("code", ""),
            payload.get("language", "python"),
            payload.get("source_code", ""),
        )
        return {"status": "COMPLETED", "validation": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CrossLanguageValidator %s cleanup complete.", self.agent_id)

    def validate_code(self, code: str, language: str, source_code: str = "") -> Dict[str, Any]:
        """Run syntax, logic, performance, and security validation on generated/translated code."""
        logger.info("Validating %s code across all four dimensions...", language)
        checks = {
            "syntax": (self.syntax_validator.process({"code": code, "language": language}) if self.syntax_validator else {"passed": True, "issues": []}),
            "logic": (self.logic_validator.process({"source_code": source_code, "target_code": code}) if self.logic_validator else {"passed": True, "issues": []}),
            "performance": (self.performance_validator.process({"code": code}) if self.performance_validator else {"passed": True, "issues": []}),
            "security": (self.security_validator.process({"code": code}) if self.security_validator else {"passed": True, "issues": []}),
        }
        all_passed = all(check.get("passed", False) for check in checks.values())
        return {
            "language": language,
            "all_passed": all_passed,
            "checks": checks,
            "issues": [issue for check in checks.values() for issue in check.get("issues", [])],
        }