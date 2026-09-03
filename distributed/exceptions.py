"""Custom exceptions for the Distributed Architecture Layer."""

from __future__ import annotations


class DistributedError(Exception):
    """Base exception for all distributed architecture errors."""
    pass


class NodeManagementError(DistributedError):
    """Raised when node registration, health check, or lifecycle operations fail."""
    pass


class ClusterCoordinationError(DistributedError):
    """Raised when leader election, cluster joining, or cluster synchronization fails."""
    pass


class LoadBalancingError(DistributedError):
    """Raised when load balancing algorithms or routing fail."""
    pass


class ServiceDiscoveryError(DistributedError):
    """Raised when service registration, discovery, or heartbeat operations fail."""
    pass


class StateSynchronizationError(DistributedError):
    """Raised when full/incremental state sync or conflict resolution fails."""
    pass


class MessageBrokerError(DistributedError):
    """Raised when message publish/subscribe or queue management fails."""
    pass


class TaskDistributionError(DistributedError):
    """Raised when task splitting, assignment, or recovery fails."""
    pass


class FaultToleranceError(DistributedError):
    """Raised when failure detection, recovery, or circuit breaking fails."""
    pass


class ReplicationError(DistributedError):
    """Raised when data replication or quorum verification fails."""
    pass


class ConsensusError(DistributedError):
    """Raised when Raft consensus, heartbeat, or log replication fails."""
    pass


class PerformanceMonitoringError(DistributedError):
    """Raised when metrics collection or cluster performance alerting fails."""
    pass


class DistributedSecurityError(DistributedError):
    """Raised when mutual TLS, node authentication, or cert validation fails."""
    pass


class LogAggregationError(DistributedError):
    """Raised when distributed log collection, indexing, or search fails."""
    pass
