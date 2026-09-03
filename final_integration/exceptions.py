"""Domain exception hierarchy for the Final System Integration & Deployment layer."""

from __future__ import annotations

from core.exceptions import FractalSystemError


class FinalIntegrationError(FractalSystemError):
    """Base exception for all Final Integration & Deployment domain errors."""


class SystemAssemblyError(FinalIntegrationError):
    """Raised when component collection, assembly, or integrity verification fails."""


class DependencyResolutionError(FinalIntegrationError):
    """Raised when dependency extraction, version pinning, or conflict resolution fails."""


class ConfigurationMergeError(FinalIntegrationError):
    """Raised when configuration collection, merging, or validation fails."""


class CodeValidationError(FinalIntegrationError):
    """Raised when syntax, typing, linting, or quality checks fail."""


class DeploymentExecutionError(FinalIntegrationError):
    """Raised when Docker, Kubernetes, Cloud, or Local deployment execution fails."""


class ServiceOrchestrationError(FinalIntegrationError):
    """Raised when service startup, connection, health checking, or monitoring fails."""


class HealthVerificationError(FinalIntegrationError):
    """Raised when overall system, agent, service, or performance health check fails."""


class GoLiveError(FinalIntegrationError):
    """Raised when readiness verification, signoff collection, or go-live execution fails."""


class SmokeTestError(FinalIntegrationError):
    """Raised when critical flows, API, UI, or integration smoke tests fail."""


class RollbackError(FinalIntegrationError):
    """Raised when automated rollback planning, execution, or verification fails."""


class PostDeploymentVerificationError(FinalIntegrationError):
    """Raised when post-deployment functional, performance, security, or user checks fail."""


class HandoverError(FinalIntegrationError):
    """Raised when documentation packaging, operations guides, or handover coordination fails."""


class SignoffError(FinalIntegrationError):
    """Raised when final signoff checklists, approvals, or signoff reporting fails."""
