"""LoadBalancer agent distributing traffic/workloads across nodes.

Implements the complete Load Balancer hierarchy (D4):
- L4 LoadBalancer coordinator
- L5 atomic workers: RoundRobin, LeastConnection, ConsistentHash, WeightedDistribution
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from distributed.exceptions import LoadBalancingError

logger = logging.getLogger("FractalCore.Distributed.LoadBalancer")


# ==============================================================================
# L5 Atomic Load Balancer Subagents
# ==============================================================================

class RoundRobin(BaseAgent):
    """L5 agent dispatching requests in cyclic sequential round-robin order."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RoundRobin %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        nodes = task_envelope.get("nodes", [])
        index = task_envelope.get("index", 0)
        if not nodes:
            return {"status": "FAILED", "selected_node": None, "error": "Empty node list"}
        selected = nodes[index % len(nodes)]
        return {"status": "COMPLETED", "selected_node": selected, "next_index": (index + 1) % len(nodes)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("RoundRobin %s cleaned up.", self.agent_id)


class LeastConnection(BaseAgent):
    """L5 agent selecting the node with the fewest active connections/tasks."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LeastConnection %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        nodes = task_envelope.get("nodes", [])
        connections = task_envelope.get("connections", {})
        if not nodes:
            return {"status": "FAILED", "selected_node": None, "error": "Empty node list"}
        selected = min(nodes, key=lambda n: connections.get(n, 0))
        return {"status": "COMPLETED", "selected_node": selected, "active_connections": connections.get(selected, 0)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("LeastConnection %s cleaned up.", self.agent_id)


class ConsistentHash(BaseAgent):
    """L5 agent mapping keys to nodes using consistent hashing ring for cache affinity."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ConsistentHash %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        nodes = task_envelope.get("nodes", [])
        key = str(task_envelope.get("key", "default_key"))
        if not nodes:
            return {"status": "FAILED", "selected_node": None, "error": "Empty node list"}
        
        # Consistent hash ring logic
        ring = {}
        for node in nodes:
            for replica in range(3):
                h = int(hashlib.md5(f"{node}:{replica}".encode("utf-8")).hexdigest(), 16)
                ring[h] = node
        
        sorted_hashes = sorted(ring.keys())
        key_hash = int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)
        
        selected = ring[sorted_hashes[0]]
        for h in sorted_hashes:
            if h >= key_hash:
                selected = ring[h]
                break
                
        return {"status": "COMPLETED", "selected_node": selected, "key": key}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ConsistentHash %s cleaned up.", self.agent_id)


class WeightedDistribution(BaseAgent):
    """L5 agent selecting nodes based on capacity weights."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("WeightedDistribution %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        nodes = task_envelope.get("nodes", [])
        weights = task_envelope.get("weights", {})
        if not nodes:
            return {"status": "FAILED", "selected_node": None, "error": "Empty node list"}
        
        total_weight = sum(weights.get(n, 1) for n in nodes)
        # Select highest weighted available
        selected = max(nodes, key=lambda n: weights.get(n, 1))
        return {"status": "COMPLETED", "selected_node": selected, "total_weight": total_weight}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("WeightedDistribution %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 LoadBalancer Agent
# ==============================================================================

class LoadBalancer(BaseAgent):
    """L4 coordinator providing multi-algorithm workload distribution across cluster nodes."""

    def __init__(
        self,
        name: str = "LoadBalancer",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
        default_algorithm: str = "round_robin",
    ) -> None:
        default_caps = capabilities or [
            "load_balancer",
            "round_robin",
            "least_connection",
            "consistent_hash",
            "weighted_distribution",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "D4_LOAD_BALANCER",
        )
        self.default_algorithm = default_algorithm
        self.nodes: List[str] = []
        self.connections: Dict[str, int] = {}
        self.weights: Dict[str, int] = {}
        self.rr_index = 0

        self.round_robin: Optional[RoundRobin] = None
        self.least_connection: Optional[LeastConnection] = None
        self.consistent_hash: Optional[ConsistentHash] = None
        self.weighted_distribution: Optional[WeightedDistribution] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("route_request", self.route_request)
        self.register_tool("update_nodes", self.update_nodes)

    def _spawn_subagents(self) -> None:
        """Spawn atomic load balancer subagents (Rule 1 & Rule 5)."""
        logger.info("LoadBalancer %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.round_robin = self.spawn_subagent(RoundRobin, name="RoundRobin", max_depth=child_depth, resources_mb=32)
        self.least_connection = self.spawn_subagent(LeastConnection, name="LeastConnection", max_depth=child_depth, resources_mb=32)
        self.consistent_hash = self.spawn_subagent(ConsistentHash, name="ConsistentHash", max_depth=child_depth, resources_mb=32)
        self.weighted_distribution = self.spawn_subagent(WeightedDistribution, name="WeightedDistribution", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LoadBalancer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        algo = task_envelope.get("algorithm", self.default_algorithm)
        key = task_envelope.get("key")
        node = self.route_request(algorithm=algo, key=key)
        return {"status": "COMPLETED", "selected_node": node, "algorithm": algo}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("LoadBalancer %s cleaned up.", self.agent_id)

    def update_nodes(self, nodes: List[str], weights: Optional[Dict[str, int]] = None) -> None:
        """Update active pool of nodes available for routing."""
        self.nodes = list(nodes)
        if weights:
            self.weights = weights
        for n in self.nodes:
            if n not in self.connections:
                self.connections[n] = 0

    def route_request(self, algorithm: Optional[str] = None, key: Optional[str] = None) -> Optional[str]:
        """Dispatch a request to an optimal node according to the specified algorithm."""
        if not self.nodes:
            return None

        algo = algorithm or self.default_algorithm
        if algo == "least_connection" and self.least_connection:
            res = self.least_connection.process({"nodes": self.nodes, "connections": self.connections})
            selected = res.get("selected_node")
        elif algo == "consistent_hash" and self.consistent_hash:
            res = self.consistent_hash.process({"nodes": self.nodes, "key": key or "default"})
            selected = res.get("selected_node")
        elif algo == "weighted_distribution" and self.weighted_distribution:
            res = self.weighted_distribution.process({"nodes": self.nodes, "weights": self.weights})
            selected = res.get("selected_node")
        else:
            res = self.round_robin.process({"nodes": self.nodes, "index": self.rr_index}) if self.round_robin else {"selected_node": self.nodes[0], "next_index": 0}
            selected = res.get("selected_node")
            self.rr_index = res.get("next_index", 0)

        if selected:
            self.connections[selected] = self.connections.get(selected, 0) + 1
        return selected

    def release_request(self, node: str) -> None:
        """Decrement active connection count on request completion."""
        if node in self.connections and self.connections[node] > 0:
            self.connections[node] -= 1
