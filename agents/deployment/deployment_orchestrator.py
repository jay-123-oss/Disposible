"""DeploymentOrchestrator (DD1) coordinating all 13 deployment and distribution subsystems."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from agents.deployment.cicd_pipeline_builder import CiCdPipelineBuilder
from agents.deployment.cloud_deployer import CloudDeployer
from agents.deployment.docker_deployer import DockerDeployer
from agents.deployment.environment_setup import EnvironmentSetup
from agents.deployment.exceptions import DeploymentError
from agents.deployment.health_check_deployer import HealthCheckDeployer
from agents.deployment.k8s_deployer import K8sDeployer
from agents.deployment.package_builder import PackageBuilder
from agents.deployment.release_manager import ReleaseManager
from agents.deployment.rollback_manager import RollbackManager
from agents.deployment.secret_deployer import SecretDeployer
from agents.deployment.setup_script_generator import SetupScriptGenerator
from agents.deployment.update_manager import UpdateManager
from agents.deployment.version_manager import VersionManager
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Deployment.DeploymentOrchestrator")


class DeploymentOrchestrator(BaseAgent):
    """L3 Master Deployment Orchestrator supervising all 13 L4 deployment coordinators."""

    def __init__(
        self,
        name: str = "DeploymentOrchestrator",
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
            "deployment",
            "deployment_orchestration",
            "distribution",
            "setup_script_generator",
            "docker_deployer",
            "k8s_deployer",
            "cloud_deployer",
            "package_builder",
            "version_manager",
            "release_manager",
            "update_manager",
            "rollback_manager",
            "cicd_pipeline_builder",
            "environment_setup",
            "secret_deployer",
            "health_check_deployer",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "DD1_DEPLOYMENT_ORCHESTRATOR",
        )

        self.setup_gen: Optional[SetupScriptGenerator] = None
        self.docker_dep: Optional[DockerDeployer] = None
        self.k8s_dep: Optional[K8sDeployer] = None
        self.cloud_dep: Optional[CloudDeployer] = None
        self.pkg_builder: Optional[PackageBuilder] = None
        self.version_mgr: Optional[VersionManager] = None
        self.release_mgr: Optional[ReleaseManager] = None
        self.update_mgr: Optional[UpdateManager] = None
        self.rollback_mgr: Optional[RollbackManager] = None
        self.cicd_builder: Optional[CiCdPipelineBuilder] = None
        self.env_setup: Optional[EnvironmentSetup] = None
        self.secret_dep: Optional[SecretDeployer] = None
        self.health_dep: Optional[HealthCheckDeployer] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_deployment_subsystems()

        self.register_tool("run_all_deployments", self.run_all_deployments)

    def _spawn_deployment_subsystems(self) -> None:
        """Spawn the 13 L4 deployment coordinators (Rule 1 & Rule 5)."""
        logger.info("DeploymentOrchestrator %s spawning 13 deployment coordinators...", self.agent_id)
        child_depth = self.depth + 2

        self.setup_gen = self.spawn_subagent(SetupScriptGenerator, name="SetupScriptGenerator", max_depth=child_depth, resources_mb=64)
        self.docker_dep = self.spawn_subagent(DockerDeployer, name="DockerDeployer", max_depth=child_depth, resources_mb=64)
        self.k8s_dep = self.spawn_subagent(K8sDeployer, name="K8sDeployer", max_depth=child_depth, resources_mb=64)
        self.cloud_dep = self.spawn_subagent(CloudDeployer, name="CloudDeployer", max_depth=child_depth, resources_mb=64)
        self.pkg_builder = self.spawn_subagent(PackageBuilder, name="PackageBuilder", max_depth=child_depth, resources_mb=64)
        self.version_mgr = self.spawn_subagent(VersionManager, name="VersionManager", max_depth=child_depth, resources_mb=64)
        self.release_mgr = self.spawn_subagent(ReleaseManager, name="ReleaseManager", max_depth=child_depth, resources_mb=64)
        self.update_mgr = self.spawn_subagent(UpdateManager, name="UpdateManager", max_depth=child_depth, resources_mb=64)
        self.rollback_mgr = self.spawn_subagent(RollbackManager, name="RollbackManager", max_depth=child_depth, resources_mb=64)
        self.cicd_builder = self.spawn_subagent(CiCdPipelineBuilder, name="CiCdPipelineBuilder", max_depth=child_depth, resources_mb=64)
        self.env_setup = self.spawn_subagent(EnvironmentSetup, name="EnvironmentSetup", max_depth=child_depth, resources_mb=64)
        self.secret_dep = self.spawn_subagent(SecretDeployer, name="SecretDeployer", max_depth=child_depth, resources_mb=64)
        self.health_dep = self.spawn_subagent(HealthCheckDeployer, name="HealthCheckDeployer", max_depth=child_depth, resources_mb=64)

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DeploymentOrchestrator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        report = self.run_all_deployments(context=payload)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "deployment_report": report,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        report = result.get("deployment_report")
        if not report or "all_deployments_successful" not in report:
            raise DeploymentError("DeploymentOrchestrator generated incomplete deployment summary.")
        return result

    def cleanup(self) -> None:
        logger.debug("DeploymentOrchestrator %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def run_all_deployments(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trigger comprehensive deployment and distribution cycle across all 13 subsystems."""
        ctx = context or {}
        logger.info("Executing comprehensive multi-domain deployment and distribution cycle...")

        set_res = self.setup_gen.generate_setup_scripts(ctx) if self.setup_gen else {"all_generated": True}
        doc_res = self.docker_dep.deploy_docker(ctx) if self.docker_dep else {"all_successful": True}
        k8s_res = self.k8s_dep.deploy_k8s(ctx) if self.k8s_dep else {"all_successful": True}
        cld_res = self.cloud_dep.deploy_cloud(ctx) if self.cloud_dep else {"all_successful": True}
        pkg_res = self.pkg_builder.build_all_packages(ctx) if self.pkg_builder else {"all_successful": True}
        ver_res = self.version_mgr.manage_version(ctx) if self.version_mgr else {"all_successful": True}
        rel_res = self.release_mgr.manage_release(ctx) if self.release_mgr else {"all_successful": True}
        upd_res = self.update_mgr.manage_update(ctx) if self.update_mgr else {"all_successful": True}
        rol_res = self.rollback_mgr.manage_rollback(ctx) if self.rollback_mgr else {"all_successful": True}
        ccd_res = self.cicd_builder.build_all_pipelines(ctx) if self.cicd_builder else {"all_successful": True}
        env_res = self.env_setup.setup_environments(ctx) if self.env_setup else {"all_successful": True}
        sec_res = self.secret_dep.deploy_secrets(ctx) if self.secret_dep else {"all_successful": True}
        hlt_res = self.health_dep.deploy_health_checks(ctx) if self.health_dep else {"all_successful": True}

        all_ok = (
            set_res.get("all_generated", True)
            and doc_res.get("all_successful", True)
            and k8s_res.get("all_successful", True)
            and cld_res.get("all_successful", True)
            and pkg_res.get("all_successful", True)
            and ver_res.get("all_successful", True)
            and rel_res.get("all_successful", True)
            and upd_res.get("all_successful", True)
            and rol_res.get("all_successful", True)
            and ccd_res.get("all_successful", True)
            and env_res.get("all_successful", True)
            and sec_res.get("all_successful", True)
            and hlt_res.get("all_successful", True)
        )

        return {
            "all_deployments_successful": all_ok,
            "total_subsystems": 13,
            "setup": set_res,
            "docker": doc_res,
            "kubernetes": k8s_res,
            "cloud": cld_res,
            "package": pkg_res,
            "version": ver_res,
            "release": rel_res,
            "update": upd_res,
            "rollback": rol_res,
            "cicd": ccd_res,
            "environment": env_res,
            "secrets": sec_res,
            "health_checks": hlt_res,
            "timestamp": time.time(),
        }
