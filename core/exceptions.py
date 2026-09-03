"""Custom exceptions for the Fractal Multi-Agent Coding System.

All exceptions inherit from FractalSystemError to allow clean global catching
while retaining fine-grained hierarchy for component-level recovery.
"""

from typing import Optional, Any, Dict


class FractalSystemError(Exception):
    """Base exception for all errors within the fractal multi-agent system."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception details to dictionary for structured logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class AgentError(FractalSystemError):
    """Raised when an agent encounters an internal processing or execution fault."""


class OrchestratorError(FractalSystemError):
    """Raised when the meta-orchestrator encounters a lifecycle or coordination failure."""


class CommunicationError(FractalSystemError):
    """Raised when a message frame cannot be routed, serialized, or verified."""


class SandboxError(FractalSystemError):
    """Raised when code execution in the sandbox violates constraints or fails abruptly."""


class QualityGateError(FractalSystemError):
    """Raised when an artifact or transition fails to pass a mandatory quality gate."""


class StateError(FractalSystemError):
    """Raised when state serialization, checkpointing, or recovery encounters an error."""


class DepthLimitError(AgentError):
    """Raised when an agent attempts to spawn sub-agents beyond the configured max depth."""


class ResourceLimitError(FractalSystemError):
    """Raised when memory, process count, or token budget quotas are exceeded."""
