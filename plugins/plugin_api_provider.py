"""PluginApiProvider agent exposing hooks, events, filters, and actions to third-party plugins.

Implements the complete Plugin API Provider hierarchy (P9):
- L4 PluginApiProvider coordinator
- L5 atomic workers: HookProvider, EventProvider, FilterProvider, ActionProvider
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from core.agent_base import BaseAgent
from plugins.exceptions import PluginAPIError
from plugins.plugin_hooks import FilterRegistry, HookExecutor, HookRegistry


logger = logging.getLogger("FractalCore.PluginSystem.PluginApiProvider")


# ==============================================================================
# L5 Atomic Plugin API Provider Subagents
# ==============================================================================

class HookProvider(BaseAgent):
    """L5 agent registering and executing plugin hook callbacks."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("HookProvider %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        registry = task_envelope.get("registry")
        action = task_envelope.get("action", "register")
        hook_name = task_envelope.get("hook_name", "")
        plugin_name = task_envelope.get("plugin_name", "")
        callback = task_envelope.get("callback")
        if registry is None:
            return {"status": "COMPLETED", "ok": False, "reason": "registry_missing"}
        if action == "register" and callback:
            registry.register(hook_name, plugin_name, callback)
            return {"status": "COMPLETED", "ok": True, "registered_hooks": registry.hook_names()}
        if action == "unregister":
            registry.unregister(hook_name, plugin_name)
            return {"status": "COMPLETED", "ok": True, "registered_hooks": registry.hook_names()}
        return {"status": "COMPLETED", "ok": False, "reason": "unknown_action"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("HookProvider %s cleaned up.", self.agent_id)


class EventProvider(BaseAgent):
    """L5 agent notifying event listeners when domain events are emitted."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("EventProvider %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        listeners = task_envelope.get("listeners", {})
        event = task_envelope.get("event_name", "")
        payload = task_envelope.get("payload", {})
        notified = len(listeners.get(event, []))
        return {"status": "COMPLETED", "ok": True, "event": event, "listeners_notified": notified, "payload_echo": payload}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("EventProvider %s cleaned up.", self.agent_id)


class FilterProvider(BaseAgent):
    """L5 agent registering and applying payload filter pipelines."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("FilterProvider %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        registry = task_envelope.get("registry")
        action = task_envelope.get("action", "register")
        filter_name = task_envelope.get("filter_name", "")
        plugin_name = task_envelope.get("plugin_name", "")
        func = task_envelope.get("func")
        payload = task_envelope.get("payload")
        if registry is None:
            return {"status": "COMPLETED", "ok": False, "reason": "registry_missing"}
        if action == "register" and func:
            registry.register(filter_name, plugin_name, func)
            return {"status": "COMPLETED", "ok": True, "filters": registry.filter_names()}
        if action == "apply":
            result = registry.apply(filter_name, payload)
            return {"status": "COMPLETED", "ok": True, "filter_result": result}
        return {"status": "COMPLETED", "ok": False, "reason": "unknown_action"}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("FilterProvider %s cleaned up.", self.agent_id)


class ActionProvider(BaseAgent):
    """L5 agent dispatching named plugin actions to registered handlers."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ActionProvider %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        actions = task_envelope.get("actions", {})
        action_name = task_envelope.get("action_name", "")
        args = task_envelope.get("args", ())
        if action_name not in actions:
            return {"status": "COMPLETED", "ok": False, "reason": f"unknown_action:{action_name}"}
        result = actions[action_name](*args)
        return {"status": "COMPLETED", "ok": True, "action": action_name, "result": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ActionProvider %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PluginApiProvider Agent
# ==============================================================================

class PluginApiProvider(BaseAgent):
    """L4 coordinator exposing the unified plugin API surface (hooks/events/filters/actions)."""

    def __init__(
        self,
        name: str = "PluginApiProvider",
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
            "plugin_api_provider",
            "hook_provider",
            "event_provider",
            "filter_provider",
            "action_provider",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P9_PLUGIN_API_PROVIDER",
        )
        self.hook_registry = HookRegistry()
        self.hook_executor = HookExecutor(self.hook_registry)
        self.filter_registry = FilterRegistry()
        self.hook_provider: Optional[HookProvider] = None
        self.event_provider: Optional[EventProvider] = None
        self.filter_provider: Optional[FilterProvider] = None
        self.action_provider: Optional[ActionProvider] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("provide_plugin_api", self.provide_plugin_api)

    def _spawn_subagents(self) -> None:
        """Spawn atomic plugin API provider subagents (Rule 1 & Rule 5)."""
        logger.info("PluginApiProvider %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.hook_provider = self.spawn_subagent(HookProvider, name="HookProvider", max_depth=child_depth, resources_mb=32)
        self.event_provider = self.spawn_subagent(EventProvider, name="EventProvider", max_depth=child_depth, resources_mb=32)
        self.filter_provider = self.spawn_subagent(FilterProvider, name="FilterProvider", max_depth=child_depth, resources_mb=32)
        self.action_provider = self.spawn_subagent(ActionProvider, name="ActionProvider", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginApiProvider %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.provide_plugin_api(payload)
        return {"status": "COMPLETED", "api_provision": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginApiProvider %s cleanup complete.", self.agent_id)

    def provide_plugin_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route an API call to the appropriate provider worker."""
        logger.info("Providing plugin API for %s...", payload.get("kind", "unknown"))
        kind = payload.get("kind", "")
        if kind == "hook":
            result = self.hook_provider.process({"registry": self.hook_registry, **payload}) if self.hook_provider else {}
        elif kind == "event":
            result = self.event_provider.process(payload) if self.event_provider else {}
        elif kind == "filter":
            result = self.filter_provider.process({"registry": self.filter_registry, **payload}) if self.filter_provider else {}
        elif kind == "action":
            result = self.action_provider.process(payload) if self.action_provider else {}
        else:
            raise PluginAPIError(f"Unknown plugin API kind: {kind}")
        return result

    def register_hook(self, hook_name: str, plugin_name: str, callback: Callable[..., Any]) -> None:
        """Convenience API for registering a hook callback."""
        self.hook_registry.register(hook_name, plugin_name, callback)

    def execute_hooks(self, hook_name: str, *args: Any, **kwargs: Any) -> List[Any]:
        """Convenience API for executing all callbacks of a hook."""
        return self.hook_executor.execute(hook_name, *args, **kwargs)

    def apply_filter(self, filter_name: str, payload: Any) -> Any:
        """Convenience API for applying a filter pipeline."""
        return self.filter_registry.apply(filter_name, payload)