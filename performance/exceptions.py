"""Domain exception hierarchy for the Performance & Load Testing layer."""

from __future__ import annotations

from core.exceptions import FractalSystemError


class PerformanceTestError(FractalSystemError):
    """Base exception for all Performance and Load Testing domain errors."""


class LoadTestError(PerformanceTestError):
    """Raised when load generation, concurrent user simulation, or ramp-up fails."""


class StressTestError(PerformanceTestError):
    """Raised when stress testing, breakpoint finding, or resource exhaustion fails."""


class SpikeTestError(PerformanceTestError):
    """Raised when sudden surge, drop, or oscillation testing fails."""


class SoakTestError(PerformanceTestError):
    """Raised when extended duration soak testing or endurance tracking fails."""


class ScalabilityTestError(PerformanceTestError):
    """Raised when horizontal/vertical scaling or elasticity benchmarking fails."""


class BenchmarkError(PerformanceTestError):
    """Raised when system, agent, API, or database benchmarking fails."""


class AnalysisError(PerformanceTestError):
    """Raised when response time, throughput, latency, or error rate analysis fails."""


class MonitoringError(PerformanceTestError):
    """Raised when resource monitoring (CPU, memory, disk, network) fails."""


class MetricsError(PerformanceTestError):
    """Raised when request counting, response timing, or metrics collection fails."""


class ReportError(PerformanceTestError):
    """Raised when HTML, JSON, CSV, or graph report generation fails."""


class ComparisonError(PerformanceTestError):
    """Raised when baseline or previous run comparison fails."""


class ThresholdError(PerformanceTestError):
    """Raised when latency, throughput, error rate, or resource thresholds are violated."""


class RecommendationError(PerformanceTestError):
    """Raised when performance or scaling recommendation generation fails."""
