"""Final System Integration & Deployment Layer Package.

Exports all 14 agents, 52 subagents, domain exceptions, and registry helper.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from core.registry import AgentRegistry
from final_integration.code_validator import (
    CodeValidator,
    LintChecker,
    QualityChecker,
    SyntaxChecker,
    TypeChecker,
)
from final_integration.compliance_checker import ComplianceCheckerUtil
from final_integration.configuration_merger import (
    ConfigCollector,
    ConfigTester,
    ConfigValidator,
    ConfigurationMerger,
    MergeEngine,
)
from final_integration.dependency_resolver import (
    ConflictResolver,
    DependencyExtractor,
    DependencyResolver,
    InstallationExecutor,
    VersionResolver,
)
from final_integration.deployment_executor import (
    CloudDeployer,
    DeploymentExecutor,
    DockerDeployer,
    K8sDeployer,
    LocalDeployer,
)
from final_integration.exceptions import (
    CodeValidationError,
    ConfigurationMergeError,
    DependencyResolutionError,
    DeploymentExecutionError,
    FinalIntegrationError,
    GoLiveError,
    HandoverError,
    HealthVerificationError,
    PostDeploymentVerificationError,
    RollbackError,
    ServiceOrchestrationError,
    SignoffError,
    SmokeTestError,
    SystemAssemblyError,
)
from final_integration.final_integration_orchestrator import FinalIntegrationOrchestrator
from final_integration.final_signoff_collector import (
    ApprovalTracker,
    FinalReportGenerator,
    FinalSignoffCollector,
    SignatureCollector,
    SignoffChecklistGenerator,
)
from final_integration.go_live_manager import (
    AnnouncementGenerator,
    ApprovalCollector,
    GoLiveExecutor,
    GoLiveManager,
    ReadinessChecker,
)
from final_integration.handover_manager import (
    DocumentationPreparer,
    HandoverManager,
    HandoverMeetingCoordinator,
    OperationsGuideGenerator,
    TrainingMaterialGenerator,
)
from final_integration.health_verifier import (
    AgentHealthChecker,
    HealthVerifier,
    PerformanceHealthChecker,
    ServiceHealthChecker,
    SystemHealthChecker,
)
from final_integration.post_deployment_verifier import (
    FunctionalVerifier,
    PerformanceVerifier,
    PostDeploymentVerifier,
    SecurityVerifier,
    UserVerifier,
)
from final_integration.quality_checker import QualityCheckerUtil
from final_integration.rollback_coordinator import (
    RollbackCommunicator,
    RollbackCoordinator,
    RollbackExecutor,
    RollbackPlanner,
    RollbackVerifier,
)
from final_integration.service_orchestrator import (
    ServiceConnector,
    ServiceHealthChecker as SrvHealthProbe,
    ServiceMonitor,
    ServiceOrchestrator,
    ServiceStarter,
)
from final_integration.smoke_tester import (
    ApiSmokeTester,
    CriticalFlowTester,
    IntegrationSmokeTester,
    SmokeTester,
    UiSmokeTester,
)
from final_integration.system_assembler import (
    AssemblyEngine,
    ComponentCollector,
    ComponentValidator,
    IntegrityChecker,
    SystemAssembler,
)

logger = logging.getLogger("FractalCore.FinalIntegration")

__all__ = [
    # Master Orchestrator (L3)
    "FinalIntegrationOrchestrator",
    # Coordinators (L4)
    "SystemAssembler",
    "DependencyResolver",
    "ConfigurationMerger",
    "CodeValidator",
    "DeploymentExecutor",
    "ServiceOrchestrator",
    "HealthVerifier",
    "GoLiveManager",
    "SmokeTester",
    "RollbackCoordinator",
    "PostDeploymentVerifier",
    "HandoverManager",
    "FinalSignoffCollector",
    # Atomic Workers (L5)
    "ComponentCollector",
    "ComponentValidator",
    "AssemblyEngine",
    "IntegrityChecker",
    "DependencyExtractor",
    "VersionResolver",
    "ConflictResolver",
    "InstallationExecutor",
    "ConfigCollector",
    "ConfigValidator",
    "MergeEngine",
    "ConfigTester",
    "SyntaxChecker",
    "TypeChecker",
    "LintChecker",
    "QualityChecker",
    "DockerDeployer",
    "K8sDeployer",
    "CloudDeployer",
    "LocalDeployer",
    "ServiceStarter",
    "ServiceConnector",
    "SrvHealthProbe",
    "ServiceMonitor",
    "SystemHealthChecker",
    "AgentHealthChecker",
    "ServiceHealthChecker",
    "PerformanceHealthChecker",
    "ReadinessChecker",
    "ApprovalCollector",
    "GoLiveExecutor",
    "AnnouncementGenerator",
    "CriticalFlowTester",
    "ApiSmokeTester",
    "UiSmokeTester",
    "IntegrationSmokeTester",
    "RollbackPlanner",
    "RollbackExecutor",
    "RollbackVerifier",
    "RollbackCommunicator",
    "FunctionalVerifier",
    "PerformanceVerifier",
    "SecurityVerifier",
    "UserVerifier",
    "DocumentationPreparer",
    "TrainingMaterialGenerator",
    "OperationsGuideGenerator",
    "HandoverMeetingCoordinator",
    "SignoffChecklistGenerator",
    "ApprovalTracker",
    "SignatureCollector",
    "FinalReportGenerator",
    # Utilities
    "QualityCheckerUtil",
    "ComplianceCheckerUtil",
    # Exceptions
    "FinalIntegrationError",
    "SystemAssemblyError",
    "DependencyResolutionError",
    "ConfigurationMergeError",
    "CodeValidationError",
    "DeploymentExecutionError",
    "ServiceOrchestrationError",
    "HealthVerificationError",
    "GoLiveError",
    "SmokeTestError",
    "RollbackError",
    "PostDeploymentVerificationError",
    "HandoverError",
    "SignoffError",
    # Helper
    "register_all_final_integration_agents",
]


def register_all_final_integration_agents(
    registry: AgentRegistry,
    parent_orchestrator: Optional[FinalIntegrationOrchestrator] = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Instantiate and register all 14 Final Integration coordinators and 52 subagents into registry."""
    orch = parent_orchestrator or FinalIntegrationOrchestrator(
        agent_id="FI1_FINAL_INTEGRATION_ORCHESTRATOR",
        max_depth=max_depth,
        auto_spawn_subagents=True,
    )
    registry.register_agent(orch)
    registered_count = 1

    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(orch)

    logger.info("Successfully registered %d Final Integration domain agents into registry.", registered_count)
    return {
        "final_integration_orchestrator": orch,
        "total_registered": registered_count,
    }
