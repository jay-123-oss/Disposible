"""Custom exceptions for the Communication & State Domain agents."""

from core.exceptions import AgentError


class CommStateError(AgentError):
    """Base exception for all errors originating in the communication & state layer."""


class TaskStoreError(CommStateError):
    """Raised when task store CRUD or lifecycle tracking fails."""


class TeamStoreError(CommStateError):
    """Raised when team store grouping or metadata management fails."""


class MailboxError(CommStateError):
    """Raised when inter-agent mailbox delivery, buffering, or receipt fails."""


class RegistryError(CommStateError):
    """Raised when agent registry lookup, heartbeat, or unregistration fails."""


class TraceError(CommStateError):
    """Raised when stigmergic pheromone trace deposition or sensing fails."""


class ArtifactError(CommStateError):
    """Raised when artifact storage, versioning, or retrieval fails."""


class SessionError(CommStateError):
    """Raised when session creation, restoration, or cleanup fails."""


class CheckpointError(CommStateError):
    """Raised when system snapshot checkpoint creation or restore fails."""


class SynchronizationError(CommStateError):
    """Raised when state replication, conflict resolution, or verification fails."""


class EventError(CommStateError):
    """Raised when event publishing, subscription, or dispatch fails."""


class RoutingError(CommStateError):
    """Raised when direct, broadcast, topic, or priority message routing fails."""


class CompressionError(CommStateError):
    """Raised when token-based state compression or decompression fails."""
