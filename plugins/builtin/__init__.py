"""Built-in plugins bundled with the Plugins System Layer.

Exports the five built-in plugins:
- CodeFormatterPlugin
- TestGeneratorPlugin
- SecurityScannerPlugin
- PerformanceOptimizerPlugin
- DocumentationGeneratorPlugin
"""

from plugins.builtin.code_formatter_plugin import CodeFormatterPlugin
from plugins.builtin.documentation_generator_plugin import DocumentationGeneratorPlugin
from plugins.builtin.performance_optimizer_plugin import PerformanceOptimizerPlugin
from plugins.builtin.security_scanner_plugin import SecurityScannerPlugin
from plugins.builtin.test_generator_plugin import TestGeneratorPlugin

__all__ = [
    "CodeFormatterPlugin",
    "TestGeneratorPlugin",
    "SecurityScannerPlugin",
    "PerformanceOptimizerPlugin",
    "DocumentationGeneratorPlugin",
]

BUILTIN_PLUGINS = [
    CodeFormatterPlugin,
    TestGeneratorPlugin,
    SecurityScannerPlugin,
    PerformanceOptimizerPlugin,
    DocumentationGeneratorPlugin,
]