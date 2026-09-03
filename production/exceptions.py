"""Domain exception hierarchy for the Production Optimization layer."""

from __future__ import annotations

from core.exceptions import FractalSystemError


class ProductionError(FractalSystemError):
    """Base exception for all Production Optimization domain errors."""


class PerformanceOptimizationError(ProductionError):
    """Raised when CPU, IO, network, or latency optimization operations fail."""


class MemoryOptimizationError(ProductionError):
    """Raised when memory tracking, GC tuning, cache sizing, or leak detection fails."""


class SecurityHardeningError(ProductionError):
    """Raised when SSL/TLS configuration, rate limiting, firewall, or patching fails."""


class ErrorHandlingError(ProductionError):
    """Raised when circuit breaker, retry mechanism, or fallback handler fails."""


class MonitoringSetupError(ProductionError):
    """Raised when metrics export, dashboard config, or log aggregation fails."""


class AlertingSetupError(ProductionError):
    """Raised when critical/warning alert setup or alert escalation fails."""


class LoggingOptimizationError(ProductionError):
    """Raised when log level, rotation, compression, or retention fails."""


class ResourceManagementError(ProductionError):
    """Raised when CPU, memory, disk, or network resource manager fails."""


class BackupError(ProductionError):
    """Raised when full or incremental backup, verification, or restore fails."""


class RecoveryError(ProductionError):
    """Raised when disaster recovery planning, procedures, or coordination fails."""


class ScalingError(ProductionError):
    """Raised when auto-scaling, scale triggers, or scaling monitoring fails."""


class LoadBalancingError(ProductionError):
    """Raised when request distribution, health check, or affinity fails."""


class CacheError(ProductionError):
    """Raised when cache strategy, population, invalidation, or hit ratio fails."""
