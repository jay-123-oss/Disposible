"""DocumentationGenerator agent generating language-natural documentation (Sphinx, JSDoc, godoc, rustdoc, Javadoc).

Implements the complete Documentation Generator hierarchy (M14):
- L4 DocumentationGenerator coordinator
- L5 atomic workers: PythonDocGenerator, JsdocGenerator, GodocGenerator, RustdocGenerator, JavadocGenerator
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from multi_lang.exceptions import DocumentationGenerationError


logger = logging.getLogger("FractalCore.MultiLang.DocumentationGenerator")


# ==============================================================================
# L5 Atomic Documentation Generator Subagents
# ==============================================================================

class PythonDocGenerator(BaseAgent):
    """L5 agent generating Sphinx-compatible docstrings and rst."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PythonDocGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        module = task_envelope.get("module_name", "myservice")
        return {"status": "COMPLETED", "language": "python", "tool": "sphinx",
                "doc_content": f".. _module:\n\n{module}\n{'=' * len(module)}\n\nGenerated Sphinx documentation."}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PythonDocGenerator %s cleaned up.", self.agent_id)


class JsdocGenerator(BaseAgent):
    """L5 agent generating JSDoc comment blocks."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("JsdocGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        module = task_envelope.get("module_name", "myservice")
        return {"status": "COMPLETED", "language": "node", "tool": "jsdoc",
                "doc_content": f"/**\n * {module} module.\n * Generated JSDoc documentation.\n */"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("JsdocGenerator %s cleaned up.", self.agent_id)


class GodocGenerator(BaseAgent):
    """L5 agent generating godoc package comments."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("GodocGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        module = task_envelope.get("module_name", "myservice")
        return {"status": "COMPLETED", "language": "go", "tool": "godoc",
                "doc_content": f"// Package {module} provides the generated service.\npackage {module}"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("GodocGenerator %s cleaned up.", self.agent_id)


class RustdocGenerator(BaseAgent):
    """L5 agent generating rustdoc crate documentation."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RustdocGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        module = task_envelope.get("module_name", "myservice")
        return {"status": "COMPLETED", "language": "rust", "tool": "rustdoc",
                "doc_content": f"//! # {module}\n//!\n//! Generated rustdoc documentation."}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("RustdocGenerator %s cleaned up.", self.agent_id)


class JavadocGenerator(BaseAgent):
    """L5 agent generating Javadoc comments."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("JavadocGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        module = task_envelope.get("module_name", "MyService")
        return {"status": "COMPLETED", "language": "java", "tool": "javadoc",
                "doc_content": f"/**\n * {module} service.\n *\n * <p>Generated Javadoc documentation.</p>\n */"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("JavadocGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 DocumentationGenerator Agent
# ==============================================================================

class DocumentationGenerator(BaseAgent):
    """L4 coordinator generating documentation for every supported language toolchain."""

    def __init__(
        self,
        name: str = "DocumentationGenerator",
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
            "documentation_generator",
            "python_doc_generator",
            "jsdoc_generator",
            "godoc_generator",
            "rustdoc_generator",
            "javadoc_generator",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M14_DOCUMENTATION_GENERATOR",
        )
        self.python_doc: Optional[PythonDocGenerator] = None
        self.jsdoc: Optional[JsdocGenerator] = None
        self.godoc: Optional[GodocGenerator] = None
        self.rustdoc: Optional[RustdocGenerator] = None
        self.javadoc: Optional[JavadocGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_documentation", self.generate_documentation)

    def _spawn_subagents(self) -> None:
        """Spawn atomic documentation subagents (Rule 1 & Rule 5)."""
        logger.info("DocumentationGenerator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.python_doc = self.spawn_subagent(PythonDocGenerator, name="PythonDocGenerator", max_depth=child_depth, resources_mb=32)
        self.jsdoc = self.spawn_subagent(JsdocGenerator, name="JsdocGenerator", max_depth=child_depth, resources_mb=32)
        self.godoc = self.spawn_subagent(GodocGenerator, name="GodocGenerator", max_depth=child_depth, resources_mb=32)
        self.rustdoc = self.spawn_subagent(RustdocGenerator, name="RustdocGenerator", max_depth=child_depth, resources_mb=32)
        self.javadoc = self.spawn_subagent(JavadocGenerator, name="JavadocGenerator", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DocumentationGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.generate_documentation(payload.get("language", "python"), payload.get("module_name", "myservice"))
        return {"status": "COMPLETED", "documentation": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DocumentationGenerator %s cleanup complete.", self.agent_id)

    def generate_documentation(self, language: str, module_name: str) -> Dict[str, Any]:
        """Generate language-specific doc snippets for a module."""
        logger.info("Generating %s documentation...", language)
        generator_map = {
            "python": self.python_doc,
            "node": self.jsdoc,
            "go": self.godoc,
            "rust": self.rustdoc,
            "java": self.javadoc,
        }
        generator = generator_map.get(language.lower())
        if generator is None:
            raise DocumentationGenerationError(f"Unsupported language for documentation: {language}")
        result = generator.process({"module_name": module_name})
        result["module_name"] = module_name
        return result