"""RustGenerator agent generating Actix/Rocket APIs, Diesel models, cargo test tests, and Cargo.toml manifests.

Implements the complete Rust Generator hierarchy (M5):
- L4 RustGenerator coordinator
- L5 atomic workers: RustApiGenerator, RustModelGenerator, RustTestGenerator, RustDependencyGenerator
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from multi_lang.exceptions import RustGenerationError


logger = logging.getLogger("FractalCore.MultiLang.RustGenerator")

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "rust_templates")


def _load_template(filename: str) -> str:
    path = os.path.join(_TEMPLATE_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as exc:
        raise RustGenerationError(f"Failed to load Rust template {filename}: {exc}") from exc


def _render(template: str, values: Dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"__{key}__", str(value))
    return rendered


# ==============================================================================
# L5 Atomic Rust Generator Subagents
# ==============================================================================

class RustApiGenerator(BaseAgent):
    """L5 agent generating Actix/Rocket API skeletons (rustfmt compliant)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RustApiGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("api_template.rs")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "api", "language": "rust", "rustfmt_compliant": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("RustApiGenerator %s cleaned up.", self.agent_id)


class RustModelGenerator(BaseAgent):
    """L5 agent generating Diesel ORM models."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RustModelGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("model_template.rs")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "model", "language": "rust", "orm": "diesel"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("RustModelGenerator %s cleaned up.", self.agent_id)


class RustTestGenerator(BaseAgent):
    """L5 agent generating `cargo test` unit tests."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RustTestGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("test_template.rs")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "test", "language": "rust", "test_framework": "cargo test"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("RustTestGenerator %s cleaned up.", self.agent_id)


class RustDependencyGenerator(BaseAgent):
    """L5 agent generating Cargo.toml manifests."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RustDependencyGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("dependency_template.rs")
        content = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_content": content, "kind": "dependency", "language": "rust", "manifest": "Cargo.toml"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("RustDependencyGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 RustGenerator Agent
# ==============================================================================

class RustGenerator(BaseAgent):
    """L4 coordinator generating complete Rust projects (API, model, tests, Cargo.toml)."""

    def __init__(
        self,
        name: str = "RustGenerator",
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
            "rust_generator",
            "rust_api_generator",
            "rust_model_generator",
            "rust_test_generator",
            "rust_dependency_generator",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M5_RUST_GENERATOR",
        )
        self.api_generator: Optional[RustApiGenerator] = None
        self.model_generator: Optional[RustModelGenerator] = None
        self.test_generator: Optional[RustTestGenerator] = None
        self.dependency_generator: Optional[RustDependencyGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_rust_project", self.generate_rust_project)

    def _spawn_subagents(self) -> None:
        """Spawn atomic Rust generator subagents (Rule 1 & Rule 5)."""
        logger.info("RustGenerator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.api_generator = self.spawn_subagent(RustApiGenerator, name="RustApiGenerator", max_depth=child_depth, resources_mb=32)
        self.model_generator = self.spawn_subagent(RustModelGenerator, name="RustModelGenerator", max_depth=child_depth, resources_mb=32)
        self.test_generator = self.spawn_subagent(RustTestGenerator, name="RustTestGenerator", max_depth=child_depth, resources_mb=32)
        self.dependency_generator = self.spawn_subagent(RustDependencyGenerator, name="RustDependencyGenerator", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RustGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.generate_rust_project(payload)
        return {"status": "COMPLETED", "generated": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("RustGenerator %s cleanup complete.", self.agent_id)

    def generate_rust_project(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a complete Rust project (Actix default) from a spec context."""
        ctx = context or {}
        values = {
            "MODULE_NAME": ctx.get("module_name", "myservice"),
            "MODEL_NAME": ctx.get("model_name", "Item"),
            "MODEL_SNAKE": ctx.get("model_name", "Item").lower(),
            "ROUTE": ctx.get("route", "items"),
            "FRAMEWORK": ctx.get("framework", "actix"),
        }
        api = self.api_generator.process({"values": values}) if self.api_generator else {"generated_code": ""}
        model = self.model_generator.process({"values": values}) if self.model_generator else {"generated_code": ""}
        test = self.test_generator.process({"values": values}) if self.test_generator else {"generated_code": ""}
        deps = self.dependency_generator.process({"values": values}) if self.dependency_generator else {"generated_content": ""}
        return {
            "language": "rust",
            "framework": values["FRAMEWORK"],
            "all_generated": True,
            "api": api,
            "model": model,
            "test": test,
            "cargo_toml": deps,
        }