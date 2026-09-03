"""Custom exceptions for the Testing Domain agents."""

from core.exceptions import AgentError


class TestingError(AgentError):
    """Base exception for all errors originating in the testing layer."""


class TestGenerationError(TestingError):
    """Raised when unit, integration, or scenario test generation fails."""


class TestExecutionError(TestingError):
    """Raised when test execution or assertion verification fails."""


class MockGenerationError(TestingError):
    """Raised when mock objects, monkeypatches, or stub generation fails."""


class TestDataCreationError(TestingError):
    """Raised when test fixture, database seed, or environment creation fails."""


class PerformanceTestError(TestingError):
    """Raised when benchmark, load, or stress testing fails to execute."""


class CoverageError(TestingError):
    """Raised when coverage analysis calculation or threshold checks fail."""


class ValidationError(TestingError):
    """Raised when test result validation or quality gate checking fails."""


class ReportGenerationError(TestingError):
    """Raised when HTML, JSON, or Markdown test report creation fails."""
