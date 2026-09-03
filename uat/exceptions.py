"""Domain exception hierarchy for the User Acceptance Testing (UAT) layer."""

from __future__ import annotations

from core.exceptions import FractalSystemError


class UATError(FractalSystemError):
    """Base exception for all User Acceptance Testing (UAT) domain errors."""


class EndToEndError(UATError):
    """Raised when an end-to-end user workflow fails."""


class UserScenarioError(UATError):
    """Raised when user scenario simulation (new, existing, admin, guest) fails."""


class BusinessFlowError(UATError):
    """Raised when business transaction workflows (order, payment, notification, reporting) fail."""


class RoleBasedError(UATError):
    """Raised when role-based access control or permission verification fails."""


class UseCaseError(UATError):
    """Raised when primary, secondary, edge, or exceptional use case validation fails."""


class AcceptanceCriteriaError(UATError):
    """Raised when functional, non-functional, UI, or performance criteria are unmet."""


class UIError(UATError):
    """Raised when navigation, responsiveness, accessibility, or usability testing fails."""


class WorkflowError(UATError):
    """Raised when approval, review, publish, or archive workflows fail."""


class IntegrationError(UATError):
    """Raised when API, database, external service, or event integration validation fails."""


class DataIntegrityError(UATError):
    """Raised when data consistency, accuracy, completeness, or validity verification fails."""


class SecurityValidationError(UATError):
    """Raised when authentication, authorization, data protection, or compliance checks fail."""


class PerformanceValidationError(UATError):
    """Raised when response time, throughput, resource usage, or scalability UAT limits fail."""


class FeedbackCollectionError(UATError):
    """Raised when survey generation, feedback sentiment analysis, or satisfaction tracking fails."""
