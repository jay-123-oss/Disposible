"""Domain exception hierarchy for the Web-Based GUI Dashboard Layer."""

from core.exceptions import FractalSystemError


class GUIError(FractalSystemError):
    """Base exception for all GUI and dashboard failures."""
    pass


class DashboardError(GUIError):
    """Raised when dashboard rendering or widget aggregation fails."""
    pass


class AgentVisualizationError(GUIError):
    """Raised when agent tree traversal or detail rendering fails."""
    pass


class TaskTrackingError(GUIError):
    """Raised when task tracking, history, or creation fails."""
    pass


class CodeEditorError(GUIError):
    """Raised when code editor loading, syntax parsing, or file saving fails."""
    pass


class TestRunnerError(GUIError):
    """Raised when test execution, selection, or coverage parsing fails."""
    pass


class SecurityDashboardError(GUIError):
    """Raised when security score, auth status, or vulnerability viewer fails."""
    pass


class PerformanceDashboardError(GUIError):
    """Raised when response time, throughput, or latency metrics fail."""
    pass


class LogViewerError(GUIError):
    """Raised when log filtering, searching, or exporting fails."""
    pass


class SettingsError(GUIError):
    """Raised when settings fetching, updating, or serialization fails."""
    pass


class UserManagementError(GUIError):
    """Raised when user creation, role assignment, or permission viewer fails."""
    pass


class ReportViewerError(GUIError):
    """Raised when report generation, detailing, or export fails."""
    pass


class APITesterError(GUIError):
    """Raised when API request building, execution, or response parsing fails."""
    pass


class HelpDocsError(GUIError):
    """Raised when documentation viewer, search, or FAQ retrieval fails."""
    pass
