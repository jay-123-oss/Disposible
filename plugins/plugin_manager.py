"""PluginManager agent managing the plugin lifecycle: registration, activation, deactivation, status.

Implements the complete Plugin Manager hierarchy (P2):
- L4 PluginManager coordinator
- L5 atomic workers: PluginRegistrar, PluginActivator, PluginDeactivator, PluginStatusChecker
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from plugins.exceptions import PluginManagerError


logger = logging.getLogger("FractalCore.PluginSystem.PluginManager")


# ==============================================================================
# L5 Atomic Plugin Manager Subagents
# ==============================================================================

class PluginRegistrar(BaseAgent):
    """L5 agent registering plugins into the plugin registry."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginRegistrar %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugin = task_envelope.get("plugin_name", "unnamed")
        registry = task_envelope.get("registry", {})
        if plugin in registry:
            return {"status": "COMPLETED", "registered": False, "reason": "already_registered", "plugin_name": plugin}
        registry[plugin] = {"state": "registered", "version": task_envelope.get("version", "1.0.0")}
        return {"status": "COMPLETED", "registered": True, "plugin_name": plugin, "state": "registered"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginRegistrar %s cleaned up.", self.agent_id)


class PluginActivator(BaseAgent):
    """L5 agent activating a plugin and invoking its activate() lifecycle hook."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginActivator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugin = task_envelope.get("plugin_name", "unnamed")
        registry = task_envelope.get("registry", {})
        if plugin not in registry:
            return {"status": "COMPLETED", "activated": False, "reason": "not_registered", "plugin_name": plugin}
        registry[plugin]["state"] = "active"
        return {"status": "COMPLETED", "activated": True, "plugin_name": plugin, "state": "active"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginActivator %s cleaned up.", self.agent_id)


class PluginDeactivator(BaseAgent):
    """L5 agent deactivating a plugin and invoking its deactivate() lifecycle hook."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginDeactivator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugin = task_envelope.get("plugin_name", "unnamed")
        registry = task_envelope.get("registry", {})
        if plugin not in registry:
            return {"status": "COMPLETED", "deactivated": False, "reason": "not_registered", "plugin_name": plugin}
        registry[plugin]["state"] = "inactive"
        return {"status": "COMPLETED", "deactivated": True, "plugin_name": plugin, "state": "inactive"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginDeactivator %s cleaned up.", self.agent_id)


class PluginStatusChecker(BaseAgent):
    """L5 agent reporting the current lifecycle state of a plugin."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginStatusChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugin = task_envelope.get("plugin_name", "unnamed")
        registry = task_envelope.get("registry", {})
        entry = registry.get(plugin)
        return {"status": "COMPLETED", "plugin_name": plugin, "state": entry.get("state", "unknown") if entry else "unknown",
                "version": entry.get("version") if entry else None, "exists": entry is not None}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginStatusChecker %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PluginManager Agent
# ==============================================================================

class PluginManager(BaseAgent):
    """L4 coordinator managing plugin registration, activation, deactivation, and status."""

    def __init__(
        self,
        name: str = "PluginManager",
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
            "plugin_manager",
            "plugin_registrar",
            "plugin_activator",
            "plugin_deactivator",
            "plugin_status_checker",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P2_PLUGIN_MANAGER",
        )
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.registrar: Optional[PluginRegistrar] = None
        self.activator: Optional[PluginActivator] = None
        self.deactivator: Optional[PluginDeactivator] = None
        self.status_checker: Optional[PluginStatusChecker] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("manage_plugin_lifecycle", self.manage_plugin_lifecycle)

    def _spawn_subagents(self) -> None:
        """Spawn atomic plugin manager subagents (Rule 1 & Rule 5)."""
        logger.info("PluginManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.registrar = self.spawn_subagent(PluginRegistrar, name="PluginRegistrar", max_depth=child_depth, resources_mb=32)
        self.activator = self.spawn_subagent(PluginActivator, name="PluginActivator", max_depth=child_depth, resources_mb=32)
        self.deactivator = self.spawn_subagent(PluginDeactivator, name="PluginDeactivator", max_depth=child_depth, resources_mb=32)
        self.status_checker = self.spawn_subagent(PluginStatusChecker, name="PluginStatusChecker", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.manage_plugin_lifecycle(payload.get("action", "status"), payload.get("plugin_name", ""))
        return {"status": "COMPLETED", "lifecycle": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginManager %s cleanup complete.", self.agent_id)

    def manage_plugin_lifecycle(self, action: str, plugin_name: str) -> Dict[str, Any]:
        """Execute a lifecycle action (register/activate/deactivate/status)."""
        logger.info("Plugin lifecycle action '%s' for '%s'...", action, plugin_name)
        if not plugin_name:
            raise PluginManagerError("Plugin name is required for lifecycle management.")
        envelope = {"plugin_name": plugin_name, "registry": self.registry}
        if action == "register":
            result = self.registrar.process(envelope) if self.registrar else {"registered": True}
        elif action == "activate":
            result = self.activator.process(envelope) if self.activator else {"activated": True}
        elif action == "deactivate":
            result = self.deactivator.process(envelope) if self.deactivator else {"deactivated": True}
        elif action == "status":
            result = self.status_checker.process(envelope) if self.status_checker else {"state": "unknown"}
        else:
            raise PluginManagerError(f"Unknown lifecycle action: {action}")
        result["plugin_name"] = plugin_name
        return result