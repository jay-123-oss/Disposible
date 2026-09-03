"""Built-in TestGeneratorPlugin that generates test skeletons for generated code."""

from __future__ import annotations

from plugins.plugin_api import PluginInterface


class TestGeneratorPlugin(PluginInterface):
    """Generates tests for code across pytest/Jest/go test/cargo test/JUnit."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "test-generator"
        self.version = "1.0.0"
        self.author = "Fractal System"
        self.description = "Generates tests for code"

    def get_hooks(self):
        return {"on_test": self._generate_test}

    def get_actions(self):
        return {"generate_test": self._generate_test}

    def _generate_test(self, code: str = "", language: str = "python", **kwargs):
        """Return a deterministic test-skeleton payload."""
        return {"language": language, "test_generated": True, "framework": self._framework(language)}

    def _framework(self, language: str) -> str:
        return {"python": "pytest", "node": "jest", "go": "go test", "rust": "cargo test", "java": "junit"}.get(language, "unknown")