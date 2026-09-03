"""Unit tests for the Production Monitoring & Support Layer (PM1-PM14 + 52 subagents + dashboards + alerts + runbooks)."""

from pathlib import Path
import unittest

from core.registry import AgentRegistry
from monitoring_support import (
    AlertManager,
    ContinuousImprover,
    ErrorAggregator,
    EscalationManager,
    IncidentDetector,
    IncidentResponder,
    LogAnalyzer,
    MonitoringSupportError,
    PerformanceMonitor,
    ProductionMonitoringOrchestrator,
    RealTimeMonitor,
    ResourceMonitor,
    RootCauseAnalyzer,
    SupportTicketManager,
    UserFeedbackMonitor,
    register_all_monitoring_support_agents,
)
from monitoring_support.dashboards import load_dashboard


class TestMonitoringSupport(unittest.TestCase):
    """Test suite verifying all production monitoring coordinators, workers, dashboards, and SLA metrics."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()
        self.orchestrator = ProductionMonitoringOrchestrator(agent_id="PM1_TEST_ORCHESTRATOR")

    def tearDown(self) -> None:
        self.registry.clear()

    def test_01_all_30_files_exist(self) -> None:
        """Verify all 30 production monitoring & support files exist and are non-empty."""
        expected_files = [
            "monitoring_support/__init__.py",
            "monitoring_support/production_monitoring_orchestrator.py",
            "monitoring_support/real_time_monitor.py",
            "monitoring_support/incident_detector.py",
            "monitoring_support/alert_manager.py",
            "monitoring_support/incident_responder.py",
            "monitoring_support/support_ticket_manager.py",
            "monitoring_support/escalation_manager.py",
            "monitoring_support/root_cause_analyzer.py",
            "monitoring_support/performance_monitor.py",
            "monitoring_support/resource_monitor.py",
            "monitoring_support/error_aggregator.py",
            "monitoring_support/log_analyzer.py",
            "monitoring_support/user_feedback_monitor.py",
            "monitoring_support/continuous_improver.py",
            "monitoring_support/dashboards/__init__.py",
            "monitoring_support/dashboards/system_dashboard.json",
            "monitoring_support/dashboards/agent_dashboard.json",
            "monitoring_support/dashboards/performance_dashboard.json",
            "monitoring_support/dashboards/alert_dashboard.json",
            "monitoring_support/alerts/alert_rules.yaml",
            "monitoring_support/alerts/notification_channels.yaml",
            "monitoring_support/alerts/alert_templates.md",
            "monitoring_support/runbooks/incident_response.md",
            "monitoring_support/runbooks/escalation_procedures.md",
            "monitoring_support/runbooks/recovery_procedures.md",
            "monitoring_support/runbooks/rollback_procedures.md",
            "monitoring_support/monitoring_config.yaml",
            "monitoring_support/support_config.yaml",
            "monitoring_support/improvement_config.yaml",
        ]
        base_dir = Path(__file__).parent.parent
        for rel_path in expected_files:
            p = base_dir / rel_path
            self.assertTrue(p.exists(), f"File does not exist: {rel_path}")
            self.assertGreater(p.stat().st_size, 0, f"File is empty: {rel_path}")

    def test_02_orchestrator_spawns_all_13_coordinators(self) -> None:
        """Verify ProductionMonitoringOrchestrator instantiates all 13 coordinators."""
        coordinators = [
            self.orchestrator.rt_mon,
            self.orchestrator.inc_det,
            self.orchestrator.alr_mgr,
            self.orchestrator.inc_rsp,
            self.orchestrator.tck_mgr,
            self.orchestrator.esc_mgr,
            self.orchestrator.rca_anl,
            self.orchestrator.prf_mon,
            self.orchestrator.res_mon,
            self.orchestrator.err_agg,
            self.orchestrator.log_anl,
            self.orchestrator.fbk_mon,
            self.orchestrator.cnt_imp,
        ]
        for coord in coordinators:
            self.assertIsNotNone(coord)
            self.assertEqual(coord.depth, 1)

    def test_03_each_coordinator_spawns_4_grandchild_agents(self) -> None:
        """Verify each of the 13 coordinators instantiates 4 atomic grandchild workers (depth=2)."""
        coordinators = [
            (self.orchestrator.rt_mon, 4),
            (self.orchestrator.inc_det, 4),
            (self.orchestrator.alr_mgr, 4),
            (self.orchestrator.inc_rsp, 4),
            (self.orchestrator.tck_mgr, 4),
            (self.orchestrator.esc_mgr, 4),
            (self.orchestrator.rca_anl, 4),
            (self.orchestrator.prf_mon, 4),
            (self.orchestrator.res_mon, 4),
            (self.orchestrator.err_agg, 4),
            (self.orchestrator.log_anl, 4),
            (self.orchestrator.fbk_mon, 4),
            (self.orchestrator.cnt_imp, 4),
        ]
        for coord, expected_count in coordinators:
            self.assertEqual(len(coord.children), expected_count)
            for sub in coord.children.values():
                self.assertEqual(sub.depth, 2)

    def test_04_registry_registers_all_66_agents(self) -> None:
        """Verify registration helper registers exactly 66 agents (1 + 13 + 52) within memory limits."""
        res = register_all_monitoring_support_agents(self.registry, self.orchestrator)
        self.assertEqual(res["total_registered"], 66)
        all_agents = self.registry.get_all_agents()
        self.assertEqual(len(all_agents), 66)
        self.assertLessEqual(self.registry._allocated_ram_mb, 8192)

    def test_05_real_time_monitor_execution(self) -> None:
        """Verify RealTimeMonitor samples system, agent, service, and business telemetry."""
        res = self.orchestrator.rt_mon.collect_realtime_metrics()
        self.assertTrue(res["all_metrics_collected"])

    def test_06_incident_detector_execution(self) -> None:
        """Verify IncidentDetector executes anomaly, pattern, threshold, and predictive detections."""
        res = self.orchestrator.inc_det.detect_incidents()
        self.assertFalse(res["incident_detected"])
        self.assertGreater(res["detection_accuracy_percent"], 95.0)

    def test_07_alert_manager_execution(self) -> None:
        """Verify AlertManager tests generation, distribution, escalation, and closure."""
        res = self.orchestrator.alr_mgr.manage_alerts()
        self.assertTrue(res["all_alerts_managed"])
        self.assertLess(res["response_time_minutes"], 5.0)

    def test_08_incident_responder_execution(self) -> None:
        """Verify IncidentResponder handles triage, coordination, resolution, and closure."""
        res = self.orchestrator.inc_rsp.respond_to_incident()
        self.assertTrue(res["incident_resolved"])
        self.assertTrue(res["resolution_time_under_1hr"])

    def test_09_support_ticket_manager_execution(self) -> None:
        """Verify SupportTicketManager manages creation, classification, assignment, and resolution."""
        res = self.orchestrator.tck_mgr.manage_support_tickets()
        self.assertTrue(res["all_tickets_managed"])
        self.assertTrue(res["sla_resolution_under_4h"])

    def test_10_escalation_manager_execution(self) -> None:
        """Verify EscalationManager executes escalation check, promotion, notifications, and tracking."""
        res = self.orchestrator.esc_mgr.manage_escalations()
        self.assertTrue(res["escalation_successful"])
        self.assertTrue(res["sla_under_15min"])

    def test_11_root_cause_analyzer_execution(self) -> None:
        """Verify RootCauseAnalyzer identifies cause, analyzes patterns, recommends and plans prevention."""
        res = self.orchestrator.rca_anl.analyze_root_cause()
        self.assertTrue(res["rca_completed"])
        self.assertTrue(res["rca_completion_under_24h"])

    def test_12_performance_monitor_execution(self) -> None:
        """Verify PerformanceMonitor tracks latency, throughput, usage, and trends."""
        res = self.orchestrator.prf_mon.monitor_performance()
        self.assertTrue(res["all_performance_healthy"])
        self.assertGreater(res["sla_compliance_percent"], 99.9)

    def test_13_resource_monitor_execution(self) -> None:
        """Verify ResourceMonitor checks CPU, memory, disk, and network."""
        res = self.orchestrator.res_mon.monitor_resources()
        self.assertTrue(res["all_resources_nominal"])

    def test_14_error_aggregator_execution(self) -> None:
        """Verify ErrorAggregator captures, classifies, analyzes errors and confirms >50% reduction."""
        res = self.orchestrator.err_agg.aggregate_errors()
        self.assertTrue(res["all_errors_aggregated"])
        self.assertGreaterEqual(res["trends"]["error_reduction_achieved_percent"], 50.0)

    def test_15_log_analyzer_execution(self) -> None:
        """Verify LogAnalyzer parses, indexes, searches (<1s), and visualizes logs."""
        res = self.orchestrator.log_anl.analyze_logs()
        self.assertTrue(res["all_logs_analyzed"])
        self.assertTrue(res["search_sla_satisfied"])

    def test_16_user_feedback_monitor_execution(self) -> None:
        """Verify UserFeedbackMonitor gathers feedback, computes CSAT (>4.5), and creates actions."""
        res = self.orchestrator.fbk_mon.monitor_user_feedback()
        self.assertTrue(res["all_feedback_reviewed"])
        self.assertGreaterEqual(res["sentiment"]["csat_score"], 4.5)

    def test_17_continuous_improver_execution(self) -> None:
        """Verify ContinuousImprover analyzes metrics, finds optimizations, and yields >20% gain."""
        res = self.orchestrator.cnt_imp.execute_continuous_improvement()
        self.assertTrue(res["improvement_cycle_completed"])
        self.assertTrue(res["performance_gain_exceeds_20_percent"])

    def test_18_sla_requirements_matrix(self) -> None:
        """Verify all 9 official SLA targets from Section 8 are satisfied."""
        matrix = self.orchestrator.evaluate_support_operations()
        self.assertTrue(matrix["all_slas_met"])
        self.assertTrue(matrix["metrics"]["system_uptime"]["passed"])
        self.assertTrue(matrix["metrics"]["response_time"]["passed"])
        self.assertTrue(matrix["metrics"]["error_rate"]["passed"])
        self.assertTrue(matrix["metrics"]["incident_response"]["passed"])
        self.assertTrue(matrix["metrics"]["incident_resolution"]["passed"])
        self.assertTrue(matrix["metrics"]["ticket_resolution"]["passed"])
        self.assertTrue(matrix["metrics"]["escalation_time"]["passed"])
        self.assertTrue(matrix["metrics"]["rca_completion"]["passed"])
        self.assertTrue(matrix["metrics"]["user_satisfaction"]["passed"])

    def test_19_full_monitoring_orchestrator_lifecycle(self) -> None:
        """Verify complete orchestrator run across all 13 subsystems and OPERATIONAL status."""
        envelope = {"payload": {"cycle": "PROD_HOURLY_AUDIT"}}
        self.orchestrator.initialize(envelope)
        result = self.orchestrator.process(envelope)
        validated = self.orchestrator.validate(result)
        self.assertEqual(validated["status"], "COMPLETED")
        self.assertTrue(validated["monitoring_report"]["monitoring_healthy"])
        self.assertEqual(validated["monitoring_report"]["system_status"], "OPERATIONAL")
        self.orchestrator.cleanup()

    def test_20_load_json_dashboards(self) -> None:
        """Verify all 4 JSON dashboards can be parsed and contain required panels."""
        dashboards = ["system_dashboard", "agent_dashboard", "performance_dashboard", "alert_dashboard"]
        for d in dashboards:
            data = load_dashboard(d)
            self.assertIsInstance(data, dict)
            self.assertIn("panels", data)
            self.assertGreater(len(data["panels"]), 0)


if __name__ == "__main__":
    unittest.main()
