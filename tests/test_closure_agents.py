"""Unit tests for the Final Documentation & Project Closure Layer (FC1-FC14 + 52 subagents + closure reports + checklists)."""

from pathlib import Path
import unittest

from core.registry import AgentRegistry
from closure import (
    ArchiveManager,
    CelebrationPlanner,
    ClosureError,
    ComplianceAuditor,
    DocumentationReviewer,
    FinalClosureOrchestrator,
    FinalReviewBoard,
    FutureRoadmapPlanner,
    KnowledgeTransferManager,
    LessonsLearnedCollector,
    PerformanceAuditor,
    ProjectClosureReportGenerator,
    QualityAuditor,
    SecurityAuditor,
    SignoffCoordinator,
    register_all_closure_agents,
)


class TestClosureAgents(unittest.TestCase):
    """Test suite verifying all project closure coordinators, workers, reports, audits, and signoffs."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()
        self.orchestrator = FinalClosureOrchestrator(agent_id="FC1_TEST_ORCHESTRATOR")

    def tearDown(self) -> None:
        self.registry.clear()

    def test_01_all_28_files_exist(self) -> None:
        """Verify all 28 closure files exist and are non-empty."""
        expected_files = [
            "closure/__init__.py",
            "closure/final_closure_orchestrator.py",
            "closure/documentation_reviewer.py",
            "closure/quality_auditor.py",
            "closure/performance_auditor.py",
            "closure/security_auditor.py",
            "closure/compliance_auditor.py",
            "closure/lessons_learned_collector.py",
            "closure/project_closure_report_generator.py",
            "closure/future_roadmap_planner.py",
            "closure/knowledge_transfer_manager.py",
            "closure/final_review_board.py",
            "closure/signoff_coordinator.py",
            "closure/archive_manager.py",
            "closure/celebration_planner.py",
            "docs/closure/PROJECT_CLOSURE_REPORT.md",
            "docs/closure/EXECUTIVE_SUMMARY.md",
            "docs/closure/LESSONS_LEARNED.md",
            "docs/closure/FUTURE_ROADMAP.md",
            "docs/closure/QUALITY_AUDIT_REPORT.md",
            "docs/closure/PERFORMANCE_AUDIT_REPORT.md",
            "docs/closure/SECURITY_AUDIT_REPORT.md",
            "docs/closure/COMPLIANCE_AUDIT_REPORT.md",
            "docs/closure/KNOWLEDGE_TRANSFER_GUIDE.md",
            "docs/closure/SIGNOFF_CHECKLIST.md",
            "docs/closure/FINAL_SIGNOFF_FORM.md",
            "docs/closure/ARCHIVE_INDEX.md",
            "docs/closure/PROJECT_TIMELINE.md",
        ]
        base_dir = Path(__file__).parent.parent
        for rel_path in expected_files:
            p = base_dir / rel_path
            self.assertTrue(p.exists(), f"File does not exist: {rel_path}")
            self.assertGreater(p.stat().st_size, 0, f"File is empty: {rel_path}")

    def test_02_orchestrator_spawns_all_13_coordinators(self) -> None:
        """Verify FinalClosureOrchestrator instantiates all 13 coordinators."""
        coordinators = [
            self.orchestrator.doc_rev,
            self.orchestrator.qlt_aud,
            self.orchestrator.prf_aud,
            self.orchestrator.sec_aud,
            self.orchestrator.cmp_aud,
            self.orchestrator.lsn_col,
            self.orchestrator.rep_gen,
            self.orchestrator.rdm_pln,
            self.orchestrator.knw_mgr,
            self.orchestrator.rvw_brd,
            self.orchestrator.sgn_crd,
            self.orchestrator.arc_mgr,
            self.orchestrator.clb_pln,
        ]
        for coord in coordinators:
            self.assertIsNotNone(coord)
            self.assertEqual(coord.depth, 1)

    def test_03_each_coordinator_spawns_4_grandchild_agents(self) -> None:
        """Verify each of the 13 coordinators instantiates 4 atomic grandchild workers (depth=2)."""
        coordinators = [
            (self.orchestrator.doc_rev, 4),
            (self.orchestrator.qlt_aud, 4),
            (self.orchestrator.prf_aud, 4),
            (self.orchestrator.sec_aud, 4),
            (self.orchestrator.cmp_aud, 4),
            (self.orchestrator.lsn_col, 4),
            (self.orchestrator.rep_gen, 4),
            (self.orchestrator.rdm_pln, 4),
            (self.orchestrator.knw_mgr, 4),
            (self.orchestrator.rvw_brd, 4),
            (self.orchestrator.sgn_crd, 4),
            (self.orchestrator.arc_mgr, 4),
            (self.orchestrator.clb_pln, 4),
        ]
        for coord, expected_count in coordinators:
            self.assertEqual(len(coord.children), expected_count)
            for sub in coord.children.values():
                self.assertEqual(sub.depth, 2)

    def test_04_registry_registers_all_66_agents(self) -> None:
        """Verify registration helper registers exactly 66 agents (1 + 13 + 52) within memory limits."""
        res = register_all_closure_agents(self.registry, self.orchestrator)
        self.assertEqual(res["total_registered"], 66)
        all_agents = self.registry.get_all_agents()
        self.assertEqual(len(all_agents), 66)
        self.assertLessEqual(self.registry._allocated_ram_mb, 8192)

    def test_05_documentation_reviewer_execution(self) -> None:
        """Verify DocumentationReviewer checks architecture, API, user, and deployment docs."""
        res = self.orchestrator.doc_rev.review_all_documentation()
        self.assertTrue(res["all_documentation_complete"])
        self.assertEqual(res["completeness_percentage"], 100.0)

    def test_06_quality_auditor_execution(self) -> None:
        """Verify QualityAuditor confirms score > 85.0 across code, test, process, and outcome."""
        res = self.orchestrator.qlt_aud.audit_system_quality()
        self.assertTrue(res["all_quality_gates_passed"])
        self.assertGreaterEqual(res["overall_quality_score"], 85.0)

    def test_07_performance_auditor_execution(self) -> None:
        """Verify PerformanceAuditor checks latency (<200ms), throughput (>100 RPS), usage (<80%), and scalability (>80%)."""
        res = self.orchestrator.prf_aud.audit_system_performance()
        self.assertTrue(res["all_performance_audits_passed"])
        self.assertLessEqual(res["response_time"]["p95_latency_ms"], 200.0)
        self.assertGreaterEqual(res["throughput"]["sustained_rps"], 100.0)

    def test_08_security_auditor_execution(self) -> None:
        """Verify SecurityAuditor confirms 0 critical/high vulnerabilities and valid RBAC."""
        res = self.orchestrator.sec_aud.audit_system_security()
        self.assertTrue(res["all_security_checks_passed"])
        self.assertTrue(res["zero_critical_or_high_vulnerabilities"])

    def test_09_compliance_auditor_execution(self) -> None:
        """Verify ComplianceAuditor validates GDPR, HIPAA, PCI, and SOX."""
        res = self.orchestrator.cmp_aud.audit_regulatory_compliance()
        self.assertTrue(res["all_compliance_requirements_met"])

    def test_10_lessons_learned_collector_execution(self) -> None:
        """Verify LessonsLearnedCollector gathers feedback, success stories, and future improvements."""
        res = self.orchestrator.lsn_col.collect_all_lessons()
        self.assertTrue(res["all_lessons_collected"])
        self.assertGreater(len(res["improvement_areas"]["improvements_identified"]), 0)

    def test_11_project_closure_report_generator_execution(self) -> None:
        """Verify ProjectClosureReportGenerator synthesizes executive summary, detailed report, and recommendations."""
        res = self.orchestrator.rep_gen.generate_closure_reports()
        self.assertTrue(res["all_reports_generated"])

    def test_12_future_roadmap_planner_execution(self) -> None:
        """Verify FutureRoadmapPlanner schedules features, enhancements, timeline, and resource quotas."""
        res = self.orchestrator.rdm_pln.plan_future_roadmap()
        self.assertTrue(res["roadmap_planning_complete"])

    def test_13_knowledge_transfer_manager_execution(self) -> None:
        """Verify KnowledgeTransferManager verifies documentation, training, handover, and wiki updates."""
        res = self.orchestrator.knw_mgr.manage_knowledge_transfer()
        self.assertTrue(res["knowledge_transfer_complete"])

    def test_14_final_review_board_execution(self) -> None:
        """Verify FinalReviewBoard executes board review and confirms 0 open action items."""
        res = self.orchestrator.rvw_brd.conduct_final_review()
        self.assertTrue(res["final_review_approved"])
        self.assertEqual(res["action_items"]["open_action_items"], 0)

    def test_15_signoff_coordinator_execution(self) -> None:
        """Verify SignoffCoordinator validates quorum and archives certificates."""
        res = self.orchestrator.sgn_crd.coordinate_final_signoff()
        self.assertTrue(res["all_signoffs_approved"])
        self.assertEqual(res["quorum_status"], "CERTIFIED")

    def test_16_archive_manager_execution(self) -> None:
        """Verify ArchiveManager indexes, compresses tarball, and verifies retrieval."""
        res = self.orchestrator.arc_mgr.manage_project_archive()
        self.assertTrue(res["archive_successfully_persisted"])
        self.assertTrue(res["retrieval"]["retrieval_verified"])

    def test_17_celebration_planner_execution(self) -> None:
        """Verify CelebrationPlanner schedules gala, awards, team appreciation, and announcements."""
        res = self.orchestrator.clb_pln.plan_project_celebration()
        self.assertTrue(res["celebration_planned"])

    def test_18_full_closure_orchestrator_lifecycle(self) -> None:
        """Verify complete orchestrator run across all 13 subsystems and PRODUCTION_READY_AND_ARCHIVED status."""
        envelope = {"payload": {"milestone": "PROJECT_CLOSURE"}}
        self.orchestrator.initialize(envelope)
        result = self.orchestrator.process(envelope)
        validated = self.orchestrator.validate(result)
        self.assertEqual(validated["status"], "COMPLETED")
        self.assertTrue(validated["closure_report"]["project_closed_successfully"])
        self.assertEqual(validated["closure_report"]["system_status"], "PRODUCTION_READY_AND_ARCHIVED")
        self.orchestrator.cleanup()


if __name__ == "__main__":
    unittest.main()
