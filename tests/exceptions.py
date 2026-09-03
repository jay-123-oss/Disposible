"""Exception hierarchy for the Testing & Validation Layer."""

from __future__ import annotations


class TestError(Exception):
    """Base exception for all testing and validation errors."""
    pass


class SystemTestError(TestError):
    """Raised when system/end-to-end test execution fails."""
    pass


class IntegrationTestError(TestError):
    """Raised when API, database, or external service integration tests fail."""
    pass


class UnitTestError(TestError):
    """Raised when unit testing of agents, models, or helpers fails."""
    pass


class PerformanceTestError(TestError):
    """Raised when latency, throughput, load, or stress thresholds fail."""
    pass


class SecurityTestError(TestError):
    """Raised when security audit, auth, injection, or compliance verification fails."""
    pass


class QualityTestError(TestError):
    """Raised when code quality, documentation, style, or complexity audits fail."""
    pass


class ValidationError(TestError):
    """Raised when output or expectation validation encounters invariant violations."""
    pass


class CoverageError(TestError):
    """Raised when code coverage metrics fall below required thresholds."""
    pass


class TestDataError(TestError):
    """Raised when test fixture loading or data generation fails."""
    pass


class MockServerError(TestError):
    """Raised when dependency or API mocking fails."""
    pass


class AggregationError(TestError):
    """Raised when test result collection, grouping, or summarization fails."""
    pass


class ReportGenerationError(TestError):
    """Raised when compiling HTML, JSON, Markdown, or JUnit reports fails."""
    pass
