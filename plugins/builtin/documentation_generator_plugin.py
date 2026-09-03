"""Built-in DocumentationGeneratorPlugin that generates documentation for code and plugins."""

from __future__ import annotations

from plugins.plugin_api import PluginInterface


class DocumentationGeneratorPlugin(PluginInterface):
    """Generates Sphinx/JSDoc/godoc/rustdoc/Javadoc-style documentation stubs."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "documentation-generator"
        self.version = "1.0.0"
        self.author = "Fractal System"
        self.description = "Generates documentation"

    def get_hooks(self):
        return {"on_document": self._document}

    def get_actions(self):
        return {"generate_docs": self._document}

    def _document(self, module_name: str = "myservice", language: str = "python", **kwargs):
        """Return a deterministic documentation stub envelope."""
        tool = {"python": "sphinx", "node": "jsdoc", "go": "godoc", "rust": "rustdoc", "java": "javadoc"}.get(language, "sphinx")
        return {"module": module_name, "language": language, "tool": tool, "doc_generated": True}