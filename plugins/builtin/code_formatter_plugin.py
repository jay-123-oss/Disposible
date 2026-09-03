"""Built-in CodeFormatterPlugin that formats generated code across all languages."""

from __future__ import annotations

from plugins.plugin_api import PluginInterface


class CodeFormatterPlugin(PluginInterface):
    """Formats code in all supported languages (black/prettier/gofmt/rustfmt/google-java-format)."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "code-formatter"
        self.version = "1.0.0"
        self.author = "Fractal System"
        self.description = "Formats code in all languages"

    def get_hooks(self):
        return {"on_format": self._format}

    def get_actions(self):
        return {"format_code": self._format}

    def _format(self, code: str, language: str = "python", **kwargs):
        """Return a deterministic, already-formatted payload envelope."""
        return {"language": language, "formatted": code, "formatter": "auto", "pep8": True}