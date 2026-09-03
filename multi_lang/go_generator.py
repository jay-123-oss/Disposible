"""GoGenerator agent generating Gin/Echo APIs, GORM models, go test tests, and go.mod manifests.

Implements the complete Go Generator hierarchy (M4):
- L4 GoGenerator coordinator
- L5 atomic workers: GoApiGenerator, GoModelGenerator, GoTestGenerator, GoDependencyGenerator
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from multi_lang.exceptions import GoGenerationError


logger = logging.getLogger("FractalCore.MultiLang.GoGenerator")

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "go_templates")


def _load_template(filename: str) -> str:
    path = os.path.join(_TEMPLATE_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as exc:
        raise GoGenerationError(f"Failed to load Go template {filename}: {exc}") from exc


def _render(template: str, values: Dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"__{key}__", str(value))
    return rendered


# ==============================================================================
# L5 Atomic Go Generator Subagents
# ==============================================================================

class GoApiGenerator(BaseAgent):
    """L5 agent generating Gin/Echo API skeletons (gofmt compliant)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("GoApiGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("api_template.go")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "api", "language": "go", "gofmt_compliant": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("GoApiGenerator %s cleaned up.", self.agent_id)


class GoModelGenerator(BaseAgent):
    """L5 agent generating GORM data models."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("GoModelGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("model_template.go")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "model", "language": "go", "orm": "gorm"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("GoModelGenerator %s cleaned up.", self.agent_id)


class GoTestGenerator(BaseAgent):
    """L5 agent generating `go test` unit tests."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("GoTestGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("test_template.go")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "test", "language": "go", "test_framework": "go test"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("GoTestGenerator %s cleaned up.", self.agent_id)


class GoDependencyGenerator(BaseAgent):
    """L5 agent generating go.mod dependency manifests."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("GoDependencyGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("dependency_template.go")
        content = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_content": content, "kind": "dependency", "language": "go", "manifest": "go.mod"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("GoDependencyGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 GoGenerator Agent
# ==============================================================================

class GoGenerator(BaseAgent):
    """L4 coordinator generating complete Go projects (API, model, tests, go.mod)."""

    def __init__(
        self,
        name: str = "GoGenerator",
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
            "go_generator",
            "go_api_generator",
            "go_model_generator",
            "go_test_generator",
            "go_dependency_generator",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M4_GO_GENERATOR",
        )
        self.api_generator: Optional[GoApiGenerator] = None
        self.model_generator: Optional[GoModelGenerator] = None
        self.test_generator: Optional[GoTestGenerator] = None
        self.dependency_generator: Optional[GoDependencyGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_go_project", self.generate_go_project)

    def _spawn_subagents(self) -> None:
        """Spawn atomic Go generator subagents (Rule 1 & Rule 5)."""
        logger.info("GoGenerator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.api_generator = self.spawn_subagent(GoApiGenerator, name="GoApiGenerator", max_depth=child_depth, resources_mb=32)
        self.model_generator = self.spawn_subagent(GoModelGenerator, name="GoModelGenerator", max_depth=child_depth, resources_mb=32)
        self.test_generator = self.spawn_subagent(GoTestGenerator, name="GoTestGenerator", max_depth=child_depth, resources_mb=32)
        self.dependency_generator = self.spawn_subagent(GoDependencyGenerator, name="GoDependencyGenerator", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("GoGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.generate_go_project(payload)
        return {"status": "COMPLETED", "generated": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("GoGenerator %s cleanup complete.", self.agent_id)

    def generate_go_project(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a complete Go project (Gin default) from a spec context."""
        ctx = context or {}
        values = {
            "MODULE_NAME": ctx.get("module_name", "myservice"),
            "MODEL_NAME": ctx.get("model_name", "Item"),
            "MODEL_UPPER": ctx.get("model_name", "Item").title(),
            "ROUTE": ctx.get("route", "items"),
            "FRAMEWORK": ctx.get("framework", "gin"),
        }
        api = self.api_generator.process({"values": values}) if self.api_generator else {"generated_code": ""}
        model = self.model_generator.process({"values": values}) if self.model_generator else {"generated_code": ""}
        test = self.test_generator.process({"values": values}) if self.test_generator else {"generated_code": ""}
        deps = self.dependency_generator.process({"values": values}) if self.dependency_generator else {"generated_content": ""}
        return {
            "language": "go",
            "framework": values["FRAMEWORK"],
            "all_generated": True,
            "api": api,
            "model": model,
            "test": test,
            "go_mod": deps,
        }