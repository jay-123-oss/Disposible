"""AgentFactory agent orchestrating the instantiation of domain agents across all 8 specialized layers."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from integration.exceptions import AgentFactoryError


logger = logging.getLogger("FractalCore.Integration.AgentFactory")


# ==============================================================================
# L5 Atomic Agent Factory Creators (8 Domains)
# ==============================================================================

class PlanningAgentCreator(BaseAgent):
    """L5 agent instantiating Planning domain agents."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PlanningAgentCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        registry = payload.get("registry")
        count = 0
        if registry:
            from agents.planning import register_all_planning_agents
            res = register_all_planning_agents(registry)
            count = res.get("total_registered", 0)

        return {"status": "COMPLETED", "domain": "planning", "created_count": count}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PlanningAgentCreator %s cleaned up.", self.agent_id)


class CodingAgentCreator(BaseAgent):
    """L5 agent instantiating Coding domain agents."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CodingAgentCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        registry = payload.get("registry")
        count = 0
        if registry:
            from agents.coding import register_all_coding_agents
            res = register_all_coding_agents(registry)
            count = res.get("total_registered", 0)

        return {"status": "COMPLETED", "domain": "coding", "created_count": count}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CodingAgentCreator %s cleaned up.", self.agent_id)


class TestingAgentCreator(BaseAgent):
    """L5 agent instantiating Testing domain agents."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TestingAgentCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        registry = payload.get("registry")
        count = 0
        if registry:
            from agents.testing import register_all_testing_agents
            res = register_all_testing_agents(registry)
            count = res.get("total_registered", 0)

        return {"status": "COMPLETED", "domain": "testing", "created_count": count}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TestingAgentCreator %s cleaned up.", self.agent_id)


class SecurityAgentCreator(BaseAgent):
    """L5 agent instantiating Security domain agents."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SecurityAgentCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        registry = payload.get("registry")
        count = 0
        if registry:
            from agents.security import register_all_security_agents
            res = register_all_security_agents(registry)
            count = res.get("total_registered", 0)

        return {"status": "COMPLETED", "domain": "security", "created_count": count}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SecurityAgentCreator %s cleaned up.", self.agent_id)


class QualityAgentCreator(BaseAgent):
    """L5 agent instantiating Quality domain agents."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("QualityAgentCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        registry = payload.get("registry")
        count = 0
        if registry:
            from agents.quality import register_all_quality_agents
            res = register_all_quality_agents(registry)
            count = res.get("total_registered", 0)

        return {"status": "COMPLETED", "domain": "quality", "created_count": count}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("QualityAgentCreator %s cleaned up.", self.agent_id)


class InfrastructureAgentCreator(BaseAgent):
    """L5 agent instantiating Infrastructure domain agents."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("InfrastructureAgentCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        registry = payload.get("registry")
        count = 0
        if registry:
            from agents.infrastructure import register_all_infrastructure_agents
            res = register_all_infrastructure_agents(registry)
            count = res.get("total_registered", 0)

        return {"status": "COMPLETED", "domain": "infrastructure", "created_count": count}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("InfrastructureAgentCreator %s cleaned up.", self.agent_id)


class CommStateAgentCreator(BaseAgent):
    """L5 agent instantiating Communication & State domain agents."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CommStateAgentCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        registry = payload.get("registry")
        count = 0
        if registry:
            from agents.commstate import register_all_commstate_agents
            res = register_all_commstate_agents(registry)
            count = res.get("total_registered", 0)

        return {"status": "COMPLETED", "domain": "commstate", "created_count": count}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CommStateAgentCreator %s cleaned up.", self.agent_id)


class MonitoringAgentCreator(BaseAgent):
    """L5 agent instantiating Monitoring & Observability domain agents."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MonitoringAgentCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        registry = payload.get("registry")
        count = 0
        if registry:
            from agents.monitoring import register_all_monitoring_agents
            res = register_all_monitoring_agents(registry)
            count = res.get("total_registered", 0)

        return {"status": "COMPLETED", "domain": "monitoring", "created_count": count}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("MonitoringAgentCreator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 AgentFactory Agent
# ==============================================================================

class AgentFactory(BaseAgent):
    """L4 coordinator overseeing agent factory creators across all 8 functional domains."""

    def __init__(
        self,
        name: str = "AgentFactory",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "agent_factory",
            "agent_creation",
            "cross_domain_instantiation",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "IA3_AGENT_FACTORY",
        )

        self.plan_creator: Optional[PlanningAgentCreator] = None
        self.code_creator: Optional[CodingAgentCreator] = None
        self.test_creator: Optional[TestingAgentCreator] = None
        self.sec_creator: Optional[SecurityAgentCreator] = None
        self.qual_creator: Optional[QualityAgentCreator] = None
        self.infra_creator: Optional[InfrastructureAgentCreator] = None
        self.comm_creator: Optional[CommStateAgentCreator] = None
        self.mon_creator: Optional[MonitoringAgentCreator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("create_domain_agents", self.create_domain_agents)

    def _spawn_subagents(self) -> None:
        """Spawn atomic agent factory creators across all 8 domains (Rule 1 & Rule 5)."""
        logger.info("AgentFactory %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.plan_creator = self.spawn_subagent(PlanningAgentCreator, name="PlanningAgentCreator", max_depth=child_depth, resources_mb=32)
        self.code_creator = self.spawn_subagent(CodingAgentCreator, name="CodingAgentCreator", max_depth=child_depth, resources_mb=32)
        self.test_creator = self.spawn_subagent(TestingAgentCreator, name="TestingAgentCreator", max_depth=child_depth, resources_mb=32)
        self.sec_creator = self.spawn_subagent(SecurityAgentCreator, name="SecurityAgentCreator", max_depth=child_depth, resources_mb=32)
        self.qual_creator = self.spawn_subagent(QualityAgentCreator, name="QualityAgentCreator", max_depth=child_depth, resources_mb=32)
        self.infra_creator = self.spawn_subagent(InfrastructureAgentCreator, name="InfrastructureAgentCreator", max_depth=child_depth, resources_mb=32)
        self.comm_creator = self.spawn_subagent(CommStateAgentCreator, name="CommStateAgentCreator", max_depth=child_depth, resources_mb=32)
        self.mon_creator = self.spawn_subagent(MonitoringAgentCreator, name="MonitoringAgentCreator", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AgentFactory %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        domain = payload.get("domain", "all")
        registry = payload.get("registry")
        res = self.create_domain_agents(domain=domain, registry=registry)
        return {"status": "COMPLETED", "creation_results": res}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AgentFactory %s cleanup complete.", self.agent_id)

    def create_domain_agents(self, domain: str = "all", registry: Any = None) -> Dict[str, Any]:
        """Instantiate domain agents for requested domain or all domains."""
        p_env = {"payload": {"registry": registry}}
        results = {}

        creators = {
            "planning": self.plan_creator,
            "coding": self.code_creator,
            "testing": self.test_creator,
            "security": self.sec_creator,
            "quality": self.qual_creator,
            "infrastructure": self.infra_creator,
            "commstate": self.comm_creator,
            "monitoring": self.mon_creator,
        }

        for dom, creator in creators.items():
            if domain in ("all", dom) and creator:
                res = creator.process(p_env)
                results[dom] = res.get("created_count", 0)

        return results
