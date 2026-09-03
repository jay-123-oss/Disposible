"""Comprehensive Unit Test Suite for Monitoring & Observability Layer Agents (Session 10)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.monitoring import (
    AlertManager,
    AuditLogger,
    BreakpointManager,
    CriticalAlertGenerator,
    DashboardGenerator,
    DriftDetector,
    ErrorAggregator,
    HealthChecker,
    LiveDebugger,
    MetricsCollector,
    MonitoringOrchestrator,
    PerformanceTracker,
    PredictiveAnalyzer,
    ReportGenerator,
    ResourceMonitor,
    TraceCollector,
    register_all_monitoring_agents,
)
from core.registry import AgentRegistry


class TestMonitoringAgents(unittest.TestCase):
    """Test suite covering all 14 monitoring & observability agents and their subagent structures."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_monitoring_orchestrator_spawns_subsystems(self) -> None:
        """Verify MonitoringOrchestrator spawns all 13 L4 coordinators."""
        orch = MonitoringOrchestrator(agent_id="TEST_MON_ORCH", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(orch.debugger)
        self.assertIsNotNone(orch.metrics)
        self.assertIsNotNone(orch.alerts)
        self.assertIsNotNone(orch.drift)
        self.assertIsNotNone(orch.audit)
        self.assertIsNotNone(orch.performance)
        self.assertIsNotNone(orch.resources)
        self.assertIsNotNone(orch.errors)
        self.assertIsNotNone(orch.traces)
        self.assertIsNotNone(orch.dashboards)
        self.assertIsNotNone(orch.reports)
        self.assertIsNotNone(orch.health)
        self.assertIsNotNone(orch.predictive)

        child_names = [c.name for c in orch.children.values()]
        self.assertIn("LiveDebugger", child_names)
        self.assertIn("MetricsCollector", child_names)
        self.assertIn("AlertManager", child_names)
        self.assertIn("DriftDetector", child_names)
        self.assertIn("AuditLogger", child_names)
        self.assertIn("PerformanceTracker", child_names)
        self.assertIn("ResourceMonitor", child_names)
        self.assertIn("ErrorAggregator", child_names)
        self.assertIn("TraceCollector", child_names)
        self.assertIn("DashboardGenerator", child_names)
        self.assertIn("ReportGenerator", child_names)
        self.assertIn("HealthChecker", child_names)
        self.assertIn("PredictiveAnalyzer", child_names)

    def test_live_debugger_breakpoints_and_inspection(self) -> None:
        """Verify LiveDebugger sets breakpoints and inspects execution frames."""
        dbg = LiveDebugger(agent_id="TEST_DBG", auto_spawn_subagents=True, max_depth=7)
        self.assertIsInstance(dbg.bp_mgr, BreakpointManager)

        bp = dbg.set_breakpoint("core/orchestrator.py", 45, condition="task_id == 'T1'")
        self.assertEqual(bp["line_no"], 45)
        self.assertEqual(len(dbg._breakpoints), 1)

        inspected = dbg.inspect_scope({"x": 10, "label": "test", "__private": "hide"})
        self.assertIn("x", inspected)
        self.assertIn("label", inspected)
        self.assertNotIn("__private", inspected)

    def test_metrics_collector_domains(self) -> None:
        """Verify MetricsCollector aggregates system, application, agent, and token metrics."""
        mc = MetricsCollector(agent_id="TEST_MC", auto_spawn_subagents=True, max_depth=7)
        snap = mc.collect_all_metrics()

        self.assertIn("system", snap)
        self.assertIn("application", snap)
        self.assertIn("agent", snap)
        self.assertIn("token", snap)
        self.assertEqual(snap["token"]["max_token_limit"], 4096)

    def test_alert_manager_thresholds_and_escalation(self) -> None:
        """Verify AlertManager classifies severity and escalates stale alerts."""
        am = AlertManager(agent_id="TEST_AM", auto_spawn_subagents=True, max_depth=7)
        self.assertIsInstance(am.crit_gen, CriticalAlertGenerator)

        crit = am.evaluate_metric("cpu_percent", 95.0)
        self.assertIsNotNone(crit)
        self.assertEqual(crit["severity"], "CRITICAL")

        warn = am.evaluate_metric("cpu_percent", 75.0)
        self.assertIsNotNone(warn)
        self.assertEqual(warn["severity"], "WARNING")

        info = am.evaluate_metric("cpu_percent", 55.0)
        self.assertIsNotNone(info)
        self.assertEqual(info["severity"], "INFO")

        # Escalation test
        stale_warn = dict(warn)
        stale_warn["created_at"] = 0  # old
        escalated = am.escalate_alert(stale_warn, escalation_interval_seconds=60)
        self.assertEqual(escalated["severity"], "CRITICAL")

    def test_drift_detector_evaluations(self) -> None:
        """Verify DriftDetector identifies performance, accuracy, and behavior shifts."""
        dd = DriftDetector(agent_id="TEST_DD", auto_spawn_subagents=True, max_depth=7)
        report = dd.detect_drift({
            "baseline_latency_ms": 50.0,
            "current_latency_ms": 70.0,
            "performance_threshold": 20.0,
        })
        self.assertIn("overall_drift_detected", report)
        self.assertEqual(report["evaluated_dimensions"], 3)

    def test_audit_logger_event_streams(self) -> None:
        """Verify AuditLogger records structured events and retrieves history."""
        al = AuditLogger(agent_id="TEST_AL", auto_spawn_subagents=True, max_depth=7)

        al.log_event("SECURITY", {"event": "TOKEN_VERIFIED", "severity": "LOW"})
        al.log_event("ACTION", {"actor": "ORCHESTRATOR", "action": "SUBMIT_TASK"})
        al.log_event("PERFORMANCE", {"metric_name": "task_ms", "duration": 42.0})
        al.log_event("ERROR", {"error_type": "SyntaxError", "error_msg": "invalid syntax"})

        trail = al.get_audit_trail()
        self.assertEqual(len(trail), 4)

        sec_only = al.get_audit_trail(log_type="SECURITY")
        self.assertEqual(len(sec_only), 1)
        self.assertEqual(sec_only[0]["type"], "SECURITY")

    def test_performance_tracker_metrics(self) -> None:
        """Verify PerformanceTracker measures throughput, latency percentiles, and scalability."""
        pt = PerformanceTracker(agent_id="TEST_PT", auto_spawn_subagents=True, max_depth=7)
        res = pt.track_performance({
            "response_times": [40.0, 50.0, 60.0],
            "current_rps": 120.0,
            "latencies": [20.0, 30.0, 45.0, 60.0],
            "concurrent_agents": 10,
        })
        self.assertTrue(res["all_thresholds_met"])
        self.assertIn("p95_ms", res["latency"])
        self.assertTrue(res["scalability"]["scaling_healthy"])

    def test_resource_monitor_capacity_bounds(self) -> None:
        """Verify ResourceMonitor audits CPU, RAM, disk, and network bounds."""
        rm = ResourceMonitor(agent_id="TEST_RM", auto_spawn_subagents=True, max_depth=7)
        report = rm.check_resources({
            "cpu_percent": 30.0,
            "allocated_ram_mb": 4096,
            "disk_percent": 50.0,
            "network_percent": 25.0,
        })
        self.assertTrue(report["all_resources_healthy"])
        self.assertTrue(report["memory"]["within_limits"])

    def test_error_aggregator_and_patterns(self) -> None:
        """Verify ErrorAggregator categorizes errors and detects recurring clusters."""
        ea = ErrorAggregator(agent_id="TEST_EA", auto_spawn_subagents=True, max_depth=7)

        # Ingest 5 syntax errors to breach pattern threshold
        for _ in range(5):
            ea.record_error("SyntaxError: invalid syntax line 12")

        pat = ea.detect_patterns(pattern_threshold=5)
        self.assertTrue(pat["pattern_detected"])
        self.assertEqual(pat["patterns"][0]["category"], "SYNTAX")

    def test_trace_collector_graph_and_breakdown(self) -> None:
        """Verify TraceCollector records spans and parses latency breakdowns."""
        tc = TraceCollector(agent_id="TEST_TC", auto_spawn_subagents=True, max_depth=7)
        s1 = tc.record_span("compile_ast", duration_ms=20.0)
        tc.record_span("run_linter", duration_ms=30.0, parent_span_id=s1["span_id"])

        analysis = tc.analyze_trace()
        self.assertEqual(analysis["graph"]["node_count"], 2)
        self.assertEqual(analysis["graph"]["edge_count"], 1)
        self.assertEqual(analysis["latency_breakdown"]["total_ms"], 50.0)

    def test_dashboard_generator_unified_view(self) -> None:
        """Verify DashboardGenerator produces complete multi-widget observability payload."""
        dg = DashboardGenerator(agent_id="TEST_DG", auto_spawn_subagents=True, max_depth=7)
        dash = dg.generate_complete_dashboard()

        self.assertIn("metrics_view", dash)
        self.assertIn("alerts_view", dash)
        self.assertIn("traces_view", dash)
        self.assertIn("health_view", dash)
        self.assertEqual(dash["health_view"]["overall_status"], "PASSING")

    def test_report_generator_periods(self) -> None:
        """Verify ReportGenerator compiles daily, weekly, and monthly reports."""
        rg = ReportGenerator(agent_id="TEST_RG", auto_spawn_subagents=True, max_depth=7)

        daily = rg.generate_report("DAILY")
        self.assertEqual(daily["period"], "DAILY")

        weekly = rg.generate_report("WEEKLY")
        self.assertEqual(weekly["period"], "WEEKLY")

        monthly = rg.generate_report("MONTHLY")
        self.assertEqual(monthly["period"], "MONTHLY")

    def test_health_checker_vitality(self) -> None:
        """Verify HealthChecker verifies system, agents, services, and dependencies."""
        hc = HealthChecker(agent_id="TEST_HC", auto_spawn_subagents=True, max_depth=7)
        eval_res = hc.check_health()

        self.assertTrue(eval_res["overall_healthy"])
        self.assertTrue(eval_res["system"]["healthy"])
        self.assertTrue(eval_res["services"]["healthy"])

    def test_predictive_analyzer_recommendations(self) -> None:
        """Verify PredictiveAnalyzer forecasts capacity and generates remediation advice."""
        pa = PredictiveAnalyzer(agent_id="TEST_PA", auto_spawn_subagents=True, max_depth=7)
        pred = pa.run_predictive_analysis({
            "current_ram_mb": 7800,  # Near 8192 MB limit
            "growth_rate_mb_hr": 200.0,
            "recent_failure_count": 0,
        })

        self.assertTrue(pred["confidence_threshold_met"])
        self.assertTrue(pred["capacity_prediction"]["critical_exhaustion_soon"])
        self.assertIn("Execute checkpoint cleaner and compress stale agent memory states.", pred["recommendations"])

    def test_monitoring_orchestrator_pipeline(self) -> None:
        """Verify MonitoringOrchestrator runs full end-to-end observability lifecycle."""
        orch = MonitoringOrchestrator(agent_id="TEST_MON_E2E", auto_spawn_subagents=True, max_depth=7)
        envelope = {
            "task_id": "T_MON_E2E",
            "payload": {"cpu": 40.0},
        }
        res = orch.execute_lifecycle(envelope)

        self.assertEqual(res["status"], "COMPLETED")
        rep = res["monitoring_report"]
        self.assertTrue(rep["all_subsystems_healthy"])
        self.assertIn("metrics", rep)
        self.assertIn("dashboard", rep)
        self.assertIn("health", rep)

    def test_register_all_monitoring_agents(self) -> None:
        """Verify registration helper registers all monitoring agents into AgentRegistry."""
        res = register_all_monitoring_agents(self.registry, max_depth=7)
        total = res["total_registered"]
        self.assertGreaterEqual(total, 14)
        self.assertIsNotNone(self.registry.get_agent("M1_MONITORING_ORCHESTRATOR"))


if __name__ == "__main__":
    unittest.main()
