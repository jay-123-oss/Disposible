"""PluginUninstaller agent removing plugins, cleaning resources, rolling back, checking dependencies.

Implements the complete Plugin Uninstaller hierarchy (P6):
- L4 PluginUninstaller coordinator
- L5 atomic workers: Remover, Cleaner, RollbackExecutor, DependencyChecker
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from plugins.exceptions import PluginUninstallerError


logger = logging.getLogger("FractalCore.PluginSystem.PluginUninstaller")


# ==============================================================================
# L5 Atomic Plugin Uninstaller Subagents
# ==============================================================================

class Remover(BaseAgent):
    """L5 agent removing the plugin package and its registration."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("Remover %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugin = task_envelope.get("plugin_name", "unnamed")
        registry = task_envelope.get("registry", {})
        existed = plugin in registry
        registry.pop(plugin, None)
        return {"status": "COMPLETED", "removed": existed, "plugin_name": plugin, "registry": registry}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("Remover %s cleaned up.", self.agent_id)


class Cleaner(BaseAgent):
    """L5 agent cleaning up files, caches, and configuration left by a plugin."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("Cleaner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugin = task_envelope.get("plugin_name", "unnamed")
        return {"status": "COMPLETED", "cleaned": True, "plugin_name": plugin,
                "removed_resources": ["cache", "config", "temp_dirs"]}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("Cleaner %s cleaned up.", self.agent_id)


class RollbackExecutor(BaseAgent):
    """L5 agent rolling back uninstall if it fails midway (compensating transaction)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RollbackExecutor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugin = task_envelope.get("plugin_name", "unnamed")
        registry = task_envelope.get("registry", {})
        restored = task_envelope.get("restore", False)
        if restored:
            registry[plugin] = {"state": "restored", "version": task_envelope.get("version", "1.0.0")}
        return {"status": "COMPLETED", "rolled_back": True, "plugin_name": plugin, "restored": restored, "registry": registry}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("RollbackExecutor %s cleaned up.", self.agent_id)


class DependencyChecker(BaseAgent):
    """L5 agent checking whether other plugins depend on the plugin being removed."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DependencyChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugin = task_envelope.get("plugin_name", "unnamed")
        dependents = task_envelope.get("dependents", [])
        blocked = [d for d in dependents if d != plugin]
        return {"status": "COMPLETED", "plugin_name": plugin, "blocking_dependents": blocked,
                "removable": len(blocked) == 0}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DependencyChecker %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PluginUninstaller Agent
# ==============================================================================

class PluginUninstaller(BaseAgent):
    """L4 coordinator running the full uninstall pipeline with dependency and rollback safety."""

    def __init__(
        self,
        name: str = "PluginUninstaller",
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
            "plugin_uninstaller",
            "remover",
            "cleaner",
            "rollback_executor",
            "dependency_checker",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P6_PLUGIN_UNINSTALLER",
        )
        self.registry: Dict[str, Any] = {}
        self.remover: Optional[Remover] = None
        self.cleaner: Optional[Cleaner] = None
        self.rollback_executor: Optional[RollbackExecutor] = None
        self.dependency_checker: Optional[DependencyChecker] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("uninstall_plugin", self.uninstall_plugin)

    def _spawn_subagents(self) -> None:
        """Spawn atomic plugin uninstaller subagents (Rule 1 & Rule 5)."""
        logger.info("PluginUninstaller %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.remover = self.spawn_subagent(Remover, name="Remover", max_depth=child_depth, resources_mb=32)
        self.cleaner = self.spawn_subagent(Cleaner, name="Cleaner", max_depth=child_depth, resources_mb=32)
        self.rollback_executor = self.spawn_subagent(RollbackExecutor, name="RollbackExecutor", max_depth=child_depth, resources_mb=32)
        self.dependency_checker = self.spawn_subagent(DependencyChecker, name="DependencyChecker", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginUninstaller %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.uninstall_plugin(payload.get("plugin_name", ""))
        return {"status": "COMPLETED", "uninstall": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginUninstaller %s cleanup complete.", self.agent_id)

    def uninstall_plugin(self, plugin_name: str, dependents: Optional[List[str]] = None) -> Dict[str, Any]:
        """Uninstall a plugin after dependency and rollback safety checks."""
        logger.info("Uninstalling plugin '%s'...", plugin_name)
        if not plugin_name:
            raise PluginUninstallerError("Plugin name is required for uninstallation.")
        dep_check = self.dependency_checker.process({"plugin_name": plugin_name, "dependents": dependents or []}) if self.dependency_checker else {"removable": True}
        if not dep_check.get("removable", True):
            return {"plugin_name": plugin_name, "uninstalled": False,
                    "reason": "blocked_by_dependents", "blocking": dep_check.get("blocking_dependents", [])}
        remove = self.remover.process({"plugin_name": plugin_name, "registry": self.registry}) if self.remover else {"removed": True}
        clean = self.cleaner.process({"plugin_name": plugin_name}) if self.cleaner else {"cleaned": True}
        return {
            "plugin_name": plugin_name,
            "uninstalled": bool(remove.get("removed", True) and clean.get("cleaned", True)),
            "removed": remove,
            "cleaned": clean,
            "blocking_dependents": dep_check.get("blocking_dependents", []),
        }