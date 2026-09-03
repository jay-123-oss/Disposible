"""Custom exceptions for the Planning Domain agents."""

from core.exceptions import AgentError


class PlanningError(AgentError):
    """Base exception for all errors originating in the planning layer."""


class IntentClarificationError(PlanningError):
    """Raised when user intent is completely unparsable or unresolvable."""


class QuestionGenerationError(PlanningError):
    """Raised when dynamic question generation fails to formulate valid queries."""


class ValidationError(PlanningError):
    """Raised when user responses or architectural constraints fail validation checks."""


class TechStackSelectionError(PlanningError):
    """Raised when a viable language or framework stack cannot be determined."""


class ArchitectureDesignError(PlanningError):
    """Raised when architecture layer, component, or data flow definition fails."""


class TaskDecompositionError(PlanningError):
    """Raised when plan tasks cannot be decomposed into a valid acyclic graph."""


class RiskAssessmentError(PlanningError):
    """Raised when risk identification, scoring, or mitigation compilation fails."""


class PlanGenerationError(PlanningError):
    """Raised when complete implementation plan synthesis encounters a critical fault."""
