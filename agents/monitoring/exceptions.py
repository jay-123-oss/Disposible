"""Custom exceptions for the Monitoring & Observability Domain agents."""

from core.exceptions import AgentError


class MonitoringError(AgentError):
    """Base exception for all errors originating in the monitoring & observability layer."""


class DebuggerError(MonitoringError):
    """Raised when interactive breakpoint or stack frame inspection fails."""


class MetricsCollectionError(MonitoringError):
    """Raised when hardware, runtime, or token metrics extraction fails."""


class AlertError(MonitoringError):
    """Raised when alert thresholding, filtering, or escalation fails."""


class DriftDetectionError(MonitoringError):
    """Raised when model, performance, or behavioral drift analysis fails."""


class AuditLogError(MonitoringError):
    """Raised when structured security or action audit log flushing fails."""


class PerformanceTrackingError(MonitoringError):
    """Raised when latency, throughput, or responsiveness profiling fails."""


class ResourceMonitoringError(MonitoringError):
    """Raised when host CPU, memory, disk, or network monitoring fails."""


class ErrorAggregationError(MonitoringError):
    """Raised when exception classification, grouping, or pattern detection fails."""


class TraceCollectionError(MonitoringError):
    """Raised when distributed span extraction or trace graph generation fails."""


class DashboardGenerationError(MonitoringError):
    """Raised when real-time dashboard visualization rendering fails."""


class ReportGenerationError(MonitoringError):
    """Raised when scheduled diagnostic report aggregation fails."""


class HealthCheckError(MonitoringError):
    """Raised when node, agent, or dependency health verification fails."""


class PredictiveAnalysisError(MonitoringError):
    """Raised when anomaly forecasting or failure prediction modeling fails."""
