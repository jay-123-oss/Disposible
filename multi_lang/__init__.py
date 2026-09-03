"""Multi-Language Support Layer for the Fractal Multi-Agent Autonomous Coding System.

Exports all 14 multi-language agents (M1-M14) and 57 atomic subagents across L3 to L5,
along with custom exceptions and the registration helper `register_all_multi_lang_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from core.registry import AgentRegistry
from multi_lang.code_formatter import (
    BlackFormatter,
    CodeFormatter,
    GofmtFormatter,
    GoogleJavaFormatter,
    PrettierFormatter,
    RustfmtFormatter,
)
from multi_lang.cross_language_validator import (
    CrossLanguageValidator,
    LogicValidator,
    PerformanceValidator,
    SecurityValidator,
    SyntaxValidator,
)
from multi_lang.dependency_resolver import (
    CompatibilityChecker,
    ConflictResolver,
    DependencyResolver,
    UpdateManager,
    VersionResolver,
)
from multi_lang.documentation_generator import (
    DocumentationGenerator,
    GodocGenerator,
    JavadocGenerator,
    JsdocGenerator,
    PythonDocGenerator,
    RustdocGenerator,
)
from multi_lang.exceptions import (
    CodeFormattingError,
    CrossLanguageValidationError,
    DependencyResolutionError,
    DocumentationGenerationError,
    FrameworkSelectionError,
    GoGenerationError,
    JavaGenerationError,
    LanguageDetectionError,
    LanguageTranslationError,
    MultiLanguageError,
    NodeGenerationError,
    PackageManagementError,
    PythonGenerationError,
    RustGenerationError,
)
from multi_lang.framework_selector import (
    ActixSelector,
    ExpressSelector,
    FastapiSelector,
    FrameworkSelector,
    GinSelector,
    SpringSelector,
)
from multi_lang.go_generator import (
    GoApiGenerator,
    GoDependencyGenerator,
    GoGenerator,
    GoModelGenerator,
    GoTestGenerator,
)
from multi_lang.java_generator import (
    JavaApiGenerator,
    JavaDependencyGenerator,
    JavaGenerator,
    JavaModelGenerator,
    JavaTestGenerator,
)
from multi_lang.language_detector import (
    ConfidenceScorer,
    FileExtensionAnalyzer,
    LanguageDetector,
    PatternMatcher,
    SyntaxAnalyzer,
)
from multi_lang.language_translator import (
    LanguageTranslator,
    NodeToPythonTranslator,
    PythonToGoTranslator,
    PythonToJavaTranslator,
    PythonToNodeTranslator,
    PythonToRustTranslator,
)
from multi_lang.multi_lang_orchestrator import MultiLanguageOrchestrator
from multi_lang.node_generator import (
    NodeApiGenerator,
    NodeDependencyGenerator,
    NodeGenerator,
    NodeModelGenerator,
    NodeTestGenerator,
)
from multi_lang.package_manager import (
    CargoManager,
    GoModManager,
    MavenManager,
    NpmManager,
    PackageManager,
    PipManager,
)
from multi_lang.python_generator import (
    PythonApiGenerator,
    PythonDependencyGenerator,
    PythonGenerator,
    PythonModelGenerator,
    PythonTestGenerator,
)
from multi_lang.rust_generator import (
    RustApiGenerator,
    RustDependencyGenerator,
    RustGenerator,
    RustModelGenerator,
    RustTestGenerator,
)


logger = logging.getLogger("FractalCore.MultiLang")


__all__ = [
    # Master Orchestrator
    "MultiLanguageOrchestrator",
    # Python Generator
    "PythonGenerator", "PythonApiGenerator", "PythonModelGenerator", "PythonTestGenerator", "PythonDependencyGenerator",
    # Node Generator
    "NodeGenerator", "NodeApiGenerator", "NodeModelGenerator", "NodeTestGenerator", "NodeDependencyGenerator",
    # Go Generator
    "GoGenerator", "GoApiGenerator", "GoModelGenerator", "GoTestGenerator", "GoDependencyGenerator",
    # Rust Generator
    "RustGenerator", "RustApiGenerator", "RustModelGenerator", "RustTestGenerator", "RustDependencyGenerator",
    # Java Generator
    "JavaGenerator", "JavaApiGenerator", "JavaModelGenerator", "JavaTestGenerator", "JavaDependencyGenerator",
    # Language Detector
    "LanguageDetector", "SyntaxAnalyzer", "PatternMatcher", "FileExtensionAnalyzer", "ConfidenceScorer",
    # Language Translator
    "LanguageTranslator", "PythonToNodeTranslator", "PythonToGoTranslator", "PythonToRustTranslator",
    "PythonToJavaTranslator", "NodeToPythonTranslator",
    # Cross-Language Validator
    "CrossLanguageValidator", "SyntaxValidator", "LogicValidator", "PerformanceValidator", "SecurityValidator",
    # Package Manager
    "PackageManager", "PipManager", "NpmManager", "GoModManager", "CargoManager", "MavenManager",
    # Framework Selector
    "FrameworkSelector", "FastapiSelector", "ExpressSelector", "GinSelector", "ActixSelector", "SpringSelector",
    # Dependency Resolver
    "DependencyResolver", "VersionResolver", "ConflictResolver", "CompatibilityChecker", "UpdateManager",
    # Code Formatter
    "CodeFormatter", "BlackFormatter", "PrettierFormatter", "GofmtFormatter", "RustfmtFormatter", "GoogleJavaFormatter",
    # Documentation Generator
    "DocumentationGenerator", "PythonDocGenerator", "JsdocGenerator", "GodocGenerator", "RustdocGenerator", "JavadocGenerator",
    # Exceptions
    "MultiLanguageError", "PythonGenerationError", "NodeGenerationError", "GoGenerationError",
    "RustGenerationError", "JavaGenerationError", "LanguageDetectionError", "LanguageTranslationError",
    "CrossLanguageValidationError", "PackageManagementError", "FrameworkSelectionError",
    "DependencyResolutionError", "CodeFormattingError", "DocumentationGenerationError",
    # Registration Helper
    "register_all_multi_lang_agents",
]


def register_all_multi_lang_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Register all Multi-Language Support layer agents into the central AgentRegistry.

    Args:
        registry: The central AgentRegistry singleton.
        parent_agent: Optional supervising orchestrator coordinator.
        max_depth: Global depth ceiling for the multi-language hierarchy.

    Returns:
        Dict mapping root agent and count of registered agents.
    """
    logger.info("Registering all multi-language support domain agents into AgentRegistry...")

    multilang_orchestrator = MultiLanguageOrchestrator(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="M1_MULTI_LANGUAGE_ORCHESTRATOR",
        auto_spawn_subagents=True,
    )
    registry.register_agent(multilang_orchestrator)

    registered_count = 1

    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(multilang_orchestrator)

    logger.info("Successfully registered %d multi-language domain agents into registry.", registered_count)
    return {
        "multilang_orchestrator": multilang_orchestrator,
        "total_registered": registered_count,
    }