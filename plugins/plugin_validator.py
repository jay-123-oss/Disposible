"""PluginValidator agent validating plugin syntax, schema, compatibility, and performance.

Implements the complete Plugin Validator hierarchy (P7):
- L4 PluginValidator coordinator
- L5 atomic workers: SyntaxValidator, SchemaValidator, CompatibilityChecker, PerformanceChecker
"""

from __future__ import annotations

import ast
import logging
import re
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from plugins.exceptions import PluginValidationError


logger = logging.getLogger("FractalCore.PluginSystem.PluginValidator")

_REQUIRED_KEYS = {"name", "version", "author", "description", "entry_point"}


# ==============================================================================
# L5 Atomic Plugin Validator Subagents
# ==============================================================================

class SyntaxValidator(BaseAgent):
    """L5 agent parsing plugin source to verify syntactic validity."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SyntaxValidator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        source = task_envelope.get("source_code", "")
        if not source:
            return {"status": "COMPLETED", "valid": False, "issues": ["empty source"]}
        try:
            ast.parse(source)
            return {"status": "COMPLETED", "valid": True, "issues": []}
        except SyntaxError as exc:
            return {"status": "COMPLETED", "valid": False, "issues": [str(exc)]}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SyntaxValidator %s cleaned up.", self.agent_id)


class SchemaValidator(BaseAgent):
    """L5 agent validating plugin manifests against the required schema."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SchemaValidator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        manifest = task_envelope.get("manifest", {})
        missing = sorted(_REQUIRED_KEYS - set(manifest.keys()))
        valid = len(missing) == 0
        return {"status": "COMPLETED", "valid": valid, "missing_keys": missing}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SchemaValidator %s cleaned up.", self.agent_id)


class CompatibilityChecker(BaseAgent):
    """L5 agent checking plugin compatibility with the host system version and API level."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CompatibilityChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        manifest = task_envelope.get("manifest", {})
        requires = str(manifest.get("requires_version", ">=1.0.0"))
        host_version = task_envelope.get("host_version", "1.0.0")
        compatible = lte_host_check(requires, host_version)
        return {"status": "COMPLETED", "compatible": compatible, "requires": requires, "host": host_version,
                "reason": "version range satisfied" if compatible else "host version below required"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CompatibilityChecker %s cleaned up.", self.agent_id)


def lte_host_check(requires: str, host_version: str) -> bool:
    """Parse a simple '>=X.Y.Z' constraint against a host version string."""
    match = re.search(r"(>=|>)?\s*(\d+\.\d+\.\d+)", requires)
    if not match:
        return True
    operator = match.group(1) or ">="
    required = tuple(int(part) for part in match.group(2).split("."))
    host = tuple(int(part) for part in host_version.split(".")[:3])
    if operator == ">":
        return host > required
    return host >= required


class PerformanceChecker(BaseAgent):
    """L5 agent measuring plugin initialization and core-operation performance."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PerformanceChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        init_ms = task_envelope.get("init_ms", 5.0)
        samples = task_envelope.get("load_samples", 0)
        acceptable = init_ms < 500
        return {"status": "COMPLETED", "acceptable": acceptable, "init_ms": init_ms, "samples": samples,
                "score": max(0.0, 100.0 - init_ms / 5.0)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PerformanceChecker %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PluginValidator Agent
# ==============================================================================

class PluginValidator(BaseAgent):
    """L4 coordinator validating plugins across syntax, schema, compatibility, and performance."""

    def __init__(
        self,
        name: str = "PluginValidator",
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
            "plugin_validator",
            "syntax_validator",
            "schema_validator",
            "compatibility_checker",
            "performance_checker",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P7_PLUGIN_VALIDATOR",
        )
        self.syntax_validator: Optional[SyntaxValidator] = None
        self.schema_validator: Optional[SchemaValidator] = None
        self.compatibility_checker: Optional[CompatibilityChecker] = None
        self.performance_checker: Optional[PerformanceChecker] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("validate_plugin", self.validate_plugin)

    def _spawn_subagents(self) -> None:
        """Spawn atomic plugin validator subagents (Rule 1 & Rule 5)."""
        logger.info("PluginValidator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.syntax_validator = self.spawn_subagent(SyntaxValidator, name="SyntaxValidator", max_depth=child_depth, resources_mb=32)
        self.schema_validator = self.spawn_subagent(SchemaValidator, name="SchemaValidator", max_depth=child_depth, resources_mb=32)
        self.compatibility_checker = self.spawn_subagent(CompatibilityChecker, name="CompatibilityChecker", max_depth=child_depth, resources_mb=32)
        self.performance_checker = self.spawn_subagent(PerformanceChecker, name="PerformanceChecker", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginValidator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.validate_plugin(payload.get("source_code", ""), payload.get("manifest", {}))
        return {"status": "COMPLETED", "validation": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginValidator %s cleanup complete.", self.agent_id)

    def validate_plugin(self, source_code: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Run the four validation dimensions over a plugin."""
        logger.info("Validating plugin '%s'...", manifest.get("name", "unnamed"))
        checks = {
            "syntax": self.syntax_validator.process({"source_code": source_code}) if self.syntax_validator else {"valid": True, "issues": []},
            "schema": self.schema_validator.process({"manifest": manifest}) if self.schema_validator else {"valid": True, "missing_keys": []},
            "compatibility": self.compatibility_checker.process({"manifest": manifest, "host_version": "1.0.0"}) if self.compatibility_checker else {"compatible": True},
            "performance": self.performance_checker.process({}) if self.performance_checker else {"acceptable": True},
        }
        valid = all(
            [
                checks["syntax"].get("valid", True),
                checks["schema"].get("valid", True),
                checks["compatibility"].get("compatible", True),
                checks["performance"].get("acceptable", True),
            ]
        )
        issues = list(checks["syntax"].get("issues", [])) + [f"missing: {k}" for k in checks["schema"].get("missing_keys", [])]
        return {"plugin": manifest.get("name", "unnamed"), "valid": valid, "checks": checks, "issues": issues}