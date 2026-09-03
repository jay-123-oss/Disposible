"""RegistryManager agent managing agent capability indexes, heartbeat monitoring, and lifecycle status."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from agents.commstate.exceptions import RegistryError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.CommState.RegistryManager")


# ==============================================================================
# L5 Atomic Registry Subagents
# ==============================================================================

class AgentRegistrar(BaseAgent):
    """L5 agent indexing agents by capabilities and registering metadata."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AgentRegistrar %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        agent_record = {
            "agent_id": payload.get("agent_id", "UNKNOWN"),
            "name": payload.get("name", "UnknownAgent"),
            "capabilities": list(payload.get("capabilities", [])),
            "level": payload.get("level", 1),
            "ram_mb": payload.get("ram_mb", 128),
            "status": "ACTIVE",
            "last_heartbeat": time.time(),
        }
        return {"status": "COMPLETED", "agent_record": agent_record}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "agent_record" not in result:
            raise RegistryError("AgentRegistrar produced invalid record.")
        return result

    def cleanup(self) -> None:
        logger.debug("AgentRegistrar %s cleaned up.", self.agent_id)


class AgentUnregistrar(BaseAgent):
    """L5 agent safely removing agents from directory upon deactivation."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AgentUnregistrar %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        registry = dict(payload.get("registry", {}))
        agent_id = payload.get("agent_id")

        unregistered = False
        if agent_id and agent_id in registry:
            del registry[agent_id]
            unregistered = True

        return {"status": "COMPLETED", "registry": registry, "unregistered": unregistered}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AgentUnregistrar %s cleaned up.", self.agent_id)


class AgentFinder(BaseAgent):
    """L5 agent locating agents matching requested capabilities."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AgentFinder %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        registry = payload.get("registry", {})
        capability = payload.get("capability")

        matched = []
        for a_id, agent in registry.items():
            if not capability or capability in agent.get("capabilities", []):
                matched.append(agent)

        return {"status": "COMPLETED", "matched_agents": matched, "count": len(matched)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AgentFinder %s cleaned up.", self.agent_id)


class AgentStatusChecker(BaseAgent):
    """L5 agent auditing heartbeat vitality and identifying stale agents."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AgentStatusChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        registry = dict(payload.get("registry", {}))
        stale_threshold = payload.get("stale_timeout_seconds", 120)
        now = time.time()

        stale_agents = []
        for a_id, agent in registry.items():
            last_hb = agent.get("last_heartbeat", now)
            if now - last_hb > stale_threshold:
                agent["status"] = "STALE"
                stale_agents.append(a_id)

        return {"status": "COMPLETED", "stale_agents": stale_agents, "registry": registry}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AgentStatusChecker %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 RegistryManager Agent
# ==============================================================================

class RegistryManager(BaseAgent):
    """L4 coordinator overseeing agent directory discovery and heartbeat monitoring."""

    def __init__(
        self,
        name: str = "RegistryManager",
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
            "registry_management",
            "agent_registration",
            "agent_discovery",
            "heartbeat_auditing",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C5_REGISTRY_MANAGER",
        )

        self._directory: Dict[str, Dict[str, Any]] = {}
        self.registrar: Optional[AgentRegistrar] = None
        self.unregistrar: Optional[AgentUnregistrar] = None
        self.finder: Optional[AgentFinder] = None
        self.status_checker: Optional[AgentStatusChecker] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("register_agent_meta", self.register_agent_meta)
        self.register_tool("find_agents_by_capability", self.find_agents_by_capability)
        self.register_tool("audit_heartbeats", self.audit_heartbeats)

    def _spawn_subagents(self) -> None:
        """Spawn atomic registry subagents (Rule 1 & Rule 5)."""
        logger.info("RegistryManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.registrar = self.spawn_subagent(
            AgentRegistrar,
            name="AgentRegistrar",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.unregistrar = self.spawn_subagent(
            AgentUnregistrar,
            name="AgentUnregistrar",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.finder = self.spawn_subagent(
            AgentFinder,
            name="AgentFinder",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.status_checker = self.spawn_subagent(
            AgentStatusChecker,
            name="AgentStatusChecker",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RegistryManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        cap = payload.get("capability")
        matched = self.find_agents_by_capability(cap)
        return {"status": "COMPLETED", "matched": matched}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("RegistryManager %s cleanup complete.", self.agent_id)

    def register_agent_meta(self, agent_id: str, name: str, capabilities: List[str], ram_mb: int = 128) -> Dict[str, Any]:
        """Index agent in registry directory."""
        p_env = {"payload": {"agent_id": agent_id, "name": name, "capabilities": capabilities, "ram_mb": ram_mb}}
        res = self.registrar.process(p_env) if self.registrar else {"agent_record": {"agent_id": agent_id, "capabilities": capabilities}}
        rec = res["agent_record"]
        self._directory[agent_id] = rec
        return rec

    def find_agents_by_capability(self, capability: Optional[str] = None) -> List[Dict[str, Any]]:
        """Look up agents offering requested capability."""
        p_env = {"payload": {"registry": self._directory, "capability": capability}}
        res = self.finder.process(p_env) if self.finder else {"matched_agents": list(self._directory.values())}
        return res.get("matched_agents", [])

    def audit_heartbeats(self, timeout_seconds: int = 120) -> List[str]:
        """Identify stale agents whose heartbeat exceeded threshold."""
        p_env = {"payload": {"registry": self._directory, "stale_timeout_seconds": timeout_seconds}}
        res = self.status_checker.process(p_env) if self.status_checker else {"stale_agents": []}
        return res.get("stale_agents", [])
