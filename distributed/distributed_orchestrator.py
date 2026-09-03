"""DistributedOrchestrator (D1) L3 agent coordinating all 13 distributed architecture subsystems.

Spawns the complete D2-D14 hierarchy:
- NodeManager, ClusterCoordinator, LoadBalancer, ServiceDiscovery
- StateSynchronizer, MessageBroker, TaskDistributor, FaultTolerance
- ReplicationManager, ConsensusManager, PerformanceMonitor, SecurityManager, LogAggregator
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from distributed.cluster_coordinator import ClusterCoordinator
from distributed.consensus_manager import ConsensusManager
from distributed.exceptions import DistributedError
from distributed.fault_tolerance import FaultTolerance
from distributed.load_balancer import LoadBalancer
from distributed.log_aggregator import LogAggregator
from distributed.message_broker import MessageBroker
from distributed.node_manager import NodeManager
from distributed.performance_monitor import PerformanceMonitor
from distributed.replication_manager import ReplicationManager
from distributed.security_manager import SecurityManager
from distributed.service_discovery import ServiceDiscovery
from distributed.state_synchronizer import StateSynchronizer
from distributed.task_distributor import TaskDistributor

logger = logging.getLogger("FractalCore.Distributed.DistributedOrchestrator")


class DistributedOrchestrator(BaseAgent):
    """L3 Master Distributed Orchestrator supervising all 13 L4 distributed subsystem coordinators."""

    def __init__(
        self,
        name: str = "DistributedOrchestrator",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 256,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
        cluster_name: str = "fractal-cluster",
    ) -> None:
        default_caps = capabilities or [
            "distributed",
            "distributed_orchestration",
            "node_manager",
            "cluster_coordinator",
            "load_balancer",
            "service_discovery",
            "state_synchronizer",
            "message_broker",
            "task_distributor",
            "fault_tolerance",
            "replication_manager",
            "consensus_manager",
            "performance_monitor",
            "security_manager",
            "log_aggregator",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "D1_DISTRIBUTED_ORCHESTRATOR",
        )
        self.cluster_name = cluster_name
        self.node_manager: Optional[NodeManager] = None
        self.cluster_coordinator: Optional[ClusterCoordinator] = None
        self.load_balancer: Optional[LoadBalancer] = None
        self.service_discovery: Optional[ServiceDiscovery] = None
        self.state_synchronizer: Optional[StateSynchronizer] = None
        self.message_broker: Optional[MessageBroker] = None
        self.task_distributor: Optional[TaskDistributor] = None
        self.fault_tolerance: Optional[FaultTolerance] = None
        self.replication_manager: Optional[ReplicationManager] = None
        self.consensus_manager: Optional[ConsensusManager] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None
        self.security_manager: Optional[SecurityManager] = None
        self.log_aggregator: Optional[LogAggregator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_distributed_subsystems()

        self.register_tool("run_cluster_lifecycle", self.run_cluster_lifecycle)
        self.register_tool("get_cluster_status", self.get_cluster_status)

    def _spawn_distributed_subsystems(self) -> None:
        """Spawn the 13 L4 distributed coordinators (Rule 1 & Rule 5)."""
        logger.info("DistributedOrchestrator %s spawning 13 distributed coordinators...", self.agent_id)
        child_depth = self.depth + 2

        self.node_manager = self.spawn_subagent(
            NodeManager, name="NodeManager", max_depth=child_depth, resources_mb=64, agent_id="D2_NODE_MANAGER"
        )
        self.cluster_coordinator = self.spawn_subagent(
            ClusterCoordinator, name="ClusterCoordinator", max_depth=child_depth, resources_mb=64, agent_id="D3_CLUSTER_COORDINATOR"
        )
        self.load_balancer = self.spawn_subagent(
            LoadBalancer, name="LoadBalancer", max_depth=child_depth, resources_mb=64, agent_id="D4_LOAD_BALANCER"
        )
        self.service_discovery = self.spawn_subagent(
            ServiceDiscovery, name="ServiceDiscovery", max_depth=child_depth, resources_mb=64, agent_id="D5_SERVICE_DISCOVERY"
        )
        self.state_synchronizer = self.spawn_subagent(
            StateSynchronizer, name="StateSynchronizer", max_depth=child_depth, resources_mb=64, agent_id="D6_STATE_SYNCHRONIZER"
        )
        self.message_broker = self.spawn_subagent(
            MessageBroker, name="MessageBroker", max_depth=child_depth, resources_mb=64, agent_id="D7_MESSAGE_BROKER"
        )
        self.task_distributor = self.spawn_subagent(
            TaskDistributor, name="TaskDistributor", max_depth=child_depth, resources_mb=64, agent_id="D8_TASK_DISTRIBUTOR"
        )
        self.fault_tolerance = self.spawn_subagent(
            FaultTolerance, name="FaultTolerance", max_depth=child_depth, resources_mb=64, agent_id="D9_FAULT_TOLERANCE"
        )
        self.replication_manager = self.spawn_subagent(
            ReplicationManager, name="ReplicationManager", max_depth=child_depth, resources_mb=64, agent_id="D10_REPLICATION_MANAGER"
        )
        self.consensus_manager = self.spawn_subagent(
            ConsensusManager, name="ConsensusManager", max_depth=child_depth, resources_mb=64, agent_id="D11_CONSENSUS_MANAGER"
        )
        self.performance_monitor = self.spawn_subagent(
            PerformanceMonitor, name="PerformanceMonitor", max_depth=child_depth, resources_mb=64, agent_id="D12_PERFORMANCE_MONITOR"
        )
        self.security_manager = self.spawn_subagent(
            SecurityManager, name="SecurityManager", max_depth=child_depth, resources_mb=64, agent_id="D13_SECURITY_MANAGER"
        )
        self.log_aggregator = self.spawn_subagent(
            LogAggregator, name="LogAggregator", max_depth=child_depth, resources_mb=64, agent_id="D14_LOG_AGGREGATOR"
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.info("DistributedOrchestrator %s initialized for cluster '%s'.", self.agent_id, self.cluster_name)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        """Execute distributed command or status aggregation."""
        intent = task_envelope.get("intent", "status")
        if intent == "lifecycle":
            return {"status": "COMPLETED", "result": self.run_cluster_lifecycle(task_envelope.get("nodes", []))}
        return {"status": "COMPLETED", "result": self.get_cluster_status()}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.info("DistributedOrchestrator %s cleanup complete.", self.agent_id)

    def run_cluster_lifecycle(self, initial_nodes: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Bootstrap nodes, join cluster, elect leader, and configure replication."""
        nodes = initial_nodes or [
            {"id": "node-1", "host": "192.168.1.10", "port": 8000, "role": "leader"},
            {"id": "node-2", "host": "192.168.1.11", "port": 8000, "role": "follower"},
            {"id": "node-3", "host": "192.168.1.12", "port": 8000, "role": "follower"},
        ]
        registered = []
        node_ids = []
        for n in nodes:
            if self.node_manager:
                self.node_manager.register_node(n)
            if self.cluster_coordinator:
                self.cluster_coordinator.join_cluster(n["id"], n)
            registered.append(n["id"])
            node_ids.append(n["id"])

        if self.load_balancer:
            self.load_balancer.update_nodes(node_ids)
        if self.replication_manager:
            self.replication_manager.set_nodes(node_ids)
        if self.task_distributor:
            self.task_distributor.set_nodes(node_ids)

        # Ensure leader elected
        leader = node_ids[0] if node_ids else None
        if self.cluster_coordinator and leader:
            self.cluster_coordinator.elect_leader(leader)
        if self.consensus_manager:
            self.consensus_manager.become_leader()

        return {
            "cluster_name": self.cluster_name,
            "bootstrapped": True,
            "node_count": len(registered),
            "leader": leader,
            "nodes": registered,
        }

    def get_cluster_status(self) -> Dict[str, Any]:
        """Query and synthesize diagnostics across all 13 subsystems."""
        return {
            "cluster_name": self.cluster_name,
            "timestamp": time.time(),
            "nodes": self.node_manager.check_nodes_health() if self.node_manager else {},
            "topology": self.cluster_coordinator.get_cluster_topology() if self.cluster_coordinator else {},
            "consensus": self.consensus_manager.get_consensus_status() if self.consensus_manager else {},
            "performance": self.performance_monitor.evaluate_cluster_health() if self.performance_monitor else {},
        }
