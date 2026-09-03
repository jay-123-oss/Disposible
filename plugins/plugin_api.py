"""Plugin API surface definition: PluginInterface, PluginContext, PluginResult, PluginMetadata.

Conforms to the Plugin API Specification from the Plugin System Layer (Prompt 24/25).
"""

from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional


class PluginContext:
    """Runtime context handed to plugins exposing services, config, and helpers."""

    def __init__(self, api: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        self.api = api
        self.config = config or {}
        self.logger = None
        self.services: Dict[str, Any] = {}

    def get_service(self, name: str) -> Any:
        """Retrieve a registered runtime service or None."""
        return self.services.get(name)

    def register_service(self, name: str, service: Any) -> None:
        """Register a runtime service for downstream plugins."""
        self.services[name] = service


class PluginResult:
    """Standardized success/failure envelope returned by plugin operations."""

    def __init__(
        self,
        success: bool,
        plugin_name: str = "",
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        self.success = success
        self.plugin_name = plugin_name
        self.data = data or {}
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the result envelope."""
        return {
            "success": self.success,
            "plugin_name": self.plugin_name,
            "data": self.data,
            "error": self.error,
        }

    @staticmethod
    def ok(plugin_name: str, data: Optional[Dict[str, Any]] = None) -> "PluginResult":
        """Factory helper for a successful plugin result."""
        return PluginResult(success=True, plugin_name=plugin_name, data=data)

    @staticmethod
    def fail(plugin_name: str, error: str, data: Optional[Dict[str, Any]] = None) -> "PluginResult":
        """Factory helper for a failed plugin result."""
        return PluginResult(success=False, plugin_name=plugin_name, data=data, error=error)


class PluginMetadata:
    """Declarative plugin metadata read from the plugin manifest."""

    def __init__(
        self,
        name: str,
        version: str,
        author: str = "Unknown",
        description: str = "",
        entry_point: str = "PluginName",
        dependencies: Optional[List[str]] = None,
        requires_version: str = ">=1.0.0",
        permissions: Optional[List[str]] = None,
    ) -> None:
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.entry_point = entry_point
        self.dependencies = dependencies or []
        self.requires_version = requires_version
        self.permissions = permissions or []

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata for manifests/JSON exchange."""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "entry_point": self.entry_point,
            "dependencies": self.dependencies,
            "requires_version": self.requires_version,
            "permissions": self.permissions,
        }


class PluginInterface(abc.ABC):
    """Abstract plugin contract every plugin must implement (Plugin API Specification)."""

    def __init__(self) -> None:
        self.name = "PluginName"
        self.version = "1.0.0"
        self.author = "Author"
        self.description = "Description"
        self.metadata: Optional[PluginMetadata] = None
        self._context: Optional[PluginContext] = None
        self._active = False

    @property
    def active(self) -> bool:
        """Whether the plugin is currently activated."""
        return self._active

    def initialize(self, api: Any) -> None:
        """Initialize plugin with API.

        Args:
            api: Plugin API provider surface (hook/event/filter/action access).
        """
        self._context = PluginContext(api=api)

    def activate(self) -> None:
        """Activate plugin."""
        self._active = True

    def deactivate(self) -> None:
        """Deactivate plugin."""
        self._active = False

    def uninstall(self) -> None:
        """Uninstall plugin and clean up resources."""
        self._active = False

    def get_hooks(self) -> Dict[str, Any]:
        """Return hooks as {hook_name: callable}."""
        return {}

    def get_events(self) -> Dict[str, Any]:
        """Return events as {event_name: callable}."""
        return {}

    def get_filters(self) -> Dict[str, Any]:
        """Return filters as {filter_name: callable}."""
        return {}

    def get_actions(self) -> Dict[str, Any]:
        """Return actions as {action_name: callable}."""
        return {}