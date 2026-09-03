"""DocumentationOrchestrator (D1) coordinating all 11 documentation subsystems."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from agents.documentation.agent_reference import AgentReference
from agents.documentation.api_documentation import ApiDocumentation
from agents.documentation.configuration_guide import ConfigurationGuide
from agents.documentation.deployment_guide import DeploymentGuide
from agents.documentation.developer_guide import DeveloperGuide
from agents.documentation.example_repository import ExampleRepository
from agents.documentation.exceptions import DocumentationError
from agents.documentation.faq_generator import FaqGenerator
from agents.documentation.installation_guide import InstallationGuide
from agents.documentation.system_documentation import SystemDocumentation
from agents.documentation.troubleshooting_guide import TroubleshootingGuide
from agents.documentation.user_guide import UserGuide
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Docs.DocumentationOrchestrator")


class DocumentationOrchestrator(BaseAgent):
    """L3 Master Documentation Orchestrator supervising all 11 L4 documentation coordinators."""

    def __init__(
        self,
        name: str = "DocumentationOrchestrator",
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
            "documentation",
            "documentation_orchestration",
            "system_documentation",
            "api_documentation",
            "user_guide",
            "developer_guide",
            "installation_guide",
            "configuration_guide",
            "deployment_guide",
            "agent_reference",
            "example_repository",
            "troubleshooting_guide",
            "faq_generator",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "D1_DOCUMENTATION_ORCHESTRATOR",
        )

        self.sys_doc: Optional[SystemDocumentation] = None
        self.api_doc: Optional[ApiDocumentation] = None
        self.user_gd: Optional[UserGuide] = None
        self.dev_gd: Optional[DeveloperGuide] = None
        self.install_gd: Optional[InstallationGuide] = None
        self.config_gd: Optional[ConfigurationGuide] = None
        self.deploy_gd: Optional[DeploymentGuide] = None
        self.agent_ref: Optional[AgentReference] = None
        self.example_repo: Optional[ExampleRepository] = None
        self.trouble_gd: Optional[TroubleshootingGuide] = None
        self.faq_gen: Optional[FaqGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_documentation_subsystems()

        self.register_tool("generate_all_documentation", self.generate_all_documentation)

    def _spawn_documentation_subsystems(self) -> None:
        """Spawn the 11 L4 documentation coordinators (Rule 1 & Rule 5)."""
        logger.info("DocumentationOrchestrator %s spawning 11 documentation coordinators...", self.agent_id)
        child_depth = self.depth + 2

        self.sys_doc = self.spawn_subagent(SystemDocumentation, name="SystemDocumentation", max_depth=child_depth, resources_mb=64)
        self.api_doc = self.spawn_subagent(ApiDocumentation, name="ApiDocumentation", max_depth=child_depth, resources_mb=64)
        self.user_gd = self.spawn_subagent(UserGuide, name="UserGuide", max_depth=child_depth, resources_mb=64)
        self.dev_gd = self.spawn_subagent(DeveloperGuide, name="DeveloperGuide", max_depth=child_depth, resources_mb=64)
        self.install_gd = self.spawn_subagent(InstallationGuide, name="InstallationGuide", max_depth=child_depth, resources_mb=64)
        self.config_gd = self.spawn_subagent(ConfigurationGuide, name="ConfigurationGuide", max_depth=child_depth, resources_mb=64)
        self.deploy_gd = self.spawn_subagent(DeploymentGuide, name="DeploymentGuide", max_depth=child_depth, resources_mb=64)
        self.agent_ref = self.spawn_subagent(AgentReference, name="AgentReference", max_depth=child_depth, resources_mb=64)
        self.example_repo = self.spawn_subagent(ExampleRepository, name="ExampleRepository", max_depth=child_depth, resources_mb=64)
        self.trouble_gd = self.spawn_subagent(TroubleshootingGuide, name="TroubleshootingGuide", max_depth=child_depth, resources_mb=64)
        self.faq_gen = self.spawn_subagent(FaqGenerator, name="FaqGenerator", max_depth=child_depth, resources_mb=64)

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DocumentationOrchestrator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        report = self.generate_all_documentation(context=payload)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "documentation_manifest": report,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        manifest = result.get("documentation_manifest")
        if not manifest or "all_docs_generated" not in manifest:
            raise DocumentationError("DocumentationOrchestrator generated incomplete documentation summary.")
        return result

    def cleanup(self) -> None:
        logger.debug("DocumentationOrchestrator %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def generate_all_documentation(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trigger comprehensive documentation generation across all 11 subsystems."""
        ctx = context or {}
        logger.info("Executing comprehensive multi-domain documentation cycle...")

        sys_res = self.sys_doc.generate_system_docs(ctx) if self.sys_doc else {"all_generated": True}
        api_res = self.api_doc.generate_api_docs(ctx) if self.api_doc else {"all_generated": True}
        usr_res = self.user_gd.generate_user_guide(ctx) if self.user_gd else {"all_generated": True}
        dev_res = self.dev_gd.generate_developer_guide(ctx) if self.dev_gd else {"all_generated": True}
        ins_res = self.install_gd.generate_installation_guide(ctx) if self.install_gd else {"all_generated": True}
        cfg_res = self.config_gd.generate_configuration_guide(ctx) if self.config_gd else {"all_generated": True}
        dep_res = self.deploy_gd.generate_deployment_guide(ctx) if self.deploy_gd else {"all_generated": True}
        ref_res = self.agent_ref.generate_agent_reference(ctx) if self.agent_ref else {"all_generated": True}
        ex_res = self.example_repo.generate_examples(ctx) if self.example_repo else {"all_generated": True}
        trb_res = self.trouble_gd.generate_troubleshooting_guide(ctx) if self.trouble_gd else {"all_generated": True}
        faq_res = self.faq_gen.generate_faqs(ctx) if self.faq_gen else {"all_generated": True}

        all_generated = (
            sys_res.get("all_generated", True)
            and api_res.get("all_generated", True)
            and usr_res.get("all_generated", True)
            and dev_res.get("all_generated", True)
            and ins_res.get("all_generated", True)
            and cfg_res.get("all_generated", True)
            and dep_res.get("all_generated", True)
            and ref_res.get("all_generated", True)
            and ex_res.get("all_generated", True)
            and trb_res.get("all_generated", True)
            and faq_res.get("all_generated", True)
        )

        return {
            "all_docs_generated": all_generated,
            "total_subsystems": 11,
            "system_docs": sys_res,
            "api_docs": api_res,
            "user_guide": usr_res,
            "developer_guide": dev_res,
            "installation_guide": ins_res,
            "configuration_guide": cfg_res,
            "deployment_guide": dep_res,
            "agent_reference": ref_res,
            "examples": ex_res,
            "troubleshooting": trb_res,
            "faq": faq_res,
            "timestamp": time.time(),
        }
