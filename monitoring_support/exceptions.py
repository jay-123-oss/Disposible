"""Domain exception hierarchy for the Production Monitoring & Support layer."""

from __future__ import annotations

from core.exceptions import FractalSystemError


class MonitoringSupportError(FractalSystemError):
    """Base exception for all Production Monitoring & Support domain errors."""


class RealTimeMonitoringError(MonitoringSupportError):
    """Raised when real-time telemetry or metrics sampling fails."""


class IncidentDetectionError(MonitoringSupportError):
    """Raised when anomaly detection, pattern recognition, or threshold triggers fail."""


class AlertManagementError(MonitoringSupportError):
    """Raised when alert generation, distribution, or escalation fails."""


class IncidentResponseError(MonitoringSupportError):
    """Raised when incident triage, coordination, or resolution fails."""


class TicketManagementError(MonitoringSupportError):
    """Raised when support ticket creation, assignment, or resolution fails."""


class EscalationError(MonitoringSupportError):
    """Raised when escalation checks, routing, or tracking fails."""


class RootCauseAnalysisError(MonitoringSupportError):
    """Raised when cause analysis, pattern mining, or prevention planning fails."""


class PerformanceMonitoringError(MonitoringSupportError):
    """Raised when latency, throughput, or SLA trend tracking fails."""


class ResourceMonitoringError(MonitoringSupportError):
    """Raised when CPU, memory, disk, or network monitoring triggers errors."""


class ErrorAggregationError(MonitoringSupportError):
    """Raised when error log collection, grouping, or classification fails."""


class LogAnalysisError(MonitoringSupportError):
    """Raised when log parsing, indexing, or query visualization fails."""


class UserFeedbackError(MonitoringSupportError):
    """Raised when user feedback harvesting or sentiment tracking fails."""


class ContinuousImprovementError(MonitoringSupportError):
    """Raised when system optimization mining or improvement execution fails."""
