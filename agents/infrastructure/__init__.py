"""Infrastructure Domain Agents for the Fractal Multi-Agent Coding System.

Exports all 14 specialized infrastructure agents and atomic subagents across levels L3 to L5,
along with the registration helper `register_all_infrastructure_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from agents.infrastructure.backup_setuper import (
    BackupSetuper,
    DatabaseBackupGenerator,
    FileBackupGenerator,
    RecoveryPlanGenerator,
)
from agents.infrastructure.cicd_setuper import (
    CICDSetuper,
    GithubActionsGenerator,
    GitlabCiGenerator,
    JenkinsGenerator,
)
from agents.infrastructure.compose_generator import (
    ComposeGenerator,
    NetworkDefiner,
    ServiceDefiner,
    VolumeDefiner,
)
from agents.infrastructure.docker_configurer import (
    DockerConfigurer,
    DockerfileGenerator,
    MultiStageBuilder,
    OptimizationChecker,
)
from agents.infrastructure.environment_manager import (
    ConfigValidator,
    EnvironmentManager,
    EnvLoader,
    EnvTemplateGenerator,
)
from agents.infrastructure.exceptions import (
    BackupError,
    CICDError,
    ComposeError,
    DockerError,
    EnvironmentError,
    HealthCheckError,
    InfrastructureError,
    KubernetesError,
    LoadBalancerError,
    LoggingError,
    MonitoringError,
    NetworkError,
    SecretError,
    TerraformError,
)
from agents.infrastructure.health_check_designer import (
    HealthCheckDesigner,
    LivenessProbeGenerator,
    ReadinessProbeGenerator,
    StartupProbeGenerator,
)
from agents.infrastructure.infrastructure_orchestrator import InfrastructureOrchestrator
from agents.infrastructure.kubernetes_manifest_generator import (
    ConfigMapGenerator,
    DeploymentGenerator,
    IngressGenerator,
    KubernetesManifestGenerator,
    ServiceGenerator,
)
from agents.infrastructure.load_balancer_configurer import (
    AwsAlbGenerator,
    LoadBalancerConfigurer,
    NginxConfigGenerator,
    TraefikConfigGenerator,
)
from agents.infrastructure.logging_stack_setuper import (
    ElasticsearchConfigurer,
    KibanaConfigurer,
    LoggingStackSetuper,
    LogstashConfigurer,
)
from agents.infrastructure.monitoring_stack_setuper import (
    AlertManagerConfigurer,
    GrafanaDashboardGenerator,
    MonitoringStackSetuper,
    PrometheusConfigGenerator,
)
from agents.infrastructure.network_configurer import (
    FirewallRuleGenerator,
    NetworkConfigurer,
    ServiceMeshConfigurer,
    VpcConfigurer,
)
from agents.infrastructure.secret_manager import (
    AwsSecretsManager,
    EncryptionKeyGenerator,
    SecretManager,
    VaultConfigurer,
)
from agents.infrastructure.terraform_script_generator import (
    ProviderConfigurer,
    ResourceDefiner,
    StateManager,
    TerraformScriptGenerator,
)
from core.registry import AgentRegistry


logger = logging.getLogger("FractalCore.Infrastructure")

__all__ = [
    # Master Orchestrator
    "InfrastructureOrchestrator",
    # Docker
    "DockerConfigurer",
    "DockerfileGenerator",
    "MultiStageBuilder",
    "OptimizationChecker",
    # Compose
    "ComposeGenerator",
    "ServiceDefiner",
    "NetworkDefiner",
    "VolumeDefiner",
    # CI/CD
    "CICDSetuper",
    "GithubActionsGenerator",
    "JenkinsGenerator",
    "GitlabCiGenerator",
    # Environment
    "EnvironmentManager",
    "EnvTemplateGenerator",
    "ConfigValidator",
    "EnvLoader",
    # Kubernetes
    "KubernetesManifestGenerator",
    "DeploymentGenerator",
    "ServiceGenerator",
    "IngressGenerator",
    "ConfigMapGenerator",
    # Terraform
    "TerraformScriptGenerator",
    "ProviderConfigurer",
    "ResourceDefiner",
    "StateManager",
    # Health Checks
    "HealthCheckDesigner",
    "ReadinessProbeGenerator",
    "LivenessProbeGenerator",
    "StartupProbeGenerator",
    # Load Balancer
    "LoadBalancerConfigurer",
    "NginxConfigGenerator",
    "TraefikConfigGenerator",
    "AwsAlbGenerator",
    # Monitoring
    "MonitoringStackSetuper",
    "PrometheusConfigGenerator",
    "GrafanaDashboardGenerator",
    "AlertManagerConfigurer",
    # Logging
    "LoggingStackSetuper",
    "ElasticsearchConfigurer",
    "LogstashConfigurer",
    "KibanaConfigurer",
    # Secrets
    "SecretManager",
    "VaultConfigurer",
    "AwsSecretsManager",
    "EncryptionKeyGenerator",
    # Network
    "NetworkConfigurer",
    "FirewallRuleGenerator",
    "VpcConfigurer",
    "ServiceMeshConfigurer",
    # Backup
    "BackupSetuper",
    "DatabaseBackupGenerator",
    "FileBackupGenerator",
    "RecoveryPlanGenerator",
    # Exceptions
    "InfrastructureError",
    "DockerError",
    "ComposeError",
    "CICDError",
    "EnvironmentError",
    "KubernetesError",
    "TerraformError",
    "HealthCheckError",
    "LoadBalancerError",
    "MonitoringError",
    "LoggingError",
    "SecretError",
    "NetworkError",
    "BackupError",
    # Registration Helper
    "register_all_infrastructure_agents",
]


def register_all_infrastructure_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Register all infrastructure layer agents into the AgentRegistry.

    Args:
        registry: The central AgentRegistry singleton.
        parent_agent: Optional supervising deployment domain coordinator.
        max_depth: Global depth ceiling for infrastructure hierarchy.

    Returns:
        Dict mapping agent_id to instantiated agent instances.
    """
    logger.info("Registering all infrastructure domain agents into AgentRegistry...")

    # Root Infrastructure Orchestrator (L3)
    infra_orchestrator = InfrastructureOrchestrator(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="I1_INFRASTRUCTURE_ORCHESTRATOR",
        auto_spawn_subagents=True,
    )
    registry.register_agent(infra_orchestrator)

    # Register all spawned children recursively
    registered_count = 1
    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(infra_orchestrator)

    logger.info("Successfully registered %d infrastructure domain agents into registry.", registered_count)
    return {
        "infrastructure_orchestrator": infra_orchestrator,
        "total_registered": registered_count,
    }
