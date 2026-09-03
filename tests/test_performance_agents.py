"""Unit tests for the Performance & Load Testing Layer (PL1-PL14 + 52 subagents + scenarios)."""

import os
import unittest
from pathlib import Path

import yaml

from core.registry import AgentRegistry
from performance.benchmark_runner import BenchmarkRunner
from performance.comparison_engine import ComparisonEngine
from performance.exceptions import PerformanceTestError
from performance.load_tester import LoadTester
from performance.metrics_collector import MetricsCollector
from performance.performance_analyzer import PerformanceAnalyzer
from performance.performance_orchestrator import PerformanceTestOrchestrator
from performance.recommendation_engine import RecommendationEngine
from performance.report_generator import ReportGenerator
from performance.resource_monitor import ResourceMonitor
from performance.scalability_tester import ScalabilityTester
from performance.soak_tester import SoakTester
from performance.spike_tester import SpikeTester
from performance.stress_tester import StressTester
from performance.threshold_validator import ThresholdValidator
from performance import register_all_performance_agents
from performance.scenarios.load_scenarios import LoadScenarioRunner
from performance.scenarios.stress_scenarios import StressScenarioRunner
from performance.scenarios.spike_scenarios import SpikeScenarioRunner
from performance.scenarios.soak_scenarios import SoakScenarioRunner


