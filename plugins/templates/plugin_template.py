"""Template: Third-party plugin scaffold. Copy this file to build a new plugin.

Placeholders like __PLUGIN_NAME__ are substituted by the Plugin Template tooling.
"""
from __future__ import annotations

from plugins.plugin_api import PluginInterface


class __PLUGIN_NAME__(PluginInterface):
    """Example plugin implementing the full PluginInterface contract."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "__PLUGIN_NAME__"
        self.version = "__PLUGIN_VERSION__"
        self.author = "__PLUGIN_AUTHOR__"
        self.description = "__PLUGIN_DESCRIPTION__"

    def get_hooks(self):
        """Expose the hooks this plugin subscribes to."""
        return {"on_generate": self._on_generate}

    def get_events(self):
        """Expose the events this plugin produces."""
        return {"plugin.ran": self._on_run}

    def get_filters(self):
        """Expose the filter pipelines this plugin participates in."""
        return {"code": self._filter_code}

    def get_actions(self):
        """Expose the actions this plugin provides."""
        return {"run": self._on_run}

    def _on_generate(self, payload=None):
        """Hook callback executed during generation."""
        return {"plugin": self.name, "status": "hooked"}

    def _filter_code(self, code, **kwargs):
        """Filter callback that can transform generated code."""
        return code

    def _on_run(self, *args, **kwargs):
        """Action callback invoked by the ActionProvider."""
        return {"plugin": self.name, "ran": True}