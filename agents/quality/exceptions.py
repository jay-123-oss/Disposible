"""Custom exceptions for the Quality Domain agents."""

from core.exceptions import AgentError


class QualityError(AgentError):
    """Base exception for all errors originating in the quality audit layer."""


class FormattingError(QualityError):
    """Raised when code indentation, spacing, or line length fails validation."""


class StyleError(QualityError):
    """Raised when code violates naming conventions or import ordering rules."""


class ComplexityError(QualityError):
    """Raised when code exceeds cyclomatic or cognitive complexity limits."""


class BestPracticeError(QualityError):
    """Raised when design patterns, SOLID, or DRY principles are violated."""


class DocumentationError(QualityError):
    """Raised when JSDoc, OpenAPI/Swagger, or README generation fails."""


class ReviewError(QualityError):
    """Raised when code review detects critical logic flaws or bugs."""


class PerformanceError(QualityError):
    """Raised when algorithmic performance or query profiling fails."""


class RefactoringError(QualityError):
    """Raised when duplicate code or refactoring suggestions fail analysis."""


class DependencyError(QualityError):
    """Raised when dependency versioning, security, or compatibility fails."""


class ScoringError(QualityError):
    """Raised when composite quality scoring calculation fails."""
