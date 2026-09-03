"""Deployment & Distribution Layer for the Fractal Multi-Agent Autonomous Coding System.

Exports all 14 specialized deployment agents (DD1 to DD14) and 52 atomic subagents across L3 to L5,
along with custom exceptions and the registration helper `register_all_deployment_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from agents.deployment.cicd_pipeline_builder import (
    CiCdPipelineBuilder,
    CircleCiPipeline,
    GithubActionsPipeline,
    GitlabCiPipeline,
    JenkinsPipeline,
)
from agents.deployment.cloud_deployer import (
    AwsDeployer,
    AzureDeployer,
    CloudDeployer,
    GcpDeployer,
    MultiCloud,
)
from agents.deployment.deployment_orchestrator import DeploymentOrchestrator
from agents.deployment.docker_deployer import (
    DockerBuilder,
    DockerComposeDeployer,
    DockerDeployer,
    DockerPusher,
    DockerRunner,
)
from agents.deployment.environment_setup import (
    DevEnvironment,
    EnvironmentSetup,
    EnvironmentValidator,
    ProductionEnvironment,
    StagingEnvironment,
)
from agents.deployment.exceptions import (
    CICDError,
    CloudError,
    DeploymentError,
    DockerError,
    EnvironmentSetupError,
    HealthCheckDeploymentError,
    KubernetesError,
    PackageError,
    ReleaseError,
    RollbackError,
    SecretDeploymentError,
    SetupError,
    UpdateError,
    VersionError,
)
from agents.deployment.health_check_deployer import (
    HealthCheckDeployer,
    LivenessProbe,
    MetricsEndpoint,
    ReadinessProbe,
    StartupProbe,
)
from agents.deployment.k8s_deployer import (
    K8sApply,
    K8sDelete,
    K8sDeployer,
    K8sRollout,
    K8sScale,
)
from agents.deployment.package_builder import (
    DistributionPreparer,
    DockerImage,
    ExeBuilder,
    PackageBuilder,
    PythonPackage,
)
from agents.deployment.release_manager import (
    ReleaseCreator,
    ReleaseManager,
    ReleaseNotes,
    ReleasePublisher,
    ReleaseValidator,
)
from agents.deployment.rollback_manager import (
    RollbackExecutor,
    RollbackHistory,
    RollbackManager,
    RollbackPoint,
    RollbackVerifier,
)
from agents.deployment.secret_deployer import (
    AwsSecretsSetup,
    EncryptionSetup,
    K8sSecretsSetup,
    SecretDeployer,
    VaultSetup,
)
from agents.deployment.setup_script_generator import (
    ConfigScript,
    DependencyScript,
    InstallScript,
    SetupScriptGenerator,
    VerificationScript,
)
from agents.deployment.update_manager import (
    UpdateChecker,
    UpdateDownloader,
    UpdateInstaller,
    UpdateManager,
    UpdateVerifier,
)
from agents.deployment.version_manager import (
    VersionComparator,
    VersionHistory,
    VersionManager,
    VersionTagger,
    VersionUpdater,
)
from core.registry import AgentRegistry


logger = logging.getLogger("FractalCore.Deployment")

__all__ = [
    # Master Deployment Orchestrator
    "DeploymentOrchestrator",
    # Setup Script Generator
    "SetupScriptGenerator",
    "InstallScript",
    "ConfigScript",
    "DependencyScript",
    "VerificationScript",
    # Docker Deployer
    "DockerDeployer",
    "DockerBuilder",
    "DockerPusher",
    "DockerRunner",
    "DockerComposeDeployer",
    # K8s Deployer
    "K8sDeployer",
    "K8sApply",
    "K8sDelete",
    "K8sScale",
    "K8sRollout",
    # Cloud Deployer
    "CloudDeployer",
    "AwsDeployer",
    "GcpDeployer",
    "AzureDeployer",
    "MultiCloud",
    # Package Builder
    "PackageBuilder",
    "PythonPackage",
    "DockerImage",
    "ExeBuilder",
    "DistributionPreparer",
    # Version Manager
    "VersionManager",
    "VersionUpdater",
    "VersionTagger",
    "VersionComparator",
    "VersionHistory",
    # Release Manager
    "ReleaseManager",
    "ReleaseCreator",
    "ReleaseNotes",
    "ReleaseValidator",
    "ReleasePublisher",
    # Update Manager
    "UpdateManager",
    "UpdateChecker",
    "UpdateDownloader",
    "UpdateInstaller",
    "UpdateVerifier",
    # Rollback Manager
    "RollbackManager",
    "RollbackPoint",
    "RollbackExecutor",
    "RollbackVerifier",
    "RollbackHistory",
    # CI/CD Pipeline Builder
    "CiCdPipelineBuilder",
    "GithubActionsPipeline",
    "JenkinsPipeline",
    "GitlabCiPipeline",
    "CircleCiPipeline",
    # Environment Setup
    "EnvironmentSetup",
    "DevEnvironment",
    "StagingEnvironment",
    "ProductionEnvironment",
    "EnvironmentValidator",
    # Secret Deployer
    "SecretDeployer",
    "VaultSetup",
    "AwsSecretsSetup",
    "K8sSecretsSetup",
    "EncryptionSetup",
    # Health Check Deployer
    "HealthCheckDeployer",
    "LivenessProbe",
    "ReadinessProbe",
    "StartupProbe",
    "MetricsEndpoint",
    # Exceptions
    "DeploymentError",
    "SetupError",
    "DockerError",
    "KubernetesError",
    "CloudError",
    "PackageError",
    "VersionError",
    "ReleaseError",
    "UpdateError",
    "RollbackError",
    "CICDError",
    "EnvironmentSetupError",
    "SecretDeploymentError",
    "HealthCheckDeploymentError",
    # Registration Helper
    "register_all_deployment_agents",
]


def register_all_deployment_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Register all Deployment & Distribution layer agents into the central AgentRegistry.

    Args:
        registry: The central AgentRegistry singleton.
        parent_agent: Optional supervising orchestrator coordinator.
        max_depth: Global depth ceiling.

    Returns:
        Dict mapping root agent and count of registered agents.
    """
    logger.info("Registering all deployment & distribution domain agents into AgentRegistry...")

    deploy_orchestrator = DeploymentOrchestrator(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="DD1_DEPLOYMENT_ORCHESTRATOR",
        auto_spawn_subagents=True,
    )
    registry.register_agent(deploy_orchestrator)

    registered_count = 1

    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(deploy_orchestrator)

    logger.info("Successfully registered %d deployment & distribution domain agents into registry.", registered_count)
    return {
        "deploy_orchestrator": deploy_orchestrator,
        "total_registered": registered_count,
    }
