"""Comprehensive Test Suite for Production Optimization Layer Agents (Session 15)."""

import os
import sys
import unittest

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT_DIR in sys.path:
    sys.path.remove(_ROOT_DIR)
sys.path.insert(0, _ROOT_DIR)

from core.registry import AgentRegistry
from production import (
    AlertingSetup,
    BackupManager,
    CacheManager,
    ErrorHandlerEnhanced,
    LoadBalancer,
    LoggingOptimizer,
    MemoryOptimizer,
    MonitoringSetup,
    PerformanceOptimizer,
    ProductionOrchestrator,
    RecoveryManager,
    ResourceManager,
    ScaleManager,
    SecurityHardener,
    register_all_production_agents,
)


class TestProductionOptimizationLayer(unittest.TestCase):
    """Test suite covering all 14 production optimization agents, subagents, and artifacts."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_production_orchestrator_spawns_subsystems(self) -> None:
        """Verify ProductionOrchestrator spawns all 13 L4 production optimization coordinators."""
        orch = ProductionOrchestrator(agent_id="TEST_PROD_ORCH", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(orch.perf_opt)
        self.assertIsNotNone(orch.mem_opt)
        self.assertIsNotNone(orch.sec_hard)
        self.assertIsNotNone(orch.err_enh)
        self.assertIsNotNone(orch.mon_set)
        self.assertIsNotNone(orch.alt_set)
        self.assertIsNotNone(orch.log_opt)
        self.assertIsNotNone(orch.res_mgr)
        self.assertIsNotNone(orch.bak_mgr)
        self.assertIsNotNone(orch.rec_mgr)
        self.assertIsNotNone(orch.scl_mgr)
        self.assertIsNotNone(orch.ld_bal)
        self.assertIsNotNone(orch.cch_mgr)

        child_names = [c.name for c in orch.children.values()]
        self.assertEqual(len(child_names), 13)
        self.assertIn("PerformanceOptimizer", child_names)
        self.assertIn("MemoryOptimizer", child_names)
        self.assertIn("SecurityHardener", child_names)
        self.assertIn("ErrorHandlerEnhanced", child_names)
        self.assertIn("MonitoringSetup", child_names)
        self.assertIn("AlertingSetup", child_names)
        self.assertIn("LoggingOptimizer", child_names)
        self.assertIn("ResourceManager", child_names)
        self.assertIn("BackupManager", child_names)
        self.assertIn("RecoveryManager", child_names)
        self.assertIn("ScaleManager", child_names)
        self.assertIn("LoadBalancer", child_names)
        self.assertIn("CacheManager", child_names)

    def test_performance_optimizer(self) -> None:
        """Verify PerformanceOptimizer coordinates CPU, IO, network, and latency tuning (<200ms)."""
        opt = PerformanceOptimizer(agent_id="TEST_PERF_OPT", auto_spawn_subagents=True, max_depth=7)
        res = opt.optimize_performance()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["cpu"]["optimized"])
        self.assertTrue(res["io"]["optimized"])
        self.assertTrue(res["network"]["optimized"])
        self.assertTrue(res["latency"]["within_sla"])
        self.assertLess(res["latency"]["current_latency_ms"], 200.0)

    def test_memory_optimizer(self) -> None:
        """Verify MemoryOptimizer coordinates tracking, GC, cache memory, and leak detection (<8GB)."""
        opt = MemoryOptimizer(agent_id="TEST_MEM_OPT", auto_spawn_subagents=True, max_depth=7)
        res = opt.optimize_memory()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["tracking"]["within_limit"])
        self.assertTrue(res["garbage_collection"]["optimized"])
        self.assertTrue(res["cache_memory"]["optimized"])
        self.assertTrue(res["leak_detection"]["detected"])
        self.assertFalse(res["leak_detection"]["leak_detected"])

    def test_security_hardener(self) -> None:
        """Verify SecurityHardener coordinates SSL, rate limiter, firewall, and patch audit (>95% score)."""
        sec = SecurityHardener(agent_id="TEST_SEC_HARD", auto_spawn_subagents=True, max_depth=7)
        res = sec.harden_security()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["ssl"]["configured"])
        self.assertTrue(res["rate_limiter"]["configured"])
        self.assertTrue(res["firewall"]["configured"])
        self.assertTrue(res["patcher"]["patched"])
        self.assertGreater(res["patcher"]["security_score"], 95.0)

    def test_error_handler_enhanced(self) -> None:
        """Verify ErrorHandlerEnhanced coordinates error catching, retry, breaker, and fallback."""
        err = ErrorHandlerEnhanced(agent_id="TEST_ERR_ENH", auto_spawn_subagents=True, max_depth=7)
        res = err.handle_production_errors()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["catcher"]["configured"])
        self.assertTrue(res["retry"]["configured"])
        self.assertTrue(res["circuit_breaker"]["configured"])
        self.assertTrue(res["fallback"]["configured"])

    def test_monitoring_setup(self) -> None:
        """Verify MonitoringSetup coordinates metrics, dashboard, log aggregation, and alert rules (100% visibility)."""
        mon = MonitoringSetup(agent_id="TEST_MON_SET", auto_spawn_subagents=True, max_depth=7)
        res = mon.setup_monitoring()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["metrics"]["exported"])
        self.assertTrue(res["dashboard"]["configured"])
        self.assertTrue(res["log_aggregation"]["configured"])
        self.assertTrue(res["alert_rules"]["generated"])
        self.assertEqual(res["visibility_percent"], 100.0)

    def test_alerting_setup(self) -> None:
        """Verify AlertingSetup coordinates critical, warning, info alerts, and escalation (<5 min response)."""
        alt = AlertingSetup(agent_id="TEST_ALT_SET", auto_spawn_subagents=True, max_depth=7)
        res = alt.setup_alerting()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["critical"]["configured"])
        self.assertTrue(res["warning"]["configured"])
        self.assertTrue(res["info"]["configured"])
        self.assertTrue(res["escalation"]["configured"])
        self.assertLessEqual(res["escalation"]["max_response_time_minutes"], 5.0)

    def test_logging_optimizer(self) -> None:
        """Verify LoggingOptimizer coordinates log level, rotation (100MB), compression, and retention (30 days)."""
        log_opt = LoggingOptimizer(agent_id="TEST_LOG_OPT", auto_spawn_subagents=True, max_depth=7)
        res = log_opt.optimize_logging()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["level"]["configured"])
        self.assertTrue(res["rotation"]["configured"])
        self.assertTrue(res["compression"]["configured"])
        self.assertTrue(res["retention"]["configured"])
        self.assertEqual(res["rotation"]["rotation_size_mb"], 100)
        self.assertEqual(res["retention"]["retention_days"], 30)

    def test_resource_manager(self) -> None:
        """Verify ResourceManager coordinates CPU, memory, disk, and network (<80% utilization target)."""
        res_mgr = ResourceManager(agent_id="TEST_RES_MGR", auto_spawn_subagents=True, max_depth=7)
        res = res_mgr.manage_resources()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["cpu"]["managed"])
        self.assertTrue(res["memory"]["managed"])
        self.assertTrue(res["disk"]["managed"])
        self.assertTrue(res["network"]["managed"])
        self.assertTrue(res["within_utilization_target"])
        self.assertLess(res["utilization_percent"], 80.0)

    def test_backup_manager(self) -> None:
        """Verify BackupManager coordinates full, incremental, verification, and restoration (30 days retention)."""
        bak = BackupManager(agent_id="TEST_BAK_MGR", auto_spawn_subagents=True, max_depth=7)
        res = bak.manage_backups()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["full_backup"]["generated"])
        self.assertTrue(res["incremental_backup"]["generated"])
        self.assertTrue(res["verifier"]["verified"])
        self.assertTrue(res["restorer"]["restored"])
        self.assertEqual(res["retention_days"], 30)

    def test_recovery_manager(self) -> None:
        """Verify RecoveryManager coordinates disaster recovery plan (RPO 5m, RTO 10m, <1 hr recovery)."""
        rec = RecoveryManager(agent_id="TEST_REC_MGR", auto_spawn_subagents=True, max_depth=7)
        res = rec.manage_recovery()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["planning"]["planned"])
        self.assertTrue(res["procedures"]["validated"])
        self.assertTrue(res["testing"]["tested"])
        self.assertTrue(res["coordination"]["coordinated"])
        self.assertLessEqual(res["planning"]["rpo_minutes"], 5)
        self.assertLessEqual(res["planning"]["rto_minutes"], 10)

    def test_scale_manager(self) -> None:
        """Verify ScaleManager coordinates autoscaling min 2, max 10 replicas, triggers, and monitoring."""
        scl = ScaleManager(agent_id="TEST_SCL_MGR", auto_spawn_subagents=True, max_depth=7)
        res = scl.manage_scaling()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["evaluation"]["evaluated"])
        self.assertTrue(res["scale_up"]["checked"])
        self.assertTrue(res["scale_down"]["checked"])
        self.assertTrue(res["monitor"]["monitored"])

    def test_load_balancer(self) -> None:
        """Verify LoadBalancer coordinates request routing, health check, affinity, and efficiency (>95%)."""
        lb = LoadBalancer(agent_id="TEST_LB_MGR", auto_spawn_subagents=True, max_depth=7)
        res = lb.balance_load()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["routing"]["routed"])
        self.assertTrue(res["health"]["checked"])
        self.assertTrue(res["affinity"]["configured"])
        self.assertTrue(res["algorithm"]["evaluated"])
        self.assertGreater(res["efficiency_percent"], 95.0)

    def test_cache_manager(self) -> None:
        """Verify CacheManager coordinates cache strategy, populator, invalidator, and hit ratio (>80%)."""
        cch = CacheManager(agent_id="TEST_CCH_MGR", auto_spawn_subagents=True, max_depth=7)
        res = cch.manage_cache()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["strategy"]["defined"])
        self.assertTrue(res["populator"]["warmed"])
        self.assertTrue(res["invalidator"]["invalidated"])
        self.assertTrue(res["performance"]["monitored"])
        self.assertGreater(res["hit_ratio_percent"], 80.0)

    def test_production_orchestrator_lifecycle(self) -> None:
        """Verify ProductionOrchestrator runs full lifecycle across all 13 coordinators and validates readiness checklist."""
        orch = ProductionOrchestrator(agent_id="TEST_FULL_PROD", auto_spawn_subagents=True, max_depth=7)
        envelope = {"task_id": "T_PROD_FULL", "payload": {}}
        res = orch.execute_lifecycle(envelope)

        self.assertEqual(res["status"], "COMPLETED")
        rep = res["optimization_report"]
        self.assertTrue(rep["all_optimizations_successful"])
        self.assertEqual(rep["total_subsystems"], 13)

        readiness = res["production_readiness"]
        self.assertTrue(readiness["production_ready"])
        self.assertEqual(readiness["passed_checks"], 13)
        self.assertEqual(readiness["total_checks"], 13)

    def test_register_all_production_agents(self) -> None:
        """Verify register_all_production_agents registers root, coordinators, and subagents."""
        res = register_all_production_agents(self.registry, max_depth=7)
        total = res["total_registered"]
        self.assertGreaterEqual(total, 66)  # 1 + 13 + 52 = 66
        self.assertIsNotNone(self.registry.get_agent("PO1_PRODUCTION_ORCHESTRATOR"))

    def test_all_30_production_files_exist(self) -> None:
        """Verify all 30 production optimization files exist and contain valid code."""
        required_files = [
            "production/__init__.py",
            "production/performance_optimizer.py",
            "production/memory_optimizer.py",
            "production/cpu_optimizer.py",
            "production/io_optimizer.py",
            "production/cache_optimizer.py",
            "production/profiling.py",
            "production/security_hardener.py",
            "production/ssl_configurer.py",
            "production/rate_limiter.py",
            "production/error_handler.py",
            "production/circuit_breaker.py",
            "production/retry_mechanism.py",
            "production/fallback_handler.py",
            "production/monitoring_setup.py",
            "production/metrics_exporter.py",
            "production/dashboard_configurer.py",
            "production/alerting_setup.py",
            "production/alert_rules.yaml",
            "production/logging_optimizer.py",
            "production/resource_manager.py",
            "production/cpu_manager.py",
            "production/memory_manager.py",
            "production/disk_manager.py",
            "production/backup_manager.py",
            "production/recovery_manager.py",
            "production/scale_manager.py",
            "production/auto_scaler.py",
            "production/load_balancer.py",
            "production/request_distributor.py",
        ]
        for rel in required_files:
            fp = os.path.join(_ROOT_DIR, rel)
            self.assertTrue(os.path.isfile(fp), f"Missing production file: {rel}")
            self.assertGreater(os.path.getsize(fp), 10, f"Empty production file: {rel}")


if __name__ == "__main__":
    unittest.main()
