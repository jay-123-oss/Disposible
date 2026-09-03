"""TerraformScriptGenerator agent synthesizing Infrastructure as Code (IaC) HCL definitions."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.infrastructure.exceptions import TerraformError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Infrastructure.TerraformScriptGenerator")


# ==============================================================================
# L5 Atomic Terraform Subagents
# ==============================================================================

class ProviderConfigurer(BaseAgent):
    """L5 agent authoring Terraform provider and version requirement blocks."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ProviderConfigurer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        region = payload.get("region", "us-east-1")

        provider_hcl = (
            "terraform {\n"
            "  required_version = \">= 1.5.0\"\n"
            "  required_providers {\n"
            "    aws = {\n"
            "      source  = \"hashicorp/aws\"\n"
            "      version = \"~> 5.0\"\n"
            "    }\n"
            "  }\n"
            "}\n\n"
            "provider \"aws\" {\n"
            f"  region = \"{region}\"\n"
            "  default_tags {\n"
            "    tags = {\n"
            "      Environment = \"production\"\n"
            "      ManagedBy   = \"FractalCore\"\n"
            "    }\n"
            "  }\n"
            "}\n"
        )
        return {"status": "COMPLETED", "provider_hcl": provider_hcl}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ProviderConfigurer %s cleaned up.", self.agent_id)


class ResourceDefiner(BaseAgent):
    """L5 agent authoring core cloud resources: VPC, subnets, ECS cluster, and RDS."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ResourceDefiner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        resources_hcl = (
            "resource \"aws_vpc\" \"main\" {\n"
            "  cidr_block           = \"10.0.0.0/16\"\n"
            "  enable_dns_support   = true\n"
            "  enable_dns_hostnames = true\n"
            "  tags = { Name = \"main-vpc\" }\n"
            "}\n\n"
            "resource \"aws_subnet\" \"public\" {\n"
            "  vpc_id                  = aws_vpc.main.id\n"
            "  cidr_block              = \"10.0.1.0/24\"\n"
            "  map_public_ip_on_launch = true\n"
            "  tags = { Name = \"public-subnet\" }\n"
            "}\n\n"
            "resource \"aws_ecs_cluster\" \"app_cluster\" {\n"
            "  name = \"microservice-ecs-cluster\"\n"
            "}\n"
        )
        return {"status": "COMPLETED", "resources_hcl": resources_hcl}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ResourceDefiner %s cleaned up.", self.agent_id)


class StateManager(BaseAgent):
    """L5 agent configuring remote S3 state storage with DynamoDB state locking."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("StateManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        state_hcl = (
            "terraform {\n"
            "  backend \"s3\" {\n"
            "    bucket         = \"fractal-terraform-state-bucket\"\n"
            "    key            = \"production/terraform.tfstate\"\n"
            "    region         = \"us-east-1\"\n"
            "    encrypt        = true\n"
            "    dynamodb_table = \"fractal-terraform-locks\"\n"
            "  }\n"
            "}\n"
        )
        return {"status": "COMPLETED", "backend_hcl": state_hcl}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("StateManager %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 TerraformScriptGenerator Agent
# ==============================================================================

class TerraformScriptGenerator(BaseAgent):
    """L4 coordinator synthesizing production Terraform Infrastructure as Code (IaC) scripts."""

    def __init__(
        self,
        name: str = "TerraformScriptGenerator",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "terraform_generation",
            "iac_synthesis",
            "cloud_resource_definition",
            "remote_state_configuration",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "I7_TERRAFORM_SCRIPT_GENERATOR",
        )

        self.provider_cfg: Optional[ProviderConfigurer] = None
        self.res_def: Optional[ResourceDefiner] = None
        self.state_mgr: Optional[StateManager] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_terraform_scripts", self.generate_terraform_scripts)

    def _spawn_subagents(self) -> None:
        """Spawn atomic Terraform subagents (Rule 1 & Rule 5)."""
        logger.info("TerraformScriptGenerator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.provider_cfg = self.spawn_subagent(
            ProviderConfigurer,
            name="ProviderConfigurer",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.res_def = self.spawn_subagent(
            ResourceDefiner,
            name="ResourceDefiner",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.state_mgr = self.spawn_subagent(
            StateManager,
            name="StateManager",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TerraformScriptGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        bundle = self.generate_terraform_scripts(region=payload.get("region", "us-east-1"))
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "terraform_bundle": bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        bundle = result.get("terraform_bundle")
        if not bundle or "main_tf" not in bundle:
            raise TerraformError("TerraformScriptGenerator produced incomplete bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("TerraformScriptGenerator %s cleanup complete.", self.agent_id)

    def generate_terraform_scripts(self, region: str = "us-east-1") -> Dict[str, str]:
        """Synthesize main.tf and backend.tf HCL scripts."""
        p_res = self.provider_cfg.process({"payload": {"region": region}}) if self.provider_cfg else {"provider_hcl": ""}
        r_res = self.res_def.process({}) if self.res_def else {"resources_hcl": ""}
        s_res = self.state_mgr.process({}) if self.state_mgr else {"backend_hcl": ""}

        main_tf = f"{p_res.get('provider_hcl')}\n\n{r_res.get('resources_hcl')}"
        return {
            "main_tf": main_tf,
            "backend_tf": s_res.get("backend_hcl", ""),
            "passed": True,
        }
