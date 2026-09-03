"""JavaGenerator agent generating Spring Boot APIs, JPA models, JUnit tests, and pom.xml manifests.

Implements the complete Java Generator hierarchy (M6):
- L4 JavaGenerator coordinator
- L5 atomic workers: JavaApiGenerator, JavaModelGenerator, JavaTestGenerator, JavaDependencyGenerator
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from multi_lang.exceptions import JavaGenerationError


logger = logging.getLogger("FractalCore.MultiLang.JavaGenerator")

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "java_templates")


def _load_template(filename: str) -> str:
    path = os.path.join(_TEMPLATE_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as exc:
        raise JavaGenerationError(f"Failed to load Java template {filename}: {exc}") from exc


def _render(template: str, values: Dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"__{key}__", str(value))
    return rendered


# ==============================================================================
# L5 Atomic Java Generator Subagents
# ==============================================================================

class JavaApiGenerator(BaseAgent):
    """L5 agent generating Spring Boot REST controller skeletons (Google Java Format compliant)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("JavaApiGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("api_template.java")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "api", "language": "java", "google_java_format": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("JavaApiGenerator %s cleaned up.", self.agent_id)


class JavaModelGenerator(BaseAgent):
    """L5 agent generating JPA entity models."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("JavaModelGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("model_template.java")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "model", "language": "java", "orm": "jpa"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("JavaModelGenerator %s cleaned up.", self.agent_id)


class JavaTestGenerator(BaseAgent):
    """L5 agent generating JUnit 5 unit tests."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("JavaTestGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("test_template.java")
        code = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_code": code, "kind": "test", "language": "java", "test_framework": "junit"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("JavaTestGenerator %s cleaned up.", self.agent_id)


class JavaDependencyGenerator(BaseAgent):
    """L5 agent generating pom.xml Maven manifests."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("JavaDependencyGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        template = _load_template("dependency_template.java")
        content = _render(template, task_envelope.get("values", {}))
        return {"status": "COMPLETED", "generated_content": content, "kind": "dependency", "language": "java", "manifest": "pom.xml"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("JavaDependencyGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 JavaGenerator Agent
# ==============================================================================

class JavaGenerator(BaseAgent):
    """L4 coordinator generating complete Java projects (API, model, tests, pom.xml)."""

    def __init__(
        self,
        name: str = "JavaGenerator",
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
            "java_generator",
            "java_api_generator",
            "java_model_generator",
            "java_test_generator",
            "java_dependency_generator",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M6_JAVA_GENERATOR",
        )
        self.api_generator: Optional[JavaApiGenerator] = None
        self.model_generator: Optional[JavaModelGenerator] = None
        self.test_generator: Optional[JavaTestGenerator] = None
        self.dependency_generator: Optional[JavaDependencyGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_java_project", self.generate_java_project)

    def _spawn_subagents(self) -> None:
        """Spawn atomic Java generator subagents (Rule 1 & Rule 5)."""
        logger.info("JavaGenerator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.api_generator = self.spawn_subagent(JavaApiGenerator, name="JavaApiGenerator", max_depth=child_depth, resources_mb=32)
        self.model_generator = self.spawn_subagent(JavaModelGenerator, name="JavaModelGenerator", max_depth=child_depth, resources_mb=32)
        self.test_generator = self.spawn_subagent(JavaTestGenerator, name="JavaTestGenerator", max_depth=child_depth, resources_mb=32)
        self.dependency_generator = self.spawn_subagent(JavaDependencyGenerator, name="JavaDependencyGenerator", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("JavaGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.generate_java_project(payload)
        return {"status": "COMPLETED", "generated": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("JavaGenerator %s cleanup complete.", self.agent_id)

    def generate_java_project(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a complete Java project (Spring Boot default) from a spec context."""
        ctx = context or {}
        values = {
            "PACKAGE_NAME": ctx.get("package_name", "com.example.service"),
            "CLASS_NAME": ctx.get("model_name", "Item"),
            "MODEL_NAME": ctx.get("model_name", "Item"),
            "ROUTE": ctx.get("route", "items"),
            "FRAMEWORK": ctx.get("framework", "spring-boot"),
        }
        api = self.api_generator.process({"values": values}) if self.api_generator else {"generated_code": ""}
        model = self.model_generator.process({"values": values}) if self.model_generator else {"generated_code": ""}
        test = self.test_generator.process({"values": values}) if self.test_generator else {"generated_code": ""}
        deps = self.dependency_generator.process({"values": values}) if self.dependency_generator else {"generated_content": ""}
        return {
            "language": "java",
            "framework": values["FRAMEWORK"],
            "all_generated": True,
            "api": api,
            "model": model,
            "test": test,
            "pom_xml": deps,
        }