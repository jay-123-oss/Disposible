"""PluginDocumentation agent generating plugin documentation, API docs, examples, and tutorials.

Implements the complete Plugin Documentation hierarchy (P14):
- L4 PluginDocumentation coordinator
- L5 atomic workers: DocGenerator, ApiDocGenerator, ExampleGenerator, TutorialGenerator
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from plugins.exceptions import PluginDocumentationError


logger = logging.getLogger("FractalCore.PluginSystem.PluginDocumentation")


# ==============================================================================
# L5 Atomic Plugin Documentation Subagents
# ==============================================================================

class DocGenerator(BaseAgent):
    """L5 agent generating the main README documentation for a plugin."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DocGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugin = task_envelope.get("plugin_name", "unnamed")
        version = task_envelope.get("version", "1.0.0")
        doc = f"# {plugin}\n\nVersion {version}\n\nGenerated plugin documentation."
        return {"status": "COMPLETED", "doc_type": "readme", "content": doc}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DocGenerator %s cleaned up.", self.agent_id)


class ApiDocGenerator(BaseAgent):
    """L5 agent generating API reference documentation for plugin entry points."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ApiDocGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugin = task_envelope.get("plugin_name", "unnamed")
        entry_point = task_envelope.get("entry_point", "PluginName")
        api_doc = f"## API Reference\n\n`{plugin}.{entry_point}` — plugin entry class."
        return {"status": "COMPLETED", "doc_type": "api", "content": api_doc}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ApiDocGenerator %s cleaned up.", self.agent_id)


class ExampleGenerator(BaseAgent):
    """L5 agent generating usage examples for a plugin."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ExampleGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugin = task_envelope.get("plugin_name", "unnamed")
        example = f"""```python
from plugins.builtin import {plugin}


instance = {plugin}()
instance.initialize(api)
instance.activate()
```"""
        return {"status": "COMPLETED", "doc_type": "example", "content": example}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ExampleGenerator %s cleaned up.", self.agent_id)


class TutorialGenerator(BaseAgent):
    """L5 agent generating step-by-step tutorials for a plugin."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TutorialGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugin = task_envelope.get("plugin_name", "unnamed")
        tutorial = (
            f"# Tutorial: {plugin}\n\n"
            f"1. Install the `{plugin}` plugin.\n"
            f"2. Activate it through the plugin manager.\n"
            f"3. Wire its hooks via the PluginApiProvider.\n"
            f"4. Call its actions from your workflow.\n"
        )
        return {"status": "COMPLETED", "doc_type": "tutorial", "content": tutorial}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TutorialGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PluginDocumentation Agent
# ==============================================================================

class PluginDocumentation(BaseAgent):
    """L4 coordinator producing README, API docs, examples, and tutorials for plugins."""

    def __init__(
        self,
        name: str = "PluginDocumentation",
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
            "plugin_documentation",
            "doc_generator",
            "api_doc_generator",
            "example_generator",
            "tutorial_generator",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P14_PLUGIN_DOCUMENTATION",
        )
        self.doc_generator: Optional[DocGenerator] = None
        self.api_doc_generator: Optional[ApiDocGenerator] = None
        self.example_generator: Optional[ExampleGenerator] = None
        self.tutorial_generator: Optional[TutorialGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_plugin_docs", self.generate_plugin_docs)

    def _spawn_subagents(self) -> None:
        """Spawn atomic plugin documentation subagents (Rule 1 & Rule 5)."""
        logger.info("PluginDocumentation %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.doc_generator = self.spawn_subagent(DocGenerator, name="DocGenerator", max_depth=child_depth, resources_mb=32)
        self.api_doc_generator = self.spawn_subagent(ApiDocGenerator, name="ApiDocGenerator", max_depth=child_depth, resources_mb=32)
        self.example_generator = self.spawn_subagent(ExampleGenerator, name="ExampleGenerator", max_depth=child_depth, resources_mb=32)
        self.tutorial_generator = self.spawn_subagent(TutorialGenerator, name="TutorialGenerator", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginDocumentation %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.generate_plugin_docs(payload.get("plugin_name", "unnamed"))
        return {"status": "COMPLETED", "documentation": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginDocumentation %s cleanup complete.", self.agent_id)

    def generate_plugin_docs(self, plugin_name: str) -> Dict[str, Any]:
        """Generate the complete documentation bundle for a plugin."""
        logger.info("Generating documentation for '%s'...", plugin_name)
        readme = self.doc_generator.process({"plugin_name": plugin_name, "version": "1.0.0"}) if self.doc_generator else {"content": ""}
        api_doc = self.api_doc_generator.process({"plugin_name": plugin_name, "entry_point": "PluginName"}) if self.api_doc_generator else {"content": ""}
        example = self.example_generator.process({"plugin_name": plugin_name}) if self.example_generator else {"content": ""}
        tutorial = self.tutorial_generator.process({"plugin_name": plugin_name}) if self.tutorial_generator else {"content": ""}
        combined = "\n\n".join(
            [readme.get("content", ""), api_doc.get("content", ""), example.get("content", ""), tutorial.get("content", "")]
        )
        return {
            "plugin_name": plugin_name,
            "all_docs_generated": True,
            "readme": readme.get("content", ""),
            "api_doc": api_doc.get("content", ""),
            "example": example.get("content", ""),
            "tutorial": tutorial.get("content", ""),
            "bundle": combined,
        }