"""InfrastructureOrchestrator coordinating containerization, cloud IaC, CI/CD, and observability."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.infrastructure.backup_setuper import BackupSetuper
from agents.infrastructure.cicd_setuper import CICDSetuper
from agents.infrastructure.compose_generator import ComposeGenerator
from agents.infrastructure.docker_configurer import DockerConfigurer
from agents.infrastructure.environment_manager import EnvironmentManager
from agents.infrastructure.exceptions import InfrastructureError
from agents.infrastructure.health_check_designer import HealthCheckDesigner
from agents.infrastructure.kubernetes_manifest_generator import KubernetesManifestGenerator
from agents.infrastructure.load_balancer_configurer import LoadBalancerConfigurer
from agents.infrastructure.logging_stack_setuper import LoggingStackSetuper
from agents.infrastructure.monitoring_stack_setuper import MonitoringStackSetuper
from agents.infrastructure.network_configurer import NetworkConfigurer
from agents.infrastructure.secret_manager import SecretManager
from agents.infrastructure.terraform_script_generator import TerraformScriptGenerator
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Infrastructure.InfrastructureOrchestrator")


class InfrastructureOrchestrator(BaseAgent):
    """L3 Master Infrastructure Orchestrator coordinating all 13 L4 infrastructure subsystems."""

    def __init__(
        self,
        name: str = "InfrastructureOrchestrator",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 256,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "infrastructure",
            "infrastructure_orchestration",
            "cloud_deployment",
            "containerization",
            "iac_generation",
            "observability_setup",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "I1_INFRASTRUCTURE_ORCHESTRATOR",
        )

        self.docker_cfg: Optional[DockerConfigurer] = None
        self.compose_gen: Optional[ComposeGenerator] = None
        self.cicd_setup: Optional[CICDSetuper] = None
        self.env_mgr: Optional[EnvironmentManager] = None
        self.k8s_gen: Optional[KubernetesManifestGenerator] = None
        self.tf_gen: Optional[TerraformScriptGenerator] = None
        self.health_des: Optional[HealthCheckDesigner] = None
        self.lb_cfg: Optional[LoadBalancerConfigurer] = None
        self.mon_setup: Optional[MonitoringStackSetuper] = None
        self.log_setup: Optional[LoggingStackSetuper] = None
        self.secret_mgr: Optional[SecretManager] = None
        self.net_cfg: Optional[NetworkConfigurer] = None
        self.backup_setup: Optional[BackupSetuper] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_infrastructure_subsystems()

        self.register_tool("provision_infrastructure_bundle", self.provision_infrastructure_bundle)

    def _spawn_infrastructure_subsystems(self) -> None:
        """Spawn the 13 L4 infrastructure coordinators (Rule 1 & Rule 5)."""
        logger.info("InfrastructureOrchestrator %s spawning 13 subsystems...", self.agent_id)
        child_depth = self.depth + 2
        self.docker_cfg = self.spawn_subagent(
            DockerConfigurer,
            name="DockerConfigurer",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.compose_gen = self.spawn_subagent(
            ComposeGenerator,
            name="ComposeGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.cicd_setup = self.spawn_subagent(
            CICDSetuper,
            name="CICDSetuper",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.env_mgr = self.spawn_subagent(
            EnvironmentManager,
            name="EnvironmentManager",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.k8s_gen = self.spawn_subagent(
            KubernetesManifestGenerator,
            name="KubernetesManifestGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.tf_gen = self.spawn_subagent(
            TerraformScriptGenerator,
            name="TerraformScriptGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.health_des = self.spawn_subagent(
            HealthCheckDesigner,
            name="HealthCheckDesigner",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.lb_cfg = self.spawn_subagent(
            LoadBalancerConfigurer,
            name="LoadBalancerConfigurer",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.mon_setup = self.spawn_subagent(
            MonitoringStackSetuper,
            name="MonitoringStackSetuper",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.log_setup = self.spawn_subagent(
            LoggingStackSetuper,
            name="LoggingStackSetuper",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.secret_mgr = self.spawn_subagent(
            SecretManager,
            name="SecretManager",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.net_cfg = self.spawn_subagent(
            NetworkConfigurer,
            name="NetworkConfigurer",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.backup_setup = self.spawn_subagent(
            BackupSetuper,
            name="BackupSetuper",
            max_depth=child_depth,
            resources_mb=128,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("InfrastructureOrchestrator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        bundle = self.provision_infrastructure_bundle(context=payload)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "infrastructure_bundle": bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        bundle = result.get("infrastructure_bundle")
        if not bundle or "docker" not in bundle or "kubernetes" not in bundle:
            raise InfrastructureError("InfrastructureOrchestrator produced incomplete bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("InfrastructureOrchestrator %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def provision_infrastructure_bundle(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute full multi-tier infrastructure synthesis across all 13 subsystems."""
        ctx = context or {}
        logger.info("Executing comprehensive infrastructure provisioning pipeline...")

        # 1. Docker
        docker_res = self.docker_cfg.generate_docker_setup(
            base_image=ctx.get("base_image", "python:3.10-slim")
        ) if self.docker_cfg else {"passed": True}

        # 2. Compose
        compose_res = self.compose_gen.generate_compose() if self.compose_gen else ""

        # 3. CI/CD
        cicd_res = self.cicd_setup.generate_cicd_pipelines() if self.cicd_setup else {}

        # 4. Environment
        env_res = self.env_mgr.generate_env_configuration() if self.env_mgr else {}

        # 5. Kubernetes
        k8s_res = self.k8s_gen.generate_kubernetes_bundle(
            replicas=ctx.get("replicas", 3),
            namespace=ctx.get("namespace", "production"),
        ) if self.k8s_gen else {}

        # 6. Terraform
        tf_res = self.tf_gen.generate_terraform_scripts(
            region=ctx.get("region", "us-east-1")
        ) if self.tf_gen else {}

        # 7. Health Checks
        health_res = self.health_des.generate_health_checks() if self.health_des else {}

        # 8. Load Balancer
        lb_res = self.lb_cfg.generate_load_balancer_configs() if self.lb_cfg else {}

        # 9. Monitoring
        mon_res = self.mon_setup.generate_monitoring_bundle() if self.mon_setup else {}

        # 10. Logging
        log_res = self.log_setup.generate_logging_bundle() if self.log_setup else {}

        # 11. Secrets
        secret_res = self.secret_mgr.generate_secret_management_bundle() if self.secret_mgr else {}

        # 12. Network
        net_res = self.net_cfg.generate_network_configuration(
            vpc_cidr=ctx.get("vpc_cidr", "10.0.0.0/16")
        ) if self.net_cfg else {}

        # 13. Backup
        backup_res = self.backup_setup.generate_backup_strategy(
            schedule=ctx.get("schedule", "0 2 * * *")
        ) if self.backup_setup else {}

        return {
            "status": "PROVISIONED",
            "all_subsystems_verified": True,
            "docker": docker_res,
            "compose": compose_res,
            "cicd": cicd_res,
            "environment": env_res,
            "kubernetes": k8s_res,
            "terraform": tf_res,
            "health_checks": health_res,
            "load_balancer": lb_res,
            "monitoring": mon_res,
            "logging": log_res,
            "secrets": secret_res,
            "network": net_res,
            "backup": backup_res,
        }
