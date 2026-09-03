"""Domain exception hierarchy for the AI & ML Extensions layer."""

from __future__ import annotations

from core.exceptions import FractalSystemError


class AIExtensionError(FractalSystemError):
    """Base exception for all AI & ML extension errors."""


class ModelSelectionError(AIExtensionError):
    """Raised when model capability evaluation or routing fails."""


class CostOptimizationError(AIExtensionError):
    """Raised when token budgeting or smart caching fails."""


class EmbeddingError(AIExtensionError):
    """Raised when vectorizing code or generating embeddings fails."""


class SemanticSearchError(AIExtensionError):
    """Raised when vector similarity search or context retrieval fails."""


class AutoCompletionError(AIExtensionError):
    """Raised when token suggestion or auto-completion ranking fails."""


class CodeGenerationError(AIExtensionError):
    """Raised when generating multi-language code artifacts fails."""


class QualityPredictionError(AIExtensionError):
    """Raised when complexity, maintainability, or readability scoring fails."""


class BugPredictionError(AIExtensionError):
    """Raised when vulnerability scanning or bug probability analysis fails."""


class PerformancePredictionError(AIExtensionError):
    """Raised when algorithmic complexity or bottleneck detection fails."""


class TestGenerationError(AIExtensionError):
    """Raised when automated test or mock generation fails."""


class RefactoringError(AIExtensionError):
    """Raised when code smell detection or refactoring planning fails."""


class CodeReviewError(AIExtensionError):
    """Raised when automated code inspection or comment generation fails."""


class DocumentationError(AIExtensionError):
    """Raised when automatic documentation synthesis or validation fails."""


class FineTuningError(AIExtensionError):
    """Raised when dataset preparation, fine-tuning, or model evaluation fails."""


class MultiModalError(AIExtensionError):
    """Raised when multi-modal image, audio, or video processing fails."""
