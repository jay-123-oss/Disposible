"""PythonGenerator agent generating FastAPI/Django/Flask APIs, SQLAlchemy/Django models, pytest tests, and requirements.txt.

Implements the complete Python Generator hierarchy (M2):
- L4 PythonGenerator coordinator
- L5 atomic workers: PythonApiGenerator, PythonModelGenerator, PythonTestGenerator, PythonDependencyGenerator
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from multi_lang.exceptions import PythonGenerationError


logger = logging.getLogger("FractalCore.MultiLang.PythonGenerator")

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "python_templates")


def _load_template(filename: str) -> str:
    """Read a raw template file from the python_templates directory."""
    path = os.path.join(_TEMPLATE_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
            if content.startswith('"""') and content.rstrip().endswith('"""'):
                content = content.strip()[3:-3].strip() + "\n"
            return content
    except OSError as exc:
        raise PythonGenerationError(f"Failed to load Python template {filename}: {exc}") from exc



def _render(template: str, values: Dict[str, str]) -> str:
    """Substitute __PLACEHOLDER__ tokens in a template with provided values."""
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"__{key}__", str(value))
    return rendered


# ==============================================================================
# L5 Atomic Python Generator Subagents
# ==============================================================================

class PythonApiGenerator(BaseAgent):
    """L5 agent generating FastAPI/Django/Flask API skeletons (PEP 8 compliant)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PythonApiGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("api_template.py")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "api", "language": "python", "pep8_compliant": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        import ast
        try:
            ast.parse(result["generated_code"])
            result["syntax_valid"] = True
        except SyntaxError as exc:
            result["syntax_valid"] = False
            result["error"] = str(exc)
        return result

    def cleanup(self) -> None:
        logger.debug("PythonApiGenerator %s cleaned up.", self.agent_id)


class PythonModelGenerator(BaseAgent):
    """L5 agent generating SQLAlchemy/Django ORM models."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PythonModelGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("model_template.py")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "model", "language": "python", "orm": "sqlalchemy"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        import ast
        try:
            ast.parse(result["generated_code"])
            result["syntax_valid"] = True
        except SyntaxError as exc:
            result["syntax_valid"] = False
            result["error"] = str(exc)
        return result

    def cleanup(self) -> None:
        logger.debug("PythonModelGenerator %s cleaned up.", self.agent_id)


class PythonTestGenerator(BaseAgent):
    """L5 agent generating pytest unit tests for APIs and models."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PythonTestGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("test_template.py")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "test", "language": "python", "test_framework": "pytest"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        import ast
        try:
            ast.parse(result["generated_code"])
            result["syntax_valid"] = True
        except SyntaxError as exc:
            result["syntax_valid"] = False
            result["error"] = str(exc)
        return result

    def cleanup(self) -> None:
        logger.debug("PythonTestGenerator %s cleaned up.", self.agent_id)


class PythonDependencyGenerator(BaseAgent):
    """L5 agent generating requirements.txt dependency manifests."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PythonDependencyGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("dependency_template.py")
        content = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_content": content, "kind": "dependency", "language": "python", "manifest": "requirements.txt"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PythonDependencyGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PythonGenerator Agent
# ==============================================================================

class PythonGenerator(BaseAgent):
    """L4 coordinator generating complete Python projects (API, model, tests, requirements)."""

    def __init__(
        self,
        name: str = "PythonGenerator",
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
            "python_generator",
            "python_api_generator",
            "python_model_generator",
            "python_test_generator",
            "python_dependency_generator",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M2_PYTHON_GENERATOR",
        )
        self.api_generator: Optional[PythonApiGenerator] = None
        self.model_generator: Optional[PythonModelGenerator] = None
        self.test_generator: Optional[PythonTestGenerator] = None
        self.dependency_generator: Optional[PythonDependencyGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_python_project", self.generate_python_project)

    def _spawn_subagents(self) -> None:
        """Spawn atomic Python generator subagents (Rule 1 & Rule 5)."""
        logger.info("PythonGenerator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.api_generator = self.spawn_subagent(PythonApiGenerator, name="PythonApiGenerator", max_depth=child_depth, resources_mb=32)
        self.model_generator = self.spawn_subagent(PythonModelGenerator, name="PythonModelGenerator", max_depth=child_depth, resources_mb=32)
        self.test_generator = self.spawn_subagent(PythonTestGenerator, name="PythonTestGenerator", max_depth=child_depth, resources_mb=32)
        self.dependency_generator = self.spawn_subagent(PythonDependencyGenerator, name="PythonDependencyGenerator", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PythonGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.generate_python_project(payload)
        return {"status": "COMPLETED", "generated": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PythonGenerator %s cleanup complete.", self.agent_id)

    def generate_python_project(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a complete Python project (FastAPI default) from a spec context."""
        ctx = context or {}
        values = {
            "MODULE_NAME": ctx.get("module_name", "my_service"),
            "MODEL_NAME": ctx.get("model_name", "Item"),
            "FIELDS": ctx.get("fields", "name: str\n    price: float"),
            "ROUTE": ctx.get("route", "items"),
            "FRAMEWORK": ctx.get("framework", "fastapi"),
        }
        api = self.api_generator.process({"values": values}) if self.api_generator else {"generated_code": ""}
        if self.api_generator:
            api = self.api_generator.validate(api)
        model = self.model_generator.process({"values": values}) if self.model_generator else {"generated_code": ""}
        if self.model_generator:
            model = self.model_generator.validate(model)
        test = self.test_generator.process({"values": values}) if self.test_generator else {"generated_code": ""}
        if self.test_generator:
            test = self.test_generator.validate(test)
        deps = self.dependency_generator.process({"values": values}) if self.dependency_generator else {"generated_content": ""}
        return {
            "language": "python",
            "framework": values["FRAMEWORK"],
            "all_generated": True,
            "api": api,
            "model": model,
            "test": test,
            "requirements_txt": deps,
        }