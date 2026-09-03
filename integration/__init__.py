"""Integration & Assembly Domain Agents for the Fractal Multi-Agent Coding System.

Exports all 14 specialized integration agents and atomic subagents across levels L3 to L5,
along with the registration helper `register_all_integration_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from core.registry import AgentRegistry
from integration.agent_factory import (
    AgentFactory,
    CodingAgentCreator,
    CommStateAgentCreator,
    InfrastructureAgentCreator,
    MonitoringAgentCreator,
    PlanningAgentCreator,
    QualityAgentCreator,
    SecurityAgentCreator,
    TestingAgentCreator,
)
from integration.configuration_loader import (
    ConfigValidator,
    ConfigurationLoader,
    DefaultConfigLoader,
    EnvConfigLoader,
    YamlConfigLoader,
)
from integration.context_manager import (
    ContextCleaner,
    ContextManager,
    ContextPropagator,
    ContextRetriever,
    ContextStorage,
)
from integration.dependency_injector import (
    AgentDependencyInjector,
    CoreDependencyInjector,
    DependencyInjector,
    RepositoryDependencyInjector,
    ServiceDependencyInjector,
)
from integration.entry_point_manager import (
    ApiEntryPoint,
    BatchEntryPoint,
    CliEntryPoint,
    EntryPointManager,
    InteractiveEntryPoint,
)
from integration.error_handler import (
    ErrorHandler,
    ErrorEscalator,
    ErrorLogger,
    ErrorRecoverer,
    ExceptionCatcher,
)
from integration.exceptions import (
    AgentFactoryError,
    ConfigurationError,
    ContextError,
    DependencyError,
    HealthError,
    InitializationError,
    IntegrationError,
    InterfaceError,
    ResourceError,
    SessionError,
    ShutdownError,
    WorkflowError,
)
from integration.health_manager import (
    AgentHealth,
    HealthManager,
    HealthReport,
    ServiceHealth,
    SystemHealth,
)
from integration.integration_orchestrator import IntegrationOrchestrator
from integration.interface_builder import (
    ApiInterfaceBuilder,
    CliInterfaceBuilder,
    InterfaceBuilder,
    InterfaceRouter,
    WebInterfaceBuilder,
)
from integration.resource_manager import (
    ConnectionManager,
    FileManager,
    MemoryManager,
    ResourceManager,
    ThreadManager,
)
from integration.session_manager import (
    SessionCleaner,
    SessionCreator,
    SessionLoader,
    SessionManager,
    SessionSaver,
)
from integration.shutdown_manager import (
    AgentCleanup,
    ForceShutdown,
    GracefulShutdown,
    ResourceRelease,
    ShutdownManager,
)
from integration.system_initializer import (
    AgentRegistrar,
    ConfigLoader,
    HealthChecker,
    ServiceStarter,
    SystemInitializer,
)
from integration.workflow_orchestrator import (
    ConditionalWorkflow,
    LinearWorkflow,
    ParallelWorkflow,
    RecursiveWorkflow,
    WorkflowOrchestrator,
)


logger = logging.getLogger("FractalCore.Integration")

__all__ = [
    # Master Orchestrator
    "IntegrationOrchestrator",
    # System Initializer
    "SystemInitializer",
    "ConfigLoader",
    "AgentRegistrar",
    "ServiceStarter",
    "HealthChecker",
    # Agent Factory
    "AgentFactory",
    "PlanningAgentCreator",
    "CodingAgentCreator",
    "TestingAgentCreator",
    "SecurityAgentCreator",
    "QualityAgentCreator",
    "InfrastructureAgentCreator",
    "CommStateAgentCreator",
    "MonitoringAgentCreator",
    # Dependency Injector
    "DependencyInjector",
    "CoreDependencyInjector",
    "AgentDependencyInjector",
    "ServiceDependencyInjector",
    "RepositoryDependencyInjector",
    # Configuration Loader
    "ConfigurationLoader",
    "YamlConfigLoader",
    "EnvConfigLoader",
    "DefaultConfigLoader",
    "ConfigValidator",
    # Entry Point Manager
    "EntryPointManager",
    "CliEntryPoint",
    "InteractiveEntryPoint",
    "BatchEntryPoint",
    "ApiEntryPoint",
    # Interface Builder
    "InterfaceBuilder",
    "CliInterfaceBuilder",
    "WebInterfaceBuilder",
    "ApiInterfaceBuilder",
    "InterfaceRouter",
    # Workflow Orchestrator
    "WorkflowOrchestrator",
    "LinearWorkflow",
    "ParallelWorkflow",
    "ConditionalWorkflow",
    "RecursiveWorkflow",
    # Error Handler
    "ErrorHandler",
    "ExceptionCatcher",
    "ErrorLogger",
    "ErrorRecoverer",
    "ErrorEscalator",
    # Shutdown Manager
    "ShutdownManager",
    "GracefulShutdown",
    "ForceShutdown",
    "AgentCleanup",
    "ResourceRelease",
    # Health Manager
    "HealthManager",
    "SystemHealth",
    "AgentHealth",
    "ServiceHealth",
    "HealthReport",
    # Session Manager
    "SessionManager",
    "SessionCreator",
    "SessionLoader",
    "SessionSaver",
    "SessionCleaner",
    # Resource Manager
    "ResourceManager",
    "MemoryManager",
    "ThreadManager",
    "ConnectionManager",
    "FileManager",
    # Context Manager
    "ContextManager",
    "ContextPropagator",
    "ContextStorage",
    "ContextRetriever",
    "ContextCleaner",
    # Exceptions
    "IntegrationError",
    "InitializationError",
    "AgentFactoryError",
    "DependencyError",
    "ConfigurationError",
    "InterfaceError",
    "WorkflowError",
    "ShutdownError",
    "HealthError",
    "SessionError",
    "ResourceError",
    "ContextError",
    # Registration Helper
    "register_all_integration_agents",
]


def register_all_integration_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Register all integration and assembly layer agents into the AgentRegistry.

    Args:
        registry: The central AgentRegistry singleton.
        parent_agent: Optional supervising orchestrator coordinator.
        max_depth: Global depth ceiling for integration hierarchy.

    Returns:
        Dict mapping agent_id to instantiated agent instances.
    """
    logger.info("Registering all integration & assembly domain agents into AgentRegistry...")

    # Root Integration Orchestrator (L3)
    integration_orchestrator = IntegrationOrchestrator(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="IA1_INTEGRATION_ORCHESTRATOR",
        auto_spawn_subagents=True,
    )
    registry.register_agent(integration_orchestrator)

    registered_count = 1
    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(integration_orchestrator)

    logger.info("Successfully registered %d integration domain agents into registry.", registered_count)
    return {
        "integration_orchestrator": integration_orchestrator,
        "total_registered": registered_count,
    }
