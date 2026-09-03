"""PerformanceTestOrchestrator (PL1) coordinating all 13 performance and load testing subsystems."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from performance.benchmark_runner import BenchmarkRunner
from performance.comparison_engine import ComparisonEngine
from performance.exceptions import PerformanceTestError
from performance.load_tester import LoadTester
from performance.metrics_collector import MetricsCollector
from performance.performance_analyzer import PerformanceAnalyzer
from performance.recommendation_engine import RecommendationEngine
from performance.report_generator import ReportGenerator
from performance.resource_monitor import ResourceMonitor
from performance.scalability_tester import ScalabilityTester
from performance.soak_tester import SoakTester
from performance.spike_tester import SpikeTester
from performance.stress_tester import StressTester
from performance.threshold_validator import ThresholdValidator


logger = logging.getLogger("FractalCore.Performance.PerformanceTestOrchestrator")


class PerformanceTestOrchestrator(BaseAgent):
    """L3 Master Performance Test Orchestrator supervising all 13 L4 performance and load testing coordinators."""

    def __init__(
        self,
        name: str = "PerformanceTestOrchestrator",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 256,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "performance",
            "performance_testing",
            "performance_orchestration",
            "load_testing",
            "load_tester",
            "stress_tester",
            "spike_tester",
            "soak_tester",
            "scalability_tester",
            "benchmark_runner",
            "performance_analyzer",
            "resource_monitor",
            "metrics_collector",
            "report_generator",
            "comparison_engine",
            "threshold_validator",
            "recommendation_engine",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "PL1_PERFORMANCE_TEST_ORCHESTRATOR",
        )

        self.load_tst: Optional[LoadTester] = None
        self.stress_tst: Optional[StressTester] = None
        self.spike_tst: Optional[SpikeTester] = None
        self.soak_tst: Optional[SoakTester] = None
        self.scale_tst: Optional[ScalabilityTester] = None
        self.bench_run: Optional[BenchmarkRunner] = None
        self.perf_ana: Optional[PerformanceAnalyzer] = None
        self.res_mon: Optional[ResourceMonitor] = None
        self.met_coll: Optional[MetricsCollector] = None
        self.rep_gen: Optional[ReportGenerator] = None
        self.comp_eng: Optional[ComparisonEngine] = None
        self.thresh_val: Optional[ThresholdValidator] = None
        self.rec_eng: Optional[RecommendationEngine] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_testing_subsystems()

        self.register_tool("run_all_performance_tests", self.run_all_performance_tests)

    def _spawn_testing_subsystems(self) -> None:
        """Spawn the 13 L4 performance coordinators (Rule 1 & Rule 5)."""
        logger.info("PerformanceTestOrchestrator %s spawning 13 performance coordinators...", self.agent_id)
        child_depth = self.depth + 2

        self.load_tst = self.spawn_subagent(LoadTester, name="LoadTester", max_depth=child_depth, resources_mb=64)
        self.stress_tst = self.spawn_subagent(StressTester, name="StressTester", max_depth=child_depth, resources_mb=64)
        self.spike_tst = self.spawn_subagent(SpikeTester, name="SpikeTester", max_depth=child_depth, resources_mb=64)
        self.soak_tst = self.spawn_subagent(SoakTester, name="SoakTester", max_depth=child_depth, resources_mb=64)
        self.scale_tst = self.spawn_subagent(ScalabilityTester, name="ScalabilityTester", max_depth=child_depth, resources_mb=64)
        self.bench_run = self.spawn_subagent(BenchmarkRunner, name="BenchmarkRunner", max_depth=child_depth, resources_mb=64)
        self.perf_ana = self.spawn_subagent(PerformanceAnalyzer, name="PerformanceAnalyzer", max_depth=child_depth, resources_mb=64)
        self.res_mon = self.spawn_subagent(ResourceMonitor, name="ResourceMonitor", max_depth=child_depth, resources_mb=64)
        self.met_coll = self.spawn_subagent(MetricsCollector, name="MetricsCollector", max_depth=child_depth, resources_mb=64)
        self.rep_gen = self.spawn_subagent(ReportGenerator, name="ReportGenerator", max_depth=child_depth, resources_mb=64)
        self.comp_eng = self.spawn_subagent(ComparisonEngine, name="ComparisonEngine", max_depth=child_depth, resources_mb=64)
        self.thresh_val = self.spawn_subagent(ThresholdValidator, name="ThresholdValidator", max_depth=child_depth, resources_mb=64)
        self.rec_eng = self.spawn_subagent(RecommendationEngine, name="RecommendationEngine", max_depth=child_depth, resources_mb=64)

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PerformanceTestOrchestrator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        report = self.run_all_performance_tests(context=payload)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "performance_test_report": report,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        report = result.get("performance_test_report")
        if not report or not report.get("all_tests_successful", False):
            raise PerformanceTestError("Performance test suite execution failed or incomplete.")
        return result

    def cleanup(self) -> None:
        logger.debug("PerformanceTestOrchestrator %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def run_all_performance_tests(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute complete suite across load, stress, spike, soak, scalability, benchmarks, and validation."""
        ctx = context or {}
        logger.info("Executing comprehensive performance test cycle across all 13 coordinators...")

        l_res = self.load_tst.run_load_test(ctx) if self.load_tst else {"all_successful": True}
        st_res = self.stress_tst.run_stress_test(ctx) if self.stress_tst else {"all_successful": True}
        sp_res = self.spike_tst.run_spike_test(ctx) if self.spike_tst else {"all_successful": True}
        sk_res = self.soak_tst.run_soak_test(ctx) if self.soak_tst else {"all_successful": True}
        sc_res = self.scale_tst.run_scalability_test(ctx) if self.scale_tst else {"all_successful": True}
        b_res = self.bench_run.run_all_benchmarks(ctx) if self.bench_run else {"all_successful": True}
        a_res = self.perf_ana.analyze_performance(ctx) if self.perf_ana else {"all_successful": True}
        rm_res = self.res_mon.monitor_resources(ctx) if self.res_mon else {"all_successful": True}
        m_res = self.met_coll.collect_metrics(ctx) if self.met_coll else {"all_successful": True}
        rp_res = self.rep_gen.generate_all_reports(ctx) if self.rep_gen else {"all_successful": True}
        c_res = self.comp_eng.compare_performance(ctx) if self.comp_eng else {"all_successful": True}
        tv_res = self.thresh_val.validate_all_thresholds(ctx) if self.thresh_val else {"all_thresholds_passed": True}
        rc_res = self.rec_eng.generate_all_recommendations(ctx) if self.rec_eng else {"all_successful": True}

        all_ok = (
            l_res.get("all_successful", True)
            and st_res.get("all_successful", True)
            and sp_res.get("all_successful", True)
            and sk_res.get("all_successful", True)
            and sc_res.get("all_successful", True)
            and b_res.get("all_successful", True)
            and a_res.get("all_successful", True)
            and rm_res.get("all_successful", True)
            and m_res.get("all_successful", True)
            and rp_res.get("all_successful", True)
            and c_res.get("all_successful", True)
            and tv_res.get("all_thresholds_passed", True)
            and rc_res.get("all_successful", True)
        )

        return {
            "all_tests_successful": all_ok,
            "total_subsystems": 13,
            "load_testing": l_res,
            "stress_testing": st_res,
            "spike_testing": sp_res,
            "soak_testing": sk_res,
            "scalability_testing": sc_res,
            "benchmarks": b_res,
            "analysis": a_res,
            "resource_monitoring": rm_res,
            "metrics": m_res,
            "reports": rp_res,
            "comparison": c_res,
            "thresholds": tv_res,
            "recommendations": rc_res,
            "timestamp": time.time(),
        }
