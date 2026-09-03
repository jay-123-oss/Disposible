"""Custom exceptions for the Integration & Assembly Domain agents."""

from core.exceptions import AgentError


class IntegrationError(AgentError):
    """Base exception for all errors originating in the integration & assembly layer."""


class InitializationError(IntegrationError):
    """Raised when system bootstrap or component initialization fails."""


class AgentFactoryError(IntegrationError):
    """Raised when dynamic agent instantiation or registration fails."""


class DependencyError(IntegrationError):
    """Raised when core or agent dependency injection fails."""


class ConfigurationError(IntegrationError):
    """Raised when configuration file parsing or validation fails."""


class InterfaceError(IntegrationError):
    """Raised when CLI, API, or Web interface generation fails."""


class WorkflowError(IntegrationError):
    """Raised when linear, parallel, conditional, or recursive workflow execution fails."""


class ShutdownError(IntegrationError):
    """Raised when graceful system or agent termination fails."""


class HealthError(IntegrationError):
    """Raised when subsystem health validation or health reporting fails."""


class SessionError(IntegrationError):
    """Raised when session creation, persistence, or cleanup fails."""


class ResourceError(IntegrationError):
    """Raised when memory, thread, or connection management limits are breached."""


class ContextError(IntegrationError):
    """Raised when cross-agent context propagation or retrieval fails."""
