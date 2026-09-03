"""NodeManager agent managing cluster node registration, health, lifecycle, and deregistration.

Implements the complete Node Manager hierarchy (D2):
- L4 NodeManager coordinator
- L5 atomic workers: NodeRegistrar, NodeHealthChecker, NodeLifecycle, NodeDeregistrar
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from distributed.exceptions import NodeManagementError

logger = logging.getLogger("FractalCore.Distributed.NodeManager")


# ==============================================================================
# L5 Atomic Node Manager Subagents
# ==============================================================================

class NodeRegistrar(BaseAgent):
    """L5 agent registering new physical/virtual nodes into the cluster inventory."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NodeRegistrar %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        node = task_envelope.get("node", {})
        node_id = node.get("id") or f"node-{int(time.time()*1000)}"
        registered_node = {
            "id": node_id,
            "host": node.get("host", "127.0.0.1"),
            "port": node.get("port", 8000),
            "role": node.get("role", "follower"),
            "status": "healthy",
            "registered_at": time.time(),
            "last_heartbeat": time.time(),
            "metadata": node.get("metadata", {}),
        }
        return {"status": "COMPLETED", "node_id": node_id, "node": registered_node}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NodeRegistrar %s cleaned up.", self.agent_id)


class NodeHealthChecker(BaseAgent):
    """L5 agent evaluating node heartbeat timestamps and determining liveness."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NodeHealthChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        node = task_envelope.get("node", {})
        timeout = task_envelope.get("heartbeat_timeout", 30.0)
        last_hb = node.get("last_heartbeat", 0)
        elapsed = time.time() - last_hb
        healthy = elapsed <= timeout
        status = "healthy" if healthy else ("degraded" if elapsed <= timeout * 2 else "dead")
        return {
            "status": "COMPLETED",
            "node_id": node.get("id", ""),
            "healthy": healthy,
            "node_status": status,
            "elapsed_seconds": round(elapsed, 2),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NodeHealthChecker %s cleaned up.", self.agent_id)


class NodeLifecycle(BaseAgent):
    """L5 agent orchestrating node state transitions (provisioning -> active -> draining -> stopped)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NodeLifecycle %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        node_id = task_envelope.get("node_id", "")
        target_state = task_envelope.get("target_state", "active")
        valid_states = {"provisioning", "active", "draining", "maintenance", "stopped"}
        if target_state not in valid_states:
            return {"status": "FAILED", "error": f"Invalid lifecycle state: {target_state}"}
        return {
            "status": "COMPLETED",
            "node_id": node_id,
            "previous_state": task_envelope.get("current_state", "unknown"),
            "new_state": target_state,
            "transitioned_at": time.time(),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NodeLifecycle %s cleaned up.", self.agent_id)


class NodeDeregistrar(BaseAgent):
    """L5 agent cleanly removing decommissioned nodes and freeing cluster resources."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NodeDeregistrar %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        node_id = task_envelope.get("node_id", "")
        reason = task_envelope.get("reason", "manual_deregister")
        return {
            "status": "COMPLETED",
            "node_id": node_id,
            "deregistered": True,
            "reason": reason,
            "deregistered_at": time.time(),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NodeDeregistrar %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 NodeManager Agent
# ==============================================================================

class NodeManager(BaseAgent):
    """L4 coordinator supervising cluster node inventory, health checks, and lifecycle."""

    def __init__(
        self,
        name: str = "NodeManager",
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
            "node_manager",
            "node_registrar",
            "node_health_checker",
            "node_lifecycle",
            "node_deregistrar",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "D2_NODE_MANAGER",
        )
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.registrar: Optional[NodeRegistrar] = None
        self.health_checker: Optional[NodeHealthChecker] = None
        self.lifecycle: Optional[NodeLifecycle] = None
        self.deregistrar: Optional[NodeDeregistrar] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("register_node", self.register_node)
        self.register_tool("check_nodes_health", self.check_nodes_health)
        self.register_tool("deregister_node", self.deregister_node)

    def _spawn_subagents(self) -> None:
        """Spawn the 4 L5 atomic workers (Rule 1 & Rule 5)."""
        logger.info("NodeManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.registrar = self.spawn_subagent(NodeRegistrar, name="NodeRegistrar", max_depth=child_depth, resources_mb=32)
        self.health_checker = self.spawn_subagent(NodeHealthChecker, name="NodeHealthChecker", max_depth=child_depth, resources_mb=32)
        self.lifecycle = self.spawn_subagent(NodeLifecycle, name="NodeLifecycle", max_depth=child_depth, resources_mb=32)
        self.deregistrar = self.spawn_subagent(NodeDeregistrar, name="NodeDeregistrar", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NodeManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        action = task_envelope.get("action", "list")
        if action == "register":
            return self.register_node(task_envelope.get("node", {}))
        elif action == "health_check":
            return self.check_nodes_health()
        elif action == "deregister":
            return self.deregister_node(task_envelope.get("node_id", ""))
        return {"status": "COMPLETED", "nodes": list(self.nodes.values()), "count": len(self.nodes)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NodeManager %s cleaned up.", self.agent_id)

    def register_node(self, node_info: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new node into the cluster."""
        res = self.registrar.process({"node": node_info}) if self.registrar else {
            "node_id": node_info.get("id", "node-local"),
            "node": node_info,
        }
        node_id = res["node_id"]
        self.nodes[node_id] = res["node"]
        logger.info("Registered node %s (total: %d)", node_id, len(self.nodes))
        return {"registered": True, "node": self.nodes[node_id], "total_nodes": len(self.nodes)}

    def record_heartbeat(self, node_id: str) -> bool:
        """Update last heartbeat timestamp for a node."""
        if node_id in self.nodes:
            self.nodes[node_id]["last_heartbeat"] = time.time()
            self.nodes[node_id]["status"] = "healthy"
            return True
        return False

    def check_nodes_health(self, timeout: float = 30.0) -> Dict[str, Any]:
        """Verify health status of all tracked nodes."""
        summary: Dict[str, Any] = {"healthy": 0, "degraded": 0, "dead": 0, "nodes": {}}
        for nid, node in list(self.nodes.items()):
            res = self.health_checker.process({"node": node, "heartbeat_timeout": timeout}) if self.health_checker else {
                "healthy": True,
                "node_status": "healthy",
            }
            status = res.get("node_status", "healthy")
            self.nodes[nid]["status"] = status
            summary["nodes"][nid] = status
            summary[status] = summary.get(status, 0) + 1
        return summary

    def deregister_node(self, node_id: str, reason: str = "manual") -> Dict[str, Any]:
        """Remove a node from the cluster."""
        if node_id not in self.nodes:
            return {"deregistered": False, "error": f"Node {node_id} not found"}
        res = self.deregistrar.process({"node_id": node_id, "reason": reason}) if self.deregistrar else {"deregistered": True}
        del self.nodes[node_id]
        logger.info("Deregistered node %s (remaining: %d)", node_id, len(self.nodes))
        return {"deregistered": True, "node_id": node_id, "remaining": len(self.nodes)}
