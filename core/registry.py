"""AgentRegistry class for tracking, finding, and monitoring fractal agents.

Implements:
- Thread-safe Singleton pattern for system-wide agent discovery.
- Capability-based querying and agent lifecycle indexing.
- Dynamic RAM and resource allocation accounting within the 8GB ceiling.
- Automated health-check sweeps across active agents.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional, Set

from core.agent_base import BaseAgent
from core.exceptions import AgentError, ResourceLimitError


logger = logging.getLogger("FractalCore.Registry")


class AgentRegistry:
    """Thread-safe singleton registry governing all instantiated agents."""

    _instance: Optional[AgentRegistry] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> AgentRegistry:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AgentRegistry, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, max_system_ram_mb: int = 8192, max_agents: int = 200) -> None:
        if getattr(self, "_initialized", False):
            return

        self._max_system_ram_mb = max_system_ram_mb
        self._max_agents = max_agents
        self._registry_lock = threading.RLock()
        self._agents: Dict[str, BaseAgent] = {}
        self._status_map: Dict[str, Dict[str, Any]] = {}
        self._allocated_ram_mb: int = 0
        self._capability_index: Dict[str, Set[str]] = {}
        self._last_health_check_ts: float = time.time()
        self._initialized = True
        logger.info(
            "AgentRegistry initialized (Max System RAM: %d MB, Max Agents: %d)",
            self._max_system_ram_mb,
            self._max_agents,
        )

    # --------------------------------------------------------------------------
    # Registration / Unregistration
    # --------------------------------------------------------------------------

    def register_agent(self, agent: BaseAgent) -> None:
        """Register a new or spawned agent into the registry.

        Args:
            agent: The BaseAgent instance to register.

        Raises:
            ResourceLimitError: If agent count or memory quota is exceeded.
            AgentError: If agent ID already exists in the registry.
        """
        with self._registry_lock:
            agent_id = agent.agent_id
            if agent_id in self._agents:
                raise AgentError(
                    f"Agent with ID '{agent_id}' is already registered.",
                    details={"agent_id": agent_id},
                )

            if len(self._agents) >= self._max_agents:
                raise ResourceLimitError(
                    f"Maximum agent capacity ({self._max_agents}) reached. Cannot register {agent_id}.",
                    details={"current_count": len(self._agents), "max_agents": self._max_agents},
                )

            req_ram = agent._resources_mb
            if (self._allocated_ram_mb + req_ram) > self._max_system_ram_mb:
                raise ResourceLimitError(
                    f"Insufficient system RAM to register agent {agent_id} ({req_ram} MB requested, "
                    f"{self._allocated_ram_mb}/{self._max_system_ram_mb} MB currently allocated).",
                    details={
                        "requested_mb": req_ram,
                        "allocated_mb": self._allocated_ram_mb,
                        "limit_mb": self._max_system_ram_mb,
                    },
                )

            # Commit registration
            self._agents[agent_id] = agent
            self._allocated_ram_mb += req_ram
            self._status_map[agent_id] = {
                "name": agent.name,
                "state": agent.state,
                "depth": agent.depth,
                "parent_id": agent.parent.agent_id if agent.parent else None,
                "allocated_mb": req_ram,
                "registered_at": time.time(),
                "last_seen": time.time(),
                "healthy": True,
            }

            # Index capabilities for fast lookup
            for cap in agent.capabilities:
                if cap not in self._capability_index:
                    self._capability_index[cap] = set()
                self._capability_index[cap].add(agent_id)

            logger.info(
                "Registered agent '%s' [%s] (Level %d, RAM: %d MB). Total RAM: %d/%d MB",
                agent.name,
                agent_id,
                agent.depth,
                req_ram,
                self._allocated_ram_mb,
                self._max_system_ram_mb,
            )

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent and release its allocated memory quota."""
        with self._registry_lock:
            if agent_id not in self._agents:
                logger.warning("Attempted to unregister unknown agent '%s'", agent_id)
                return

            agent = self._agents.pop(agent_id)
            status_info = self._status_map.pop(agent_id, {})
            released_ram = status_info.get("allocated_mb", agent._resources_mb)
            self._allocated_ram_mb = max(0, self._allocated_ram_mb - released_ram)

            # Clean capability index
            for cap in agent.capabilities:
                if cap in self._capability_index and agent_id in self._capability_index[cap]:
                    self._capability_index[cap].remove(agent_id)
                    if not self._capability_index[cap]:
                        del self._capability_index[cap]

            logger.info(
                "Unregistered agent '%s' (Released %d MB). Total RAM: %d/%d MB",
                agent_id,
                released_ram,
                self._allocated_ram_mb,
                self._max_system_ram_mb,
            )

    # --------------------------------------------------------------------------
    # Queries & Lookups
    # --------------------------------------------------------------------------

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Retrieve an agent instance by its ID."""
        with self._registry_lock:
            return self._agents.get(agent_id)

    def find_by_capability(self, capability: str) -> List[BaseAgent]:
        """Find all registered agents declaring a specific capability."""
        with self._registry_lock:
            agent_ids = self._capability_index.get(capability, set())
            return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def find_by_name(self, name: str) -> List[BaseAgent]:
        """Find all registered agents matching a given name."""
        with self._registry_lock:
            return [agent for agent in self._agents.values() if agent.name == name]

    def get_all_agents(self) -> List[BaseAgent]:
        """Return a snapshot list of all currently registered agents."""
        with self._registry_lock:
            return list(self._agents.values())

    def get_allocated_ram_mb(self) -> int:
        """Return the current total allocated RAM across all registered agents."""
        with self._registry_lock:
            return self._allocated_ram_mb

    # --------------------------------------------------------------------------
    # Status & Health Monitoring
    # --------------------------------------------------------------------------

    def update_status(self, agent_id: str, state: str, extra_info: Optional[Dict[str, Any]] = None) -> None:
        """Update an agent's tracked status and heartbeat timestamp."""
        with self._registry_lock:
            if agent_id in self._status_map:
                self._status_map[agent_id]["state"] = state
                self._status_map[agent_id]["last_seen"] = time.time()
                if extra_info:
                    self._status_map[agent_id].update(extra_info)

    def health_check_all(self, timeout_threshold_seconds: float = 60.0) -> Dict[str, Any]:
        """Run health check across all registered agents.

        Returns:
            Dictionary containing healthy count, degraded count, and per-agent status.
        """
        with self._registry_lock:
            now = time.time()
            healthy_count = 0
            unhealthy_agents: List[str] = []

            for agent_id, info in self._status_map.items():
                elapsed = now - info["last_seen"]
                is_stale = elapsed > timeout_threshold_seconds and info["state"] == "working"
                if is_stale:
                    info["healthy"] = False
                    unhealthy_agents.append(agent_id)
                    logger.warning("Agent '%s' marked UNHEALTHY (last seen %.1fs ago)", agent_id, elapsed)
                else:
                    info["healthy"] = True
                    healthy_count += 1

            self._last_health_check_ts = now
            return {
                "total_agents": len(self._agents),
                "healthy_count": healthy_count,
                "unhealthy_count": len(unhealthy_agents),
                "unhealthy_agents": unhealthy_agents,
                "allocated_ram_mb": self._allocated_ram_mb,
                "max_system_ram_mb": self._max_system_ram_mb,
            }

    def clear(self) -> None:
        """Clear all registered agents and reset counters (used in testing)."""
        with self._registry_lock:
            self._agents.clear()
            self._status_map.clear()
            self._allocated_ram_mb = 0
            self._capability_index.clear()
            self._max_system_ram_mb = 8192
            self._max_agents = 200
            logger.info("AgentRegistry cleared.")
