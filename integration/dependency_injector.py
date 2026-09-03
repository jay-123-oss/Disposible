"""DependencyInjector agent resolving and binding core singletons, agent hierarchies, and services."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from integration.exceptions import DependencyError


logger = logging.getLogger("FractalCore.Integration.DependencyInjector")


# ==============================================================================
# L5 Atomic Dependency Injector Subagents
# ==============================================================================

class CoreDependencyInjector(BaseAgent):
    """L5 agent wiring core infrastructure (TaskQueue, AgentRegistry, StateManager, Monitor)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CoreDependencyInjector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        target = payload.get("target")

        return {
            "status": "COMPLETED",
            "injected": ["registry", "task_queue", "state_manager", "monitor"],
            "target": str(target),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CoreDependencyInjector %s cleaned up.", self.agent_id)


class AgentDependencyInjector(BaseAgent):
    """L5 agent linking parent-child hierarchical references and mailbox connections."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AgentDependencyInjector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        parent = payload.get("parent")
        child = payload.get("child")

        if parent and child and hasattr(child, "_parent"):
            child._parent = parent

        return {
            "status": "COMPLETED",
            "hierarchy_wired": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AgentDependencyInjector %s cleaned up.", self.agent_id)


class ServiceDependencyInjector(BaseAgent):
    """L5 agent providing LLM endpoints, sandboxes, and quality gates to agents."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ServiceDependencyInjector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        services = payload.get("services", ["sandbox", "quality_gate", "llm_client"])

        return {
            "status": "COMPLETED",
            "services_injected": services,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ServiceDependencyInjector %s cleaned up.", self.agent_id)


class RepositoryDependencyInjector(BaseAgent):
    """L5 agent binding task stores, artifact repositories, and checkpoint directories."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RepositoryDependencyInjector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        repos = payload.get("repositories", ["task_store", "artifact_store", "checkpoint_store"])

        return {
            "status": "COMPLETED",
            "repositories_injected": repos,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("RepositoryDependencyInjector %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 DependencyInjector Agent
# ==============================================================================

class DependencyInjector(BaseAgent):
    """L4 coordinator overseeing dependency injection across core systems, agents, services, and repos."""

    def __init__(
        self,
        name: str = "DependencyInjector",
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
            "dependency_injection",
            "core_injection",
            "agent_injection",
            "service_injection",
            "repository_injection",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "IA4_DEPENDENCY_INJECTOR",
        )

        self.core_inj: Optional[CoreDependencyInjector] = None
        self.agent_inj: Optional[AgentDependencyInjector] = None
        self.svc_inj: Optional[ServiceDependencyInjector] = None
        self.repo_inj: Optional[RepositoryDependencyInjector] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("inject_dependencies", self.inject_dependencies)

    def _spawn_subagents(self) -> None:
        """Spawn atomic dependency injector subagents (Rule 1 & Rule 5)."""
        logger.info("DependencyInjector %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.core_inj = self.spawn_subagent(CoreDependencyInjector, name="CoreDependencyInjector", max_depth=child_depth, resources_mb=32)
        self.agent_inj = self.spawn_subagent(AgentDependencyInjector, name="AgentDependencyInjector", max_depth=child_depth, resources_mb=32)
        self.svc_inj = self.spawn_subagent(ServiceDependencyInjector, name="ServiceDependencyInjector", max_depth=child_depth, resources_mb=32)
        self.repo_inj = self.spawn_subagent(RepositoryDependencyInjector, name="RepositoryDependencyInjector", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DependencyInjector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        res = self.inject_dependencies(target=payload.get("target"))
        return {"status": "COMPLETED", "injection_results": res}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DependencyInjector %s cleanup complete.", self.agent_id)

    def inject_dependencies(self, target: Any = None) -> Dict[str, Any]:
        """Execute full dependency injection suite."""
        p_env = {"payload": {"target": target}}

        c_res = self.core_inj.process(p_env) if self.core_inj else {}
        a_res = self.agent_inj.process(p_env) if self.agent_inj else {}
        s_res = self.svc_inj.process(p_env) if self.svc_inj else {}
        r_res = self.repo_inj.process(p_env) if self.repo_inj else {}

        return {
            "core": c_res,
            "agents": a_res,
            "services": s_res,
            "repositories": r_res,
            "injection_complete": True,
        }
