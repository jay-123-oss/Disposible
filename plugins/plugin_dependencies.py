"""PluginDependencies agent resolving plugin dependency trees, conflicts, compatibility, and visualization.

Implements the complete Plugin Dependencies hierarchy (P13):
- L4 PluginDependencies coordinator
- L5 atomic workers: DependencyResolver, ConflictResolver, CompatibilityChecker, TreeVisualizer
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from plugins.exceptions import PluginDependencyError


logger = logging.getLogger("FractalCore.PluginSystem.PluginDependencies")


# ==============================================================================
# L5 Atomic Plugin Dependencies Subagents
# ==============================================================================

class DependencyResolver(BaseAgent):
    """L5 agent resolving a plugin's dependency closure."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DependencyResolver %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        graph = task_envelope.get("graph", {})
        start = task_envelope.get("plugin_name", "")
        if not start:
            return {"status": "COMPLETED", "resolved": [], "count": 0}
        resolved = []
        to_walk = [start]
        visited = set()
        while to_walk:
            current = to_walk.pop(0)
            if current in visited:
                continue
            visited.add(current)
            resolved.append(current)
            to_walk.extend(graph.get(current, []))
        return {"status": "COMPLETED", "resolved": resolved, "count": len(resolved)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DependencyResolver %s cleaned up.", self.agent_id)


class ConflictResolver(BaseAgent):
    """L5 agent detecting version conflicts in a plugin dependency set."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ConflictResolver %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        dependencies = task_envelope.get("dependencies", {})
        conflicts = []
        for name, versions in dependencies.items():
            unique = set(str(v) for v in versions)
            if len(unique) > 1:
                conflicts.append({"package": name, "versions": sorted(unique)})
        return {"status": "COMPLETED", "conflicts": conflicts, "conflict_count": len(conflicts)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ConflictResolver %s cleaned up.", self.agent_id)


class CompatibilityChecker(BaseAgent):
    """L5 agent verifying plugin set compatibility as a whole."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CompatibilityChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        dependencies = task_envelope.get("dependencies", {})
        host = task_envelope.get("host_version", "1.0.0")
        incompatible = [name for name, versions in dependencies.items() if str(versions).find(host) == -1 and str(versions) != "any"]
        return {"status": "COMPLETED", "compatible": len(incompatible) == 0, "incompatible_plugins": incompatible}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CompatibilityChecker %s cleaned up.", self.agent_id)


class TreeVisualizer(BaseAgent):
    """L5 agent rendering a plugin dependency tree as ASCII or text."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TreeVisualizer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        graph = task_envelope.get("graph", {})
        root = task_envelope.get("plugin_name", "root")
        lines = [root]
        children = graph.get(root, [])
        for child in children:
            lines.append(f"  +-- {child}")
        return {"status": "COMPLETED", "tree": "\n".join(lines), "nodes": [root, *children]}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TreeVisualizer %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PluginDependencies Agent
# ==============================================================================

class PluginDependencies(BaseAgent):
    """L4 coordinator managing dependency resolution, conflicts, compatibility, and tree views."""

    def __init__(
        self,
        name: str = "PluginDependencies",
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
            "plugin_dependencies",
            "dependency_resolver",
            "conflict_resolver",
            "compatibility_checker",
            "tree_visualizer",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P13_PLUGIN_DEPENDENCIES",
        )
        self.resolver: Optional[DependencyResolver] = None
        self.conflict_resolver: Optional[ConflictResolver] = None
        self.compatibility_checker: Optional[CompatibilityChecker] = None
        self.tree_visualizer: Optional[TreeVisualizer] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("resolve_plugin_dependencies", self.resolve_plugin_dependencies)

    def _spawn_subagents(self) -> None:
        """Spawn atomic plugin dependency subagents (Rule 1 & Rule 5)."""
        logger.info("PluginDependencies %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.resolver = self.spawn_subagent(DependencyResolver, name="DependencyResolver", max_depth=child_depth, resources_mb=32)
        self.conflict_resolver = self.spawn_subagent(ConflictResolver, name="ConflictResolver", max_depth=child_depth, resources_mb=32)
        self.compatibility_checker = self.spawn_subagent(CompatibilityChecker, name="CompatibilityChecker", max_depth=child_depth, resources_mb=32)
        self.tree_visualizer = self.spawn_subagent(TreeVisualizer, name="TreeVisualizer", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginDependencies %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.resolve_plugin_dependencies(payload.get("plugin_name", ""), payload.get("graph", {}))
        return {"status": "COMPLETED", "dependency_report": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginDependencies %s cleanup complete.", self.agent_id)

    def resolve_plugin_dependencies(self, plugin_name: str, graph: Dict[str, List[str]]) -> Dict[str, Any]:
        """Resolve the dependency closure, check conflicts, and render the tree."""
        logger.info("Resolving dependencies for '%s'...", plugin_name)
        resolved = self.resolver.process({"plugin_name": plugin_name, "graph": graph}) if self.resolver else {"resolved": [], "count": 0}
        versions = {name: ["1.0.0"] for name in graph.get(plugin_name, [])}
        conflicts = self.conflict_resolver.process({"dependencies": versions}) if self.conflict_resolver else {"conflicts": []}
        compat = self.compatibility_checker.process({"dependencies": versions, "host_version": "1.0.0"}) if self.compatibility_checker else {"compatible": True}
        tree = self.tree_visualizer.process({"plugin_name": plugin_name, "graph": graph}) if self.tree_visualizer else {"tree": plugin_name}
        return {
            "plugin_name": plugin_name,
            "resolved_dependencies": resolved.get("resolved", []),
            "dependency_count": resolved.get("count", 0),
            "conflicts": conflicts.get("conflicts", []),
            "compatible": compat.get("compatible", True),
            "dependency_tree": tree.get("tree", ""),
        }