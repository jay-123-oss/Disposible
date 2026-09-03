"""Unit tests for the Closed-Loop LangGraph Engineering Engine."""

from core.engine import ClosedLoopEngineeringEngine, PlannerAgent


def test_planner_agent():
    planner = PlannerAgent()
    plan = planner.plan("Add JWT authentication and unit tests")
    assert plan.complexity == "high"
    assert len(plan.tasks) >= 3
    assert len(plan.acceptance_criteria) >= 2


def test_closed_loop_execution():
    engine = ClosedLoopEngineeringEngine()
    result = engine.run_task("Create math utility with tests and verify")

    assert result["is_completed"] is True
    assert result["verification_report"] is not None
    assert result["verification_report"]["overall_status"] == "SUCCESS"
    assert len(result["files_modified"]) > 0
    assert result["security_audit"]["passed"] is True
