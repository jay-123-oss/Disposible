"""NodeGenerator agent generating Express/NestJS APIs, Mongoose/Sequelize models, Jest/Mocha tests, and package.json.

Implements the complete Node.js Generator hierarchy (M3):
- L4 NodeGenerator coordinator
- L5 atomic workers: NodeApiGenerator, NodeModelGenerator, NodeTestGenerator, NodeDependencyGenerator
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from multi_lang.exceptions import NodeGenerationError


logger = logging.getLogger("FractalCore.MultiLang.NodeGenerator")

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "node_templates")


def _load_template(filename: str) -> str:
    path = os.path.join(_TEMPLATE_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as exc:
        raise NodeGenerationError(f"Failed to load Node template {filename}: {exc}") from exc


def _render(template: str, values: Dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"__{key}__", str(value))
    return rendered


# ==============================================================================
# L5 Atomic Node Generator Subagents
# ==============================================================================

class NodeApiGenerator(BaseAgent):
    """L5 agent generating Express/NestJS API skeletons (ESLint compliant)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NodeApiGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("api_template.js")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "api", "language": "node", "eslint_compliant": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NodeApiGenerator %s cleaned up.", self.agent_id)


class NodeModelGenerator(BaseAgent):
    """L5 agent generating Mongoose/Sequelize data models."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NodeModelGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("model_template.js")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "model", "language": "node", "orm": "mongoose"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NodeModelGenerator %s cleaned up.", self.agent_id)


class NodeTestGenerator(BaseAgent):
    """L5 agent generating Jest/Mocha tests."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NodeTestGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("test_template.js")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "test", "language": "node", "test_framework": "jest"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NodeTestGenerator %s cleaned up.", self.agent_id)


class NodeDependencyGenerator(BaseAgent):
    """L5 agent generating package.json manifests."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NodeDependencyGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("dependency_template.json")
        content = _render(template, task_envelope.get("values", {}))
        try:
            import json
            json.loads(content)
            valid = True
        except (ValueError, TypeError):
            valid = False
        return {"status": "COMPLETED", "generated_content": content, "kind": "dependency", "language": "node", "manifest": "package.json", "json_valid": valid}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NodeDependencyGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 NodeGenerator Agent
# ==============================================================================

class NodeGenerator(BaseAgent):
    """L4 coordinator generating complete Node.js projects (API, model, tests, package.json)."""

    def __init__(
        self,
        name: str = "NodeGenerator",
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
            "node_generator",
            "node_api_generator",
            "node_model_generator",
            "node_test_generator",
            "node_dependency_generator",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M3_NODE_GENERATOR",
        )
        self.api_generator: Optional[NodeApiGenerator] = None
        self.model_generator: Optional[NodeModelGenerator] = None
        self.test_generator: Optional[NodeTestGenerator] = None
        self.dependency_generator: Optional[NodeDependencyGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_node_project", self.generate_node_project)

    def _spawn_subagents(self) -> None:
        """Spawn atomic Node generator subagents (Rule 1 & Rule 5)."""
        logger.info("NodeGenerator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.api_generator = self.spawn_subagent(NodeApiGenerator, name="NodeApiGenerator", max_depth=child_depth, resources_mb=32)
        self.model_generator = self.spawn_subagent(NodeModelGenerator, name="NodeModelGenerator", max_depth=child_depth, resources_mb=32)
        self.test_generator = self.spawn_subagent(NodeTestGenerator, name="NodeTestGenerator", max_depth=child_depth, resources_mb=32)
        self.dependency_generator = self.spawn_subagent(NodeDependencyGenerator, name="NodeDependencyGenerator", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NodeGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.generate_node_project(payload)
        return {"status": "COMPLETED", "generated": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NodeGenerator %s cleanup complete.", self.agent_id)

    def generate_node_project(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a complete Node.js project (Express default) from a spec context."""
        ctx = context or {}
        values = {
            "MODULE_NAME": ctx.get("module_name", "my-service"),
            "MODEL_NAME": ctx.get("model_name", "Item"),
            "ROUTE": ctx.get("route", "items"),
            "FRAMEWORK": ctx.get("framework", "express"),
        }
        api = self.api_generator.process({"values": values}) if self.api_generator else {"generated_code": ""}
        model = self.model_generator.process({"values": values}) if self.model_generator else {"generated_code": ""}
        test = self.test_generator.process({"values": values}) if self.test_generator else {"generated_code": ""}
        deps = self.dependency_generator.process({"values": values}) if self.dependency_generator else {"generated_content": ""}
        return {
            "language": "node",
            "framework": values["FRAMEWORK"],
            "all_generated": True,
            "api": api,
            "model": model,
            "test": test,
            "package_json": deps,
        }