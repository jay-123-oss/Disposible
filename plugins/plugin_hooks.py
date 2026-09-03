"""Plugin hook and filter infrastructure shared across the Plugin API Provider (P9)."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from plugins.exceptions import PluginAPIError, PluginEventError


logger = logging.getLogger("FractalCore.PluginSystem.Hooks")


class HookRegistry:
    """Central registry mapping hook names to registered plugin callbacks."""

    def __init__(self) -> None:
        self._hooks: Dict[str, Dict[str, Callable[..., Any]]] = {}

    def register(self, hook_name: str, plugin_name: str, callback: Callable[..., Any]) -> None:
        """Register a callback under a hook name for a given plugin."""
        self._hooks.setdefault(hook_name, {})[plugin_name] = callback

    def unregister(self, hook_name: str, plugin_name: str) -> None:
        """Remove a plugin's callback from a hook."""
        if hook_name in self._hooks:
            self._hooks[hook_name].pop(plugin_name, None)

    def callbacks(self, hook_name: str) -> List[Callable[..., Any]]:
        """Return all registered callbacks for a hook."""
        return list(self._hooks.get(hook_name, {}).values())

    def hook_names(self) -> List[str]:
        """List all registered hook names."""
        return list(self._hooks.keys())


class HookExecutor:
    """Executes chained hook callbacks in deterministic plugin registration order."""

    def __init__(self, registry: HookRegistry) -> None:
        self.registry = registry

    def execute(self, hook_name: str, *args: Any, **kwargs: Any) -> List[Any]:
        """Run every callback registered under the hook, collecting outputs."""
        results = []
        for callback in self.registry.callbacks(hook_name):
            try:
                results.append(callback(*args, **kwargs))
            except Exception as exc:  # pragma: no cover - defensive isolation
                logger.error("Hook '%s' callback failed: %s", hook_name, exc)
                raise PluginEventError(f"Hook {hook_name} callback failed: {exc}") from exc
        return results

    def execute_first(self, hook_name: str, *args: Any, **kwargs: Any) -> Optional[Any]:
        """Execute only the first registered callback for a hook."""
        callbacks = self.registry.callbacks(hook_name)
        return callbacks[0](*args, **kwargs) if callbacks else None


class FilterRegistry:
    """Pipeline of filters mutating a shared payload (blackboard-style)."""

    def __init__(self) -> None:
        self._filters: Dict[str, Dict[str, Callable[..., Any]]] = {}

    def register(self, filter_name: str, plugin_name: str, func: Callable[..., Any]) -> None:
        """Register a filter function for a named filter point."""
        self._filters.setdefault(filter_name, {})[plugin_name] = func

    def apply(self, filter_name: str, payload: Any, **kwargs: Any) -> Any:
        """Apply all registered filters sequentially, threading the payload through."""
        result = payload
        for func in list(self._filters.get(filter_name, {}).values()):
            result = func(result, **kwargs)
        return result

    def filter_names(self) -> List[str]:
        """List all registered filter names."""
        return list(self._filters.keys())