"""Plugin System Layer for the Fractal Multi-Agent Autonomous Coding System.

Exports all 14 plugin agents (P1-P14) and 53 atomic subagents across L3 to L5,
along with the plugin API, hook infrastructure, built-in plugins, custom exceptions,
and the registration helper `register_all_plugin_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from core.registry import AgentRegistry
from plugins.exceptions import (
    PluginAPIError,
    PluginDependencyError,
    PluginDocumentationError,
    PluginError,
    PluginEventError,
    PluginInstallerError,
    PluginLoaderError,
    PluginManagerError,
    PluginMarketplaceError,
    PluginSecurityError,
    PluginStoreError,
    PluginUninstallerError,
    PluginValidationError,
    PluginVersionError,
)
from plugins.plugin_api import PluginContext, PluginInterface, PluginMetadata, PluginResult
from plugins.plugin_api_provider import (
    ActionProvider,
    EventProvider,
    FilterProvider,
    HookProvider,
    PluginApiProvider,
)
from plugins.plugin_dependencies import (
    CompatibilityChecker,
    ConflictResolver,
    DependencyResolver,
    PluginDependencies,
    TreeVisualizer,
)
from plugins.plugin_documentation import (
    ApiDocGenerator,
    DocGenerator,
    ExampleGenerator,
    PluginDocumentation,
    TutorialGenerator,
)
from plugins.plugin_event_listener import (
    EventDispatcher,
    EventHandler,
    EventLogger,
    EventRegistrar,
    PluginEventListener,
)
from plugins.plugin_hooks import FilterRegistry, HookExecutor, HookRegistry
from plugins.plugin_installer import (
    Downloader,
    Extractor,
    PluginInstaller,
    SetupExecutor,
    VerificationRunner,
)
from plugins.plugin_loader import (
    DynamicLoader,
    HotReloader,
    PluginLoader,
    RuntimeLoader,
    StaticLoader,
)
from plugins.plugin_manager import (
    PluginActivator,
    PluginDeactivator,
    PluginManager,
    PluginRegistrar,
    PluginStatusChecker,
)
from plugins.plugin_marketplace import (
    PluginMarketplace,
    PluginRater,
    PluginRecommender,
    PluginReviewer,
    PluginSearcher,
)
from plugins.plugin_orchestrator import PluginOrchestrator
from plugins.plugin_security_scanner import (
    MalwareScanner,
    PermissionChecker,
    PluginSecurityScanner,
    SignatureVerifier,
    VulnerabilityScanner,
)
from plugins.plugin_store import (
    CacheManager,
    IndexUpdater,
    LocalStore,
    PluginStore,
    RemoteStore,
)
from plugins.plugin_uninstaller import (
    Cleaner,
    DependencyChecker,
    PluginUninstaller,
    Remover,
    RollbackExecutor,
)
from plugins.plugin_validator import (
    CompatibilityChecker as PluginCompatibilityChecker,
    PerformanceChecker,
    PluginValidator,
    SchemaValidator,
    SyntaxValidator as PluginSyntaxValidator,
)
from plugins.plugin_version_manager import (
    PluginVersionManager,
    VersionChecker,
    VersionHistory,
    VersionRollback,
    VersionUpdater,
)


logger = logging.getLogger("FractalCore.PluginSystem")


__all__ = [
    # Master Orchestrator
    "PluginOrchestrator",
    # Plugin Manager
    "PluginManager", "PluginRegistrar", "PluginActivator", "PluginDeactivator", "PluginStatusChecker",
    # Plugin Loader
    "PluginLoader", "DynamicLoader", "StaticLoader", "RuntimeLoader", "HotReloader",
    # Plugin Store
    "PluginStore", "LocalStore", "RemoteStore", "CacheManager", "IndexUpdater",
    # Plugin Installer
    "PluginInstaller", "Downloader", "Extractor", "SetupExecutor", "VerificationRunner",
    # Plugin Uninstaller
    "PluginUninstaller", "Remover", "Cleaner", "RollbackExecutor", "DependencyChecker",
    # Plugin Validator
    "PluginValidator", "PluginSyntaxValidator", "SchemaValidator", "PluginCompatibilityChecker", "PerformanceChecker",
    # Plugin Security Scanner
    "PluginSecurityScanner", "VulnerabilityScanner", "MalwareScanner", "PermissionChecker", "SignatureVerifier",
    # Plugin API Provider
    "PluginApiProvider", "HookProvider", "EventProvider", "FilterProvider", "ActionProvider",
    # Plugin Event Listener
    "PluginEventListener", "EventRegistrar", "EventDispatcher", "EventHandler", "EventLogger",
    # Plugin Marketplace
    "PluginMarketplace", "PluginSearcher", "PluginRecommender", "PluginRater", "PluginReviewer",
    # Plugin Version Manager
    "PluginVersionManager", "VersionChecker", "VersionUpdater", "VersionRollback", "VersionHistory",
    # Plugin Dependencies
    "PluginDependencies", "DependencyResolver", "ConflictResolver", "CompatibilityChecker", "TreeVisualizer",
    # Plugin Documentation
    "PluginDocumentation", "DocGenerator", "ApiDocGenerator", "ExampleGenerator", "TutorialGenerator",
    # Plugin API surface
    "PluginInterface", "PluginContext", "PluginResult", "PluginMetadata",
    "HookRegistry", "HookExecutor", "FilterRegistry",
    # Exceptions
    "PluginError", "PluginManagerError", "PluginLoaderError", "PluginStoreError", "PluginInstallerError",
    "PluginUninstallerError", "PluginValidationError", "PluginSecurityError", "PluginAPIError",
    "PluginEventError", "PluginMarketplaceError", "PluginVersionError", "PluginDependencyError",
    "PluginDocumentationError",
    # Registration Helper
    "register_all_plugin_agents",
]


def register_all_plugin_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Register all Plugin System layer agents into the central AgentRegistry.

    Args:
        registry: The central AgentRegistry singleton.
        parent_agent: Optional supervising orchestrator coordinator.
        max_depth: Global depth ceiling for the plugin hierarchy.

    Returns:
        Dict mapping root agent and count of registered agents.
    """
    logger.info("Registering all plugin system domain agents into AgentRegistry...")

    plugin_orchestrator = PluginOrchestrator(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="P1_PLUGIN_ORCHESTRATOR",
        auto_spawn_subagents=True,
    )
    registry.register_agent(plugin_orchestrator)

    registered_count = 1

    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(plugin_orchestrator)

    logger.info("Successfully registered %d plugin system domain agents into registry.", registered_count)
    return {
        "plugin_orchestrator": plugin_orchestrator,
        "total_registered": registered_count,
    }