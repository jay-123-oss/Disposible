"""Domain exception hierarchy for the Final Documentation & Project Closure layer."""

from __future__ import annotations

from core.exceptions import FractalSystemError


class ClosureError(FractalSystemError):
    """Base exception for all Project Closure domain errors."""


class DocumentationReviewError(ClosureError):
    """Raised when documentation audit or completeness review fails."""


class QualityAuditError(ClosureError):
    """Raised when code, test, process, or outcome quality fails thresholds."""


class PerformanceAuditError(ClosureError):
    """Raised when latency, throughput, or capacity audits fail."""


class SecurityAuditError(ClosureError):
    """Raised when security audits detect critical or unresolved vulnerabilities."""


class ComplianceAuditError(ClosureError):
    """Raised when regulatory compliance (GDPR, SOC2, etc.) fails."""


class LessonsLearnedError(ClosureError):
    """Raised when retrospective or lessons learned harvesting fails."""


class ReportGenerationError(ClosureError):
    """Raised when final closure executive or detailed report generation fails."""


class RoadmapPlanningError(ClosureError):
    """Raised when future architecture and feature roadmap planning fails."""


class KnowledgeTransferError(ClosureError):
    """Raised when operations handover documentation or training fails."""


class FinalReviewError(ClosureError):
    """Raised when final review board execution or action item closure fails."""


class SignoffError(ClosureError):
    """Raised when stakeholder final signoff collection or validation fails."""


class ArchiveError(ClosureError):
    """Raised when artifact collection, indexing, or archival storage fails."""


class CelebrationError(ClosureError):
    """Raised when project completion celebration or recognition planning fails."""
