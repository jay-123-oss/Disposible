"""Production Optimization Layer for the Fractal Multi-Agent Autonomous Coding System.

Exports all 14 specialized production optimization agents (PO1 to PO14) and 52 atomic subagents across L3 to L5,
along with custom exceptions, optimization utilities, and the registration helper `register_all_production_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from core.registry import AgentRegistry
from production.alerting_setup import (
    AlertEscalationManager,
    AlertingSetup,
    CriticalAlertConfigurer,
    InfoAlertConfigurer,
    WarningAlertConfigurer,
)
from production.auto_scaler import AutoScalerUtil
from production.backup_manager import (
    BackupManager,
    BackupRestorer,
    BackupVerifier,
    FullBackupGenerator,
    IncrementalBackupGenerator,
)
from production.cache_manager import (
    CacheInvalidator,
    CacheManager,
    CachePerformanceMonitor,
    CachePopulator,
    CacheStrategyDefiner,
)
from production.cache_optimizer import CacheOptimizerUtil
from production.circuit_breaker import CircuitBreakerUtil, CircuitState
from production.cpu_manager import CpuManagerUtil
from production.cpu_optimizer import CpuOptimizerUtil
from production.dashboard_configurer import DashboardConfigurerUtil
from production.disk_manager import DiskManagerUtil
from production.error_handler import (
    CircuitBreaker,
    ErrorHandlerEnhanced,
    FallbackHandler,
    GlobalErrorCatcher,
    RetryMechanism,
)
from production.exceptions import (
    AlertingSetupError,
    BackupError,
    CacheError,
    ErrorHandlingError,
    LoadBalancingError,
    LoggingOptimizationError,
    MemoryOptimizationError,
    MonitoringSetupError,
    PerformanceOptimizationError,
    ProductionError,
    RecoveryError,
    ResourceManagementError,
    ScalingError,
    SecurityHardeningError,
)
from production.fallback_handler import FallbackHandlerUtil
from production.io_optimizer import IoOptimizerUtil
from production.load_balancer import (
    HealthChecker,
    LoadAlgorithm,
    LoadBalancer,
    RequestDistributor,
    SessionAffinity,
)
from production.logging_optimizer import (
    LogCompressor,
    LoggingOptimizer,
    LogLevelConfigurer,
    LogRetentionManager,
    LogRotator,
)
from production.memory_manager import MemoryManagerUtil
from production.memory_optimizer import (
    CacheMemoryOptimizer,
    GarbageCollectorOptimizer,
    MemoryLeakDetector,
    MemoryOptimizer,
    MemoryUsageTracker,
)
from production.metrics_exporter import MetricsExporterUtil
from production.monitoring_setup import (
    AlertRulesGenerator,
    DashboardConfigurer,
    LogAggregator,
    MetricsExporter,
    MonitoringSetup,
)
from production.performance_optimizer import (
    CpuOptimizer,
    IoOptimizer,
    LatencyReducer,
    NetworkOptimizer,
    PerformanceOptimizer,
)
from production.production_orchestrator import ProductionOrchestrator
from production.profiling import RuntimeProfiler
from production.recovery_manager import (
    DisasterRecoveryPlanner,
    RecoveryCoordinator,
    RecoveryManager,
    RecoveryProcedures,
    RecoveryTester,
)
from production.rate_limiter import RateLimiterUtil
from production.request_distributor import RequestDistributorUtil
from production.resource_manager import (
    CpuManager,
    DiskManager,
    MemoryManager,
    NetworkManager,
    ResourceManager,
)
from production.retry_mechanism import RetryMechanismUtil
from production.scale_manager import (
    AutoScaler,
    ScaleDownTrigger,
    ScaleManager,
    ScaleUpTrigger,
    ScalingMonitor,
)
from production.security_hardener import (
    FirewallConfigurer,
    RateLimiter,
    SecurityHardener,
    SslConfigurer,
    VulnerabilityPatcher,
)
from production.ssl_configurer import SslConfigurerUtil


logger = logging.getLogger("FractalCore.Production")

__all__ = [
    # Master Production Orchestrator
    "ProductionOrchestrator",
    # Performance Optimizer
    "PerformanceOptimizer",
    "CpuOptimizer",
    "IoOptimizer",
    "NetworkOptimizer",
    "LatencyReducer",
    # Memory Optimizer
    "MemoryOptimizer",
    "MemoryUsageTracker",
    "GarbageCollectorOptimizer",
    "CacheMemoryOptimizer",
    "MemoryLeakDetector",
    # Security Hardener
    "SecurityHardener",
    "SslConfigurer",
    "RateLimiter",
    "FirewallConfigurer",
    "VulnerabilityPatcher",
    # Error Handler Enhanced
    "ErrorHandlerEnhanced",
    "GlobalErrorCatcher",
    "RetryMechanism",
    "CircuitBreaker",
    "FallbackHandler",
    # Monitoring Setup
    "MonitoringSetup",
    "MetricsExporter",
    "DashboardConfigurer",
    "LogAggregator",
    "AlertRulesGenerator",
    # Alerting Setup
    "AlertingSetup",
    "CriticalAlertConfigurer",
    "WarningAlertConfigurer",
    "InfoAlertConfigurer",
    "AlertEscalationManager",
    # Logging Optimizer
    "LoggingOptimizer",
    "LogLevelConfigurer",
    "LogRotator",
    "LogCompressor",
    "LogRetentionManager",
    # Resource Manager
    "ResourceManager",
    "CpuManager",
    "MemoryManager",
    "DiskManager",
    "NetworkManager",
    # Backup Manager
    "BackupManager",
    "FullBackupGenerator",
    "IncrementalBackupGenerator",
    "BackupVerifier",
    "BackupRestorer",
    # Recovery Manager
    "RecoveryManager",
    "DisasterRecoveryPlanner",
    "RecoveryProcedures",
    "RecoveryTester",
    "RecoveryCoordinator",
    # Scale Manager
    "ScaleManager",
    "AutoScaler",
    "ScaleUpTrigger",
    "ScaleDownTrigger",
    "ScalingMonitor",
    # Load Balancer
    "LoadBalancer",
    "RequestDistributor",
    "HealthChecker",
    "SessionAffinity",
    "LoadAlgorithm",
    # Cache Manager
    "CacheManager",
    "CacheStrategyDefiner",
    "CachePopulator",
    "CacheInvalidator",
    "CachePerformanceMonitor",
    # Exceptions
    "ProductionError",
    "PerformanceOptimizationError",
    "MemoryOptimizationError",
    "SecurityHardeningError",
    "ErrorHandlingError",
    "MonitoringSetupError",
    "AlertingSetupError",
    "LoggingOptimizationError",
    "ResourceManagementError",
    "BackupError",
    "RecoveryError",
    "ScalingError",
    "LoadBalancingError",
    "CacheError",
    # Utilities
    "CpuOptimizerUtil",
    "IoOptimizerUtil",
    "CacheOptimizerUtil",
    "RuntimeProfiler",
    "SslConfigurerUtil",
    "RateLimiterUtil",
    "CircuitBreakerUtil",
    "CircuitState",
    "RetryMechanismUtil",
    "FallbackHandlerUtil",
    "MetricsExporterUtil",
    "DashboardConfigurerUtil",
    "CpuManagerUtil",
    "MemoryManagerUtil",
    "DiskManagerUtil",
    "AutoScalerUtil",
    "RequestDistributorUtil",
    # Registration Helper
    "register_all_production_agents",
]


def register_all_production_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Register all Production Optimization layer agents into the central AgentRegistry.

    Args:
        registry: The central AgentRegistry singleton.
        parent_agent: Optional supervising orchestrator coordinator.
        max_depth: Global depth ceiling.

    Returns:
        Dict mapping root orchestrator and count of registered agents.
    """
    logger.info("Registering all production optimization domain agents into AgentRegistry...")

    prod_orchestrator = ProductionOrchestrator(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="PO1_PRODUCTION_ORCHESTRATOR",
        auto_spawn_subagents=True,
    )
    registry.register_agent(prod_orchestrator)

    registered_count = 1

    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(prod_orchestrator)

    logger.info("Successfully registered %d production optimization domain agents into registry.", registered_count)
    return {
        "production_orchestrator": prod_orchestrator,
        "total_registered": registered_count,
    }
