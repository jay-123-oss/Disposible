"""Distributed Architecture Layer for the Fractal Multi-Agent Autonomous Coding System.

Exports all 14 distributed agents (D1-D14) and 52 atomic subagents across L3 to L5,
along with custom exceptions and the registration helper `register_all_distributed_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from core.registry import AgentRegistry
from distributed.cluster_coordinator import (
    ClusterCoordinator,
    ClusterJoiner,
    ClusterLeaver,
    ClusterSync,
    LeaderElector,
)
from distributed.consensus_manager import (
    CommitManager,
    ConsensusManager,
    LeaderHeartbeat,
    LogReplication,
    RaftImplementation,
)
from distributed.distributed_orchestrator import DistributedOrchestrator
from distributed.exceptions import (
    ClusterCoordinationError,
    ConsensusError,
    DistributedError,
    DistributedSecurityError,
    FaultToleranceError,
    LoadBalancingError,
    LogAggregationError,
    MessageBrokerError,
    NodeManagementError,
    PerformanceMonitoringError,
    ReplicationError,
    ServiceDiscoveryError,
    StateSynchronizationError,
    TaskDistributionError,
)
from distributed.fault_tolerance import (
    AutoRecoverer,
    CircuitBreaker,
    FailureDetector,
    FaultTolerance,
    RetryManager,
)
from distributed.load_balancer import (
    ConsistentHash,
    LeastConnection,
    LoadBalancer,
    RoundRobin,
    WeightedDistribution,
)
from distributed.log_aggregator import (
    LogAggregator,
    LogCollector,
    LogIndexer,
    LogSearcher,
    LogVisualizer,
)
from distributed.message_broker import (
    MessageBroker,
    Publisher,
    QueueManager,
    Subscriber,
    TopicManager,
)
from distributed.node_manager import (
    NodeDeregistrar,
    NodeHealthChecker,
    NodeLifecycle,
    NodeManager,
    NodeRegistrar,
)
from distributed.performance_monitor import (
    ClusterMetricsAggregator,
    NodeMetricsCollector,
    PerfAlerter,
    PerfAnalyzer,
    PerformanceMonitor,
)
from distributed.raft import (
    AppendEntriesArgs,
    AppendEntriesReply,
    RaftEngine,
    RaftLogEntry,
    RaftRole,
    RequestVoteArgs,
    RequestVoteReply,
)
from distributed.replication_manager import (
    AsyncReplication,
    ReplicationFactor,
    ReplicationManager,
    ReplicationVerifier,
    SyncReplication,
)
from distributed.security_manager import (
    AuditLogger,
    CertManager,
    Encryption,
    NodeAuth,
    SecurityManager,
)
from distributed.service_discovery import (
    ServiceCache,
    ServiceDiscovery,
    ServiceFinder,
    ServiceHealthChecker,
    ServiceRegistrar,
)
from distributed.state_synchronizer import (
    ConflictResolver,
    FullSync,
    IncrementalSync,
    StateSynchronizer,
    StateVerifier,
)
from distributed.task_distributor import (
    TaskAssigner,
    TaskDistributor,
    TaskRecoverer,
    TaskSplitter,
    TaskTracker,
)

logger = logging.getLogger("FractalCore.Distributed")


def register_all_distributed_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Instantiate and register all 66 distributed agents into the central registry."""
    orch = DistributedOrchestrator(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="D1_DISTRIBUTED_ORCHESTRATOR",
        auto_spawn_subagents=True,
    )
    registry.register_agent(orch)
    registered_count = 1

    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in getattr(agent, "children", {}).items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(orch)
    logger.info("Successfully registered %d distributed architecture agents into registry.", registered_count)
    return {"distributed_orchestrator": orch, "total_registered": registered_count}



__all__ = [
    # Master L3
    "DistributedOrchestrator",
    # L4 Coordinators
    "NodeManager",
    "ClusterCoordinator",
    "LoadBalancer",
    "ServiceDiscovery",
    "StateSynchronizer",
    "MessageBroker",
    "TaskDistributor",
    "FaultTolerance",
    "ReplicationManager",
    "ConsensusManager",
    "PerformanceMonitor",
    "SecurityManager",
    "LogAggregator",
    # L5 Atomic Subagents
    "NodeRegistrar",
    "NodeHealthChecker",
    "NodeLifecycle",
    "NodeDeregistrar",
    "LeaderElector",
    "ClusterJoiner",
    "ClusterLeaver",
    "ClusterSync",
    "RoundRobin",
    "LeastConnection",
    "ConsistentHash",
    "WeightedDistribution",
    "ServiceRegistrar",
    "ServiceFinder",
    "ServiceHealthChecker",
    "ServiceCache",
    "FullSync",
    "IncrementalSync",
    "ConflictResolver",
    "StateVerifier",
    "Publisher",
    "Subscriber",
    "QueueManager",
    "TopicManager",
    "TaskSplitter",
    "TaskAssigner",
    "TaskTracker",
    "TaskRecoverer",
    "FailureDetector",
    "AutoRecoverer",
    "CircuitBreaker",
    "RetryManager",
    "ReplicationFactor",
    "SyncReplication",
    "AsyncReplication",
    "ReplicationVerifier",
    "RaftImplementation",
    "LeaderHeartbeat",
    "LogReplication",
    "CommitManager",
    "NodeMetricsCollector",
    "ClusterMetricsAggregator",
    "PerfAnalyzer",
    "PerfAlerter",
    "NodeAuth",
    "Encryption",
    "CertManager",
    "AuditLogger",
    "LogCollector",
    "LogIndexer",
    "LogSearcher",
    "LogVisualizer",
    # Raft Engine
    "RaftEngine",
    "RaftRole",
    "RaftLogEntry",
    "RequestVoteArgs",
    "RequestVoteReply",
    "AppendEntriesArgs",
    "AppendEntriesReply",
    # Exceptions
    "DistributedError",
    "NodeManagementError",
    "ClusterCoordinationError",
    "LoadBalancingError",
    "ServiceDiscoveryError",
    "StateSynchronizationError",
    "MessageBrokerError",
    "TaskDistributionError",
    "FaultToleranceError",
    "ReplicationError",
    "ConsensusError",
    "PerformanceMonitoringError",
    "DistributedSecurityError",
    "LogAggregationError",
    # Helper
    "register_all_distributed_agents",
]
