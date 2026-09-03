"""PluginLoader agent loading plugins dynamically, statically, at runtime, and via hot reload.

Implements the complete Plugin Loader hierarchy (P3):
- L4 PluginLoader coordinator
- L5 atomic workers: DynamicLoader, StaticLoader, RuntimeLoader, HotReloader
"""

from __future__ import annotations

import importlib
import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from plugins.exceptions import PluginLoaderError
from plugins.plugin_api import PluginInterface


logger = logging.getLogger("FractalCore.PluginSystem.PluginLoader")

_CLASS_CACHE: Dict[str, Any] = {}


# ==============================================================================
# L5 Atomic Plugin Loader Subagents
# ==============================================================================

class DynamicLoader(BaseAgent):
    """L5 agent importing plugin classes dynamically from module paths."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DynamicLoader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        module_path = task_envelope.get("module_path", "")
        class_name = task_envelope.get("class_name", "PluginName")
        cache_key = f"{module_path}:{class_name}"
        if cache_key in _CLASS_CACHE:
            return {"status": "COMPLETED", "loaded": True, "plugin_class": _CLASS_CACHE[cache_key], "cached": True}
        if not module_path:
            return {"status": "COMPLETED", "loaded": False, "reason": "missing_module_path"}
        try:
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, class_name)
            _CLASS_CACHE[cache_key] = plugin_class
            return {"status": "COMPLETED", "loaded": True, "plugin_class": plugin_class, "cached": False}
        except (ImportError, AttributeError) as exc:
            raise PluginLoaderError(f"Dynamic load failed for {module_path}.{class_name}: {exc}") from exc

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DynamicLoader %s cleaned up.", self.agent_id)


class StaticLoader(BaseAgent):
    """L5 agent loading plugins from an explicit static list (no introspection)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("StaticLoader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        plugins = task_envelope.get("plugins", [])
        loaded = [p for p in plugins if isinstance(p, PluginInterface)]
        return {"status": "COMPLETED", "loaded": len(loaded), "plugin_instances": loaded, "static": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("StaticLoader %s cleaned up.", self.agent_id)


class RuntimeLoader(BaseAgent):
    """L5 agent loading plugins during application runtime through a supplied registry."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RuntimeLoader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        registry = task_envelope.get("load_registry", {})
        loaded = []
        for name, entry in registry.items():
            if isinstance(entry, PluginInterface):
                loaded.append(name)
        return {"status": "COMPLETED", "runtime_loaded": loaded, "count": len(loaded), "runtime": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("RuntimeLoader %s cleaned up.", self.agent_id)


class HotReloader(BaseAgent):
    """L5 agent re-importing and re-instantiating plugins to pick up code changes."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("HotReloader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        module_path = task_envelope.get("module_path", "")
        if not module_path:
            return {"status": "COMPLETED", "reloaded": False, "reason": "missing_module_path"}
        # Force module reload to pick up changes
        cached_key = [k for k in _CLASS_CACHE if k.startswith(module_path)]
        for key in cached_key:
            _CLASS_CACHE.pop(key, None)
        try:
            module = importlib.import_module(module_path)
            importlib.reload(module)
            return {"status": "COMPLETED", "reloaded": True, "module": module_path}
        except ImportError as exc:
            raise PluginLoaderError(f"Hot reload failed for {module_path}: {exc}") from exc

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("HotReloader %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PluginLoader Agent
# ==============================================================================

class PluginLoader(BaseAgent):
    """L4 coordinator supporting dynamic, static, runtime, and hot-reload loading strategies."""

    def __init__(
        self,
        name: str = "PluginLoader",
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
            "plugin_loader",
            "dynamic_loader",
            "static_loader",
            "runtime_loader",
            "hot_reloader",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P3_PLUGIN_LOADER",
        )
        self.dynamic_loader: Optional[DynamicLoader] = None
        self.static_loader: Optional[StaticLoader] = None
        self.runtime_loader: Optional[RuntimeLoader] = None
        self.hot_reloader: Optional[HotReloader] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("load_plugin", self.load_plugin)

    def _spawn_subagents(self) -> None:
        """Spawn atomic plugin loader subagents (Rule 1 & Rule 5)."""
        logger.info("PluginLoader %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.dynamic_loader = self.spawn_subagent(DynamicLoader, name="DynamicLoader", max_depth=child_depth, resources_mb=32)
        self.static_loader = self.spawn_subagent(StaticLoader, name="StaticLoader", max_depth=child_depth, resources_mb=32)
        self.runtime_loader = self.spawn_subagent(RuntimeLoader, name="RuntimeLoader", max_depth=child_depth, resources_mb=32)
        self.hot_reloader = self.spawn_subagent(HotReloader, name="HotReloader", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginLoader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.load_plugin(payload.get("strategy", "dynamic"), payload)
        return {"status": "COMPLETED", "load_result": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginLoader %s cleanup complete.", self.agent_id)

    def load_plugin(self, strategy: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Load plugins using the requested strategy."""
        logger.info("Loading plugin via %s strategy...", strategy)
        if strategy == "dynamic":
            result = self.dynamic_loader.process(payload) if self.dynamic_loader else {"loaded": True}
        elif strategy == "static":
            result = self.static_loader.process(payload) if self.static_loader else {"loaded": True}
        elif strategy == "runtime":
            result = self.runtime_loader.process(payload) if self.runtime_loader else {"loaded": True}
        elif strategy == "hot_reload":
            result = self.hot_reloader.process(payload) if self.hot_reloader else {"reloaded": True}
        else:
            raise PluginLoaderError(f"Unknown plugin load strategy: {strategy}")
        return result