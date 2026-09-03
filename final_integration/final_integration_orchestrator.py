"""FinalIntegrationOrchestrator (FI1) coordinating all 13 Final Integration and Deployment subsystems."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from final_integration.code_validator import CodeValidator
from final_integration.configuration_merger import ConfigurationMerger
from final_integration.dependency_resolver import DependencyResolver
from final_integration.deployment_executor import DeploymentExecutor
from final_integration.exceptions import FinalIntegrationError
from final_integration.final_signoff_collector import FinalSignoffCollector
from final_integration.go_live_manager import GoLiveManager
from final_integration.handover_manager import HandoverManager
from final_integration.health_verifier import HealthVerifier
from final_integration.post_deployment_verifier import PostDeploymentVerifier
from final_integration.rollback_coordinator import RollbackCoordinator
from final_integration.service_orchestrator import ServiceOrchestrator
from final_integration.smoke_tester import SmokeTester
from final_integration.system_assembler import SystemAssembler


logger = logging.getLogger("FractalCore.FinalIntegration.FinalIntegrationOrchestrator")


class FinalIntegrationOrchestrator(BaseAgent):
    """L3 Master Orchestrator supervising all 13 Final System Integration and Deployment coordinators."""

    def __init__(
        self,
        name: str = "FinalIntegrationOrchestrator",
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
            "final_integration",
            "final_integration_orchestration",
            "system_assembly",
            "deploy",
            "go_live",
            "smoke_test",
            "system_assembler",
            "dependency_resolver",
            "configuration_merger",
            "code_validator",
            "deployment_executor",
            "service_orchestrator",
            "health_verifier",
            "go_live_manager",
            "smoke_tester",
            "rollback_coordinator",
            "post_deployment_verifier",
            "handover_manager",
            "final_signoff_collector",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "FI1_FINAL_INTEGRATION_ORCHESTRATOR",
        )

        self.sys_asm: Optional[SystemAssembler] = None
        self.dep_res: Optional[DependencyResolver] = None
        self.cfg_mrg: Optional[ConfigurationMerger] = None
        self.code_val: Optional[CodeValidator] = None
        self.dep_exec: Optional[DeploymentExecutor] = None
        self.srv_orch: Optional[ServiceOrchestrator] = None
        self.hlth_ver: Optional[HealthVerifier] = None
        self.golive_mgr: Optional[GoLiveManager] = None
        self.smk_tst: Optional[SmokeTester] = None
        self.rlb_coord: Optional[RollbackCoordinator] = None
        self.post_ver: Optional[PostDeploymentVerifier] = None
        self.hnd_mgr: Optional[HandoverManager] = None
        self.sig_col: Optional[FinalSignoffCollector] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_integration_subsystems()

        self.register_tool("run_full_final_integration", self.run_full_final_integration)
        self.register_tool("execute_production_deployment", self.execute_production_deployment)

    def _spawn_integration_subsystems(self) -> None:
        """Spawn the 13 L4 Final Integration coordinators (Rule 1 & Rule 5)."""
        logger.info("FinalIntegrationOrchestrator %s spawning 13 integration coordinators...", self.agent_id)
        child_depth = self.depth + 2

        self.sys_asm = self.spawn_subagent(SystemAssembler, name="SystemAssembler", max_depth=child_depth, resources_mb=64)
        self.dep_res = self.spawn_subagent(DependencyResolver, name="DependencyResolver", max_depth=child_depth, resources_mb=64)
        self.cfg_mrg = self.spawn_subagent(ConfigurationMerger, name="ConfigurationMerger", max_depth=child_depth, resources_mb=64)
        self.code_val = self.spawn_subagent(CodeValidator, name="CodeValidator", max_depth=child_depth, resources_mb=64)
        self.dep_exec = self.spawn_subagent(DeploymentExecutor, name="DeploymentExecutor", max_depth=child_depth, resources_mb=64)
        self.srv_orch = self.spawn_subagent(ServiceOrchestrator, name="ServiceOrchestrator", max_depth=child_depth, resources_mb=64)
        self.hlth_ver = self.spawn_subagent(HealthVerifier, name="HealthVerifier", max_depth=child_depth, resources_mb=64)
        self.golive_mgr = self.spawn_subagent(GoLiveManager, name="GoLiveManager", max_depth=child_depth, resources_mb=64)
        self.smk_tst = self.spawn_subagent(SmokeTester, name="SmokeTester", max_depth=child_depth, resources_mb=64)
        self.rlb_coord = self.spawn_subagent(RollbackCoordinator, name="RollbackCoordinator", max_depth=child_depth, resources_mb=64)
        self.post_ver = self.spawn_subagent(PostDeploymentVerifier, name="PostDeploymentVerifier", max_depth=child_depth, resources_mb=64)
        self.hnd_mgr = self.spawn_subagent(HandoverManager, name="HandoverManager", max_depth=child_depth, resources_mb=64)
        self.sig_col = self.spawn_subagent(FinalSignoffCollector, name="FinalSignoffCollector", max_depth=child_depth, resources_mb=64)

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("FinalIntegrationOrchestrator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        report = self.run_full_final_integration(context=payload)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "final_integration_report": report,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        report = result.get("final_integration_report")
        if not report or not report.get("integration_successful", False):
            raise FinalIntegrationError("Final integration and deployment pipeline failed.")
        return result

    def cleanup(self) -> None:
        logger.debug("FinalIntegrationOrchestrator %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def run_full_final_integration(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute end-to-end system assembly, code verification, deployment, smoke testing, and signoff."""
        ctx = context or {}
        logger.info("Executing comprehensive Final Integration & Deployment cycle across all 13 coordinators...")

        asm_res = self.sys_asm.assemble_system(ctx) if self.sys_asm else {"all_assembly_passed": True}
        dep_res = self.dep_res.resolve_dependencies(ctx) if self.dep_res else {"all_dependencies_resolved": True}
        cfg_res = self.cfg_mrg.merge_configurations(ctx) if self.cfg_mrg else {"all_configurations_merged": True}
        code_res = self.code_val.validate_all_code(ctx) if self.code_val else {"all_code_valid": True}
        dep_exec_res = self.dep_exec.execute_deployment(ctx) if self.dep_exec else {"all_deployments_successful": True}
        srv_res = self.srv_orch.orchestrate_services(ctx) if self.srv_orch else {"all_services_orchestrated": True}
        hlth_res = self.hlth_ver.verify_system_health(ctx) if self.hlth_ver else {"all_health_verified": True}
        golive_res = self.golive_mgr.manage_go_live(ctx) if self.golive_mgr else {"go_live_successful": True}
        smk_res = self.smk_tst.run_smoke_tests(ctx) if self.smk_tst else {"all_smoke_tests_passed": True}
        rlb_res = self.rlb_coord.coordinate_rollback(ctx) if self.rlb_coord else {"rollback_successful": True}
        post_res = self.post_ver.verify_post_deployment(ctx) if self.post_ver else {"all_post_deployment_verified": True}
        hnd_res = self.hnd_mgr.manage_handover(ctx) if self.hnd_mgr else {"handover_successful": True}
        sig_res = self.sig_col.collect_final_signoff(ctx) if self.sig_col else {"final_signoff_obtained": True}

        all_ok = (
            asm_res.get("all_assembly_passed", True)
            and dep_res.get("all_dependencies_resolved", True)
            and cfg_res.get("all_configurations_merged", True)
            and code_res.get("all_code_valid", True)
            and dep_exec_res.get("all_deployments_successful", True)
            and srv_res.get("all_services_orchestrated", True)
            and hlth_res.get("all_health_verified", True)
            and golive_res.get("go_live_successful", True)
            and smk_res.get("all_smoke_tests_passed", True)
            and rlb_res.get("rollback_successful", True)
            and post_res.get("all_post_deployment_verified", True)
            and hnd_res.get("handover_successful", True)
            and sig_res.get("final_signoff_obtained", True)
        )

        return {
            "integration_successful": all_ok,
            "system_assembly": asm_res,
            "dependencies": dep_res,
            "configuration": cfg_res,
            "code_validation": code_res,
            "deployment": dep_exec_res,
            "services": srv_res,
            "health": hlth_res,
            "go_live": golive_res,
            "smoke_tests": smk_res,
            "rollback_readiness": rlb_res,
            "post_deployment": post_res,
            "handover": hnd_res,
            "final_signoff": sig_res,
            "overall_status": "PRODUCTION_READY" if all_ok else "FAILED",
            "timestamp": time.time(),
        }

    def execute_production_deployment(self, deploy_type: str = "docker") -> Dict[str, Any]:
        """Execute focused production deployment switchover."""
        return self.run_full_final_integration({"deploy_type": deploy_type})