class TestPerformanceAgents(unittest.TestCase):
    """Test suite verifying all performance testing coordinators, workers, and scenarios."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()
        self.orchestrator = PerformanceTestOrchestrator(agent_id="PL1_TEST_ORCHESTRATOR")

    def tearDown(self) -> None:
        self.registry.clear()

    def test_01_all_25_files_exist(self) -> None:
        """Verify all 25 performance testing files exist and are non-empty."""
        expected_files = [
            "performance/__init__.py",
            "performance/performance_orchestrator.py",
            "performance/load_tester.py",
            "performance/stress_tester.py",
            "performance/spike_tester.py",
            "performance/soak_tester.py",
            "performance/scalability_tester.py",
            "performance/benchmark_runner.py",
            "performance/performance_analyzer.py",
            "performance/resource_monitor.py",
            "performance/metrics_collector.py",
            "performance/report_generator.py",
            "performance/comparison_engine.py",
            "performance/threshold_validator.py",
            "performance/recommendation_engine.py",
            "performance/scenarios/__init__.py",
            "performance/scenarios/load_scenarios.py",
            "performance/scenarios/stress_scenarios.py",
            "performance/scenarios/spike_scenarios.py",
            "performance/scenarios/soak_scenarios.py",
            "performance/performance_config.yaml",
            "performance/thresholds.yaml",
            "performance/report_templates/html_template.html",
            "performance/report_templates/json_schema.json",
            "performance/exceptions.py",
        ]
        base_dir = Path(__file__).parent.parent
        for rel_path in expected_files:
            p = base_dir / rel_path
            self.assertTrue(p.exists(), f"File does not exist: {rel_path}")
            self.assertGreater(p.stat().st_size, 0, f"File is empty: {rel_path}")

    def test_02_orchestrator_spawns_all_13_coordinators(self) -> None:
        """Verify PerformanceTestOrchestrator instantiates all 13 coordinators."""
        coordinators = [
            self.orchestrator.load_tst,
            self.orchestrator.stress_tst,
            self.orchestrator.spike_tst,
            self.orchestrator.soak_tst,
            self.orchestrator.scale_tst,
            self.orchestrator.bench_run,
            self.orchestrator.perf_ana,
            self.orchestrator.res_mon,
            self.orchestrator.met_coll,
            self.orchestrator.rep_gen,
            self.orchestrator.comp_eng,
            self.orchestrator.thresh_val,
            self.orchestrator.rec_eng,
        ]
        for coord in coordinators:
            self.assertIsNotNone(coord)
            self.assertEqual(coord.depth, 1)

    def test_03_each_coordinator_spawns_4_grandchild_agents(self) -> None:
        """Verify each of the 13 coordinators instantiates 4 atomic grandchild workers (depth=2)."""
        coordinators = [
            (self.orchestrator.load_tst, 4),
            (self.orchestrator.stress_tst, 4),
            (self.orchestrator.spike_tst, 4),
            (self.orchestrator.soak_tst, 4),
            (self.orchestrator.scale_tst, 4),
            (self.orchestrator.bench_run, 4),
            (self.orchestrator.perf_ana, 4),
            (self.orchestrator.res_mon, 4),
            (self.orchestrator.met_coll, 4),
            (self.orchestrator.rep_gen, 4),
            (self.orchestrator.comp_eng, 4),
            (self.orchestrator.thresh_val, 4),
            (self.orchestrator.rec_eng, 4),
        ]
        for coord, expected_count in coordinators:
            self.assertEqual(len(coord.children), expected_count)
            for sub in coord.children.values():
                self.assertEqual(sub.depth, 2)

    def test_04_registry_registers_all_66_agents(self) -> None:
        """Verify registration helper registers exactly 66 agents (1 + 13 + 52) within memory limits."""
        res = register_all_performance_agents(self.registry, self.orchestrator)
        self.assertEqual(res["total_registered"], 66)
        all_agents = self.registry.get_all_agents()
        self.assertEqual(len(all_agents), 66)
        self.assertLessEqual(self.registry._allocated_ram_mb, 8192)

    def test_05_load_tester_execution(self) -> None:
        """Verify LoadTester runs concurrent, ramp-up, constant, and variable tests."""
        res = self.orchestrator.load_tst.run_load_test()
        self.assertTrue(res["all_successful"])
        self.assertEqual(res["target_concurrency"], 1000)

    def test_06_stress_tester_execution(self) -> None:
        """Verify StressTester identifies breaking point and failover."""
        res = self.orchestrator.stress_tst.run_stress_test()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["breakpoint"]["found"])

    def test_07_spike_tester_execution(self) -> None:
        """Verify SpikeTester handles sudden surge and stabilization."""
        res = self.orchestrator.spike_tst.run_spike_test()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["surge"]["handled"])

    def test_08_soak_tester_execution(self) -> None:
        """Verify SoakTester tests extended duration and checks memory leaks."""
        res = self.orchestrator.soak_tst.run_soak_test()
        self.assertTrue(res["all_successful"])
        self.assertFalse(res["memory_leak"]["leak_detected"])

    def test_09_scalability_tester_execution(self) -> None:
        """Verify ScalabilityTester evaluates horizontal, vertical, and efficiency targets."""
        res = self.orchestrator.scale_tst.run_scalability_test()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["efficiency"]["within_target"])

    def test_10_benchmark_runner_execution(self) -> None:
        """Verify BenchmarkRunner executes system, agent, API, and DB benchmarks."""
        res = self.orchestrator.bench_run.run_all_benchmarks()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["api"]["within_target"])

    def test_11_performance_analyzer_execution(self) -> None:
        """Verify PerformanceAnalyzer computes percentiles, throughput, and error rates."""
        res = self.orchestrator.perf_ana.analyze_performance()
        self.assertTrue(res["all_successful"])
        self.assertLess(res["response_time"]["p95_ms"], 200.0)

    def test_12_resource_monitor_execution(self) -> None:
        """Verify ResourceMonitor captures CPU, memory, disk, and network stats."""
        res = self.orchestrator.res_mon.monitor_resources()
        self.assertTrue(res["all_successful"])
        self.assertIn("cpu_percent", res["cpu"])
        self.assertIn("memory_mb", res["memory"])

    def test_13_metrics_collector_execution(self) -> None:
        """Verify MetricsCollector collects request counts, timers, and success rate."""
        res = self.orchestrator.met_coll.collect_metrics()
        self.assertTrue(res["all_successful"])
        self.assertGreaterEqual(res["success_rate"]["success_rate_percent"], 99.0)

    def test_14_report_generator_execution(self) -> None:
        """Verify ReportGenerator generates HTML, JSON, CSV, and graph summaries."""
        res = self.orchestrator.rep_gen.generate_all_reports()
        self.assertTrue(res["all_successful"])

    def test_15_comparison_engine_execution(self) -> None:
        """Verify ComparisonEngine compares baselines, previous runs, and SLA targets."""
        res = self.orchestrator.comp_eng.compare_performance()
        self.assertTrue(res["all_successful"])
        self.assertFalse(res["previous_run"]["regression_detected"])

    def test_16_threshold_validator_execution(self) -> None:
        """Verify ThresholdValidator enforces latency, throughput, and error boundaries."""
        res = self.orchestrator.thresh_val.validate_all_thresholds()
        self.assertTrue(res["all_thresholds_passed"])

    def test_17_recommendation_engine_execution(self) -> None:
        """Verify RecommendationEngine synthesizes prioritized optimization suggestions."""
        res = self.orchestrator.rec_eng.generate_all_recommendations()
        self.assertTrue(res["all_successful"])
        self.assertGreater(len(res["prioritized_actions"]["prioritized_actions"]), 0)

    def test_18_full_performance_orchestrator_lifecycle(self) -> None:
        """Verify complete orchestrator run across all 13 subsystems."""
        envelope = {"payload": {"test_run_id": "PERF_RUN_001"}}
        self.orchestrator.initialize(envelope)
        result = self.orchestrator.process(envelope)
        validated = self.orchestrator.validate(result)
        self.assertEqual(validated["status"], "COMPLETED")
        self.assertTrue(validated["performance_test_report"]["all_tests_successful"])
        self.orchestrator.cleanup()

    def test_19_scenarios_standalone_execution(self) -> None:
        """Verify all 4 scenario generators execute correctly."""
        l_res = LoadScenarioRunner().execute_scenario()
        self.assertTrue(l_res["success"])

        st_res = StressScenarioRunner().execute_scenario()
        self.assertTrue(st_res["success"])

        sp_res = SpikeScenarioRunner().execute_scenario()
        self.assertTrue(sp_res["success"])

        sk_res = SoakScenarioRunner().execute_scenario()
        self.assertTrue(sk_res["success"])


if __name__ == "__main__":
    unittest.main()
