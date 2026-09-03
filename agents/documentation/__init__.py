"""Documentation Layer for the Fractal Multi-Agent Autonomous Coding System.

Exports all 12 specialized documentation agents (D1 to D12) and 44 atomic subagents across L3 to L5,
along with custom exceptions and the registration helper `register_all_documentation_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from agents.documentation.agent_reference import (
    AgentApiReference,
    AgentCapabilities,
    AgentLifecycle,
    AgentReference,
    CustomAgentGuide,
)
from agents.documentation.api_documentation import (
    ApiDocumentation,
    EndpointDocumenter,
    OpenApiGenerator,
    SchemaDocumenter,
    SwaggerGenerator,
)
from agents.documentation.configuration_guide import (
    ConfigReference,
    ConfigurationGuide,
    CustomConfigGuide,
    EnvironmentVariables,
    ValidationGuide,
)
from agents.documentation.deployment_guide import (
    CiCdDeployment,
    CloudDeployment,
    DeploymentGuide,
    DockerDeployment,
    K8sDeployment,
)
from agents.documentation.developer_guide import (
    CodeStructureGuide,
    ContributingGuide,
    DebuggingGuide,
    DeveloperGuide,
    ExtensionGuide,
)
from agents.documentation.documentation_orchestrator import DocumentationOrchestrator
from agents.documentation.example_repository import (
    AdvancedExamples,
    BasicExamples,
    ExampleRepository,
    IntegrationExamples,
    UseCaseExamples,
)
from agents.documentation.exceptions import (
    AgentReferenceError,
    ApiDocumentationError,
    ConfigurationGuideError,
    DeploymentGuideError,
    DeveloperGuideError,
    DocumentationError,
    ExampleRepositoryError,
    FaqGenerationError,
    InstallationGuideError,
    SystemDocumentationError,
    TroubleshootingGuideError,
    UserGuideError,
)
from agents.documentation.faq_generator import (
    ConfigurationFaq,
    FaqGenerator,
    GeneralFaq,
    TechnicalFaq,
    TroubleshootingFaq,
)
from agents.documentation.installation_guide import (
    InstallationGuide,
    PrerequisitesDocumenter,
    StepByStepInstall,
    TroubleshootingInstall,
    VerificationGuide,
)
from agents.documentation.system_documentation import (
    ArchitectureDocumenter,
    ComponentDocumenter,
    DataFlowDocumenter,
    SystemDiagramGenerator,
    SystemDocumentation,
)
from agents.documentation.troubleshooting_guide import (
    CommonIssues,
    ErrorCodes,
    EscalationGuide,
    SolutionSteps,
    TroubleshootingGuide,
)
from agents.documentation.user_guide import (
    BestPracticesGuide,
    FeatureGuide,
    GettingStarted,
    UseCaseGuide,
    UserGuide,
)
from core.registry import AgentRegistry


logger = logging.getLogger("FractalCore.Docs")

__all__ = [
    # Master Documentation Orchestrator
    "DocumentationOrchestrator",
    # System Documentation
    "SystemDocumentation",
    "ArchitectureDocumenter",
    "ComponentDocumenter",
    "DataFlowDocumenter",
    "SystemDiagramGenerator",
    # API Documentation
    "ApiDocumentation",
    "OpenApiGenerator",
    "SwaggerGenerator",
    "EndpointDocumenter",
    "SchemaDocumenter",
    # User Guide
    "UserGuide",
    "GettingStarted",
    "FeatureGuide",
    "UseCaseGuide",
    "BestPracticesGuide",
    # Developer Guide
    "DeveloperGuide",
    "CodeStructureGuide",
    "ExtensionGuide",
    "ContributingGuide",
    "DebuggingGuide",
    # Installation Guide
    "InstallationGuide",
    "PrerequisitesDocumenter",
    "StepByStepInstall",
    "TroubleshootingInstall",
    "VerificationGuide",
    # Configuration Guide
    "ConfigurationGuide",
    "ConfigReference",
    "EnvironmentVariables",
    "CustomConfigGuide",
    "ValidationGuide",
    # Deployment Guide
    "DeploymentGuide",
    "DockerDeployment",
    "K8sDeployment",
    "CloudDeployment",
    "CiCdDeployment",
    # Agent Reference
    "AgentReference",
    "AgentApiReference",
    "AgentCapabilities",
    "AgentLifecycle",
    "CustomAgentGuide",
    # Example Repository
    "ExampleRepository",
    "BasicExamples",
    "AdvancedExamples",
    "UseCaseExamples",
    "IntegrationExamples",
    # Troubleshooting Guide
    "TroubleshootingGuide",
    "CommonIssues",
    "ErrorCodes",
    "SolutionSteps",
    "EscalationGuide",
    # FAQ Generator
    "FaqGenerator",
    "GeneralFaq",
    "TechnicalFaq",
    "ConfigurationFaq",
    "TroubleshootingFaq",
    # Exceptions
    "DocumentationError",
    "SystemDocumentationError",
    "ApiDocumentationError",
    "UserGuideError",
    "DeveloperGuideError",
    "InstallationGuideError",
    "ConfigurationGuideError",
    "DeploymentGuideError",
    "AgentReferenceError",
    "ExampleRepositoryError",
    "TroubleshootingGuideError",
    "FaqGenerationError",
    # Registration Helper
    "register_all_documentation_agents",
]


def register_all_documentation_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Register all Documentation layer agents into the central AgentRegistry.

    Args:
        registry: The central AgentRegistry singleton.
        parent_agent: Optional supervising orchestrator coordinator.
        max_depth: Global depth ceiling.

    Returns:
        Dict mapping root agent and count of registered agents.
    """
    logger.info("Registering all documentation domain agents into AgentRegistry...")

    doc_orchestrator = DocumentationOrchestrator(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="D1_DOCUMENTATION_ORCHESTRATOR",
        auto_spawn_subagents=True,
    )
    registry.register_agent(doc_orchestrator)

    registered_count = 1

    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(doc_orchestrator)

    logger.info("Successfully registered %d documentation domain agents into registry.", registered_count)
    return {
        "doc_orchestrator": doc_orchestrator,
        "total_registered": registered_count,
    }
