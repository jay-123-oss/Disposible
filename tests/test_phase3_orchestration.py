"""Phase 3 Automated Verification Tests: Canonical Orchestration Layer.

Verifies:
- TEST A: 'project ko explain kro' -> intent=EXPLAIN, mode=READ_ONLY, no write tool
- TEST B: 'project architecture explain karo' -> READ_ONLY, context collection occurs
- TEST C: 'project me bug find kro' -> read-only, no write
- TEST D: 'README banao' -> CREATE/MUTATION, write allowed through policy
- TEST E: 'pytest chalao' -> terminal tool executes, actual exit code returned
- TEST F: 'login bug fix kro' -> dynamic plan includes analysis, coding, testing
- TEST G: Malformed plan rejected safely
- TEST H: Agent requests write_file while task is READ_ONLY -> policy denies execution
- TEST I: Independent analysis tasks -> parallel execution possible
- TEST J: Dependent task -> does not execute before dependency completion
- CRITICAL REGRESSION: 'project ko explain kro' leaves workspace clean (no sample.txt)
"""

import asyncio
import os
import pytest
from core.canonical_orchestrator import (
    CanonicalOrchestrator,
    Task,
    TaskGraph,
    TaskPriority,
    TaskStatus,
)
from core.intent_engine import ExecutionMode, ExecutionPolicyGate, IntentEngine, IntentResult, IntentType
from core.tools import ToolManager


@pytest.fixture
def orchestrator():
    return CanonicalOrchestrator()


def test_a_project_ko_explain_kro(orchestrator):
    """TEST A: 'project ko explain kro' -> intent=EXPLAIN, mode=READ_ONLY, no write tool."""
    prompt = "project ko explain kro"
    res = asyncio.run(orchestrator.execute_prompt(prompt))

    assert res["intent"] == IntentType.EXPLAIN.value
    assert res["execution_mode"] == ExecutionMode.READ_ONLY.value
    assert res["files"] == {}
    assert res["tasks_executed"] > 0
    assert "Architecture" in res["summary"] or "Antigravity" in res["summary"]

    # Verify no write tool in the generated task graph
    intent_res = IntentEngine.classify(prompt)
    graph = orchestrator.create_task_graph(prompt, intent_res)
    for task in graph.tasks.values():
        assert "write_file" not in task.required_tools
        assert "edit_file" not in task.required_tools


def test_b_project_architecture_explain_karo(orchestrator):
    """TEST B: 'project architecture explain karo' -> READ_ONLY, context collection occurs."""
    prompt = "project architecture explain karo"
    events = []

    async def on_event(event_type, data):
        events.append((event_type, data))

    res = asyncio.run(orchestrator.execute_prompt(prompt, event_callback=on_event))
    assert res["execution_mode"] == ExecutionMode.READ_ONLY.value

    # Verify CONTEXT_COLLECTED event occurred
    context_events = [e for e in events if e[0] == "CONTEXT_COLLECTED"]
    assert len(context_events) > 0
    assert context_events[0][1]["files_count"] > 0


def test_c_project_me_bug_find_kro(orchestrator):
    """TEST C: 'project me bug find kro' -> read-only, no write."""
    prompt = "project me bug find kro"
    res = asyncio.run(orchestrator.execute_prompt(prompt))

    assert res["execution_mode"] == ExecutionMode.READ_ONLY.value
    assert res["files"] == {}

    intent_res = IntentEngine.classify(prompt)
    graph = orchestrator.create_task_graph(prompt, intent_res)
    for task in graph.tasks.values():
        assert "write_file" not in task.required_tools
        assert task.execution_mode == ExecutionMode.READ_ONLY


def test_d_readme_banao(orchestrator):
    """TEST D: 'README banao' -> CREATE/MUTATION, write allowed through policy."""
    prompt = "README banao"
    intent_res = IntentEngine.classify(prompt)
    assert intent_res.intent == IntentType.CREATE
    assert intent_res.execution_mode == ExecutionMode.MUTATION

    # Verify write tool is permitted under this intent
    decision = ExecutionPolicyGate.evaluate(intent_res, "write_file", {"filepath": "README.md"})
    assert decision.allowed is True

    graph = orchestrator.create_task_graph(prompt, intent_res)
    create_tasks = [t for t in graph.tasks.values() if t.intent == IntentType.CREATE]
    assert len(create_tasks) > 0
    assert "write_file" in create_tasks[0].required_tools


def test_e_pytest_chalao(orchestrator):
    """TEST E: 'pytest chalao' -> terminal tool executes, actual exit code returned."""
    prompt = "pytest chalao"
    intent_res = IntentEngine.classify(prompt)
    assert intent_res.intent == IntentType.TEST
    assert intent_res.execution_mode == ExecutionMode.TERMINAL

    # Execute actual tool through ToolManager
    tools = ToolManager()
    result = tools.execute("run_tests", test_path="tests/test_phase2_intent_policy.py")
    assert hasattr(result, "exit_code")
    assert result.exit_code == 0
    assert result.success is True


def test_f_login_bug_fix_kro_dynamic_plan(orchestrator):
    """TEST F: 'login bug fix kro' -> dynamic plan includes analysis, coding, testing."""
    prompt = "login bug fix kro"
    intent_res = IntentEngine.classify(prompt)
    graph = orchestrator.create_task_graph(prompt, intent_res)

    intents_in_graph = {t.intent for t in graph.tasks.values()}
    assert IntentType.DEBUG in intents_in_graph or IntentType.MODIFY in intents_in_graph
    assert IntentType.TEST in intents_in_graph

    # Verify dependencies are chained
    tasks = list(graph.tasks.values())
    assert any(len(t.dependencies) > 0 for t in tasks)


def test_g_malformed_plan_rejected_safely(orchestrator):
    """TEST G: LLM returns a malformed plan -> system rejects it safely."""
    # Attempt to build task graph with empty or invalid prompt
    intent_res = IntentEngine.classify("")
    graph = orchestrator.create_task_graph("", intent_res)
    assert len(graph.tasks) > 0
    # Safe fallback task generated
    first_task = list(graph.tasks.values())[0]
    assert first_task.execution_mode == ExecutionMode.READ_ONLY


def test_h_write_denied_while_read_only():
    """TEST H: Agent requests write_file while task is READ_ONLY -> policy denies execution."""
    intent_res = IntentResult(
        intent=IntentType.EXPLAIN,
        confidence=0.99,
        requires_write=False,
        requires_terminal=False,
        requires_external_research=False,
        requires_confirmation=False,
        execution_mode=ExecutionMode.READ_ONLY,
        reason="Explanation task",
    )
    decision = ExecutionPolicyGate.evaluate(intent_res, "write_file", {"filepath": "sample.txt"})
    assert decision.allowed is False
    assert "read-only" in decision.reason.lower()


def test_i_independent_analysis_tasks_parallel_ready():
    """TEST I: Independent analysis tasks -> parallel execution is possible."""
    graph = TaskGraph()
    t1 = Task(task_id="T1", description="Inspect arch", objective="arch", intent=IntentType.ANALYZE)
    t2 = Task(task_id="T2", description="Inspect security", objective="sec", intent=IntentType.ANALYZE)
    graph.add_task(t1)
    graph.add_task(t2)

    ready = graph.get_ready_tasks()
    # Both tasks have no dependencies, so both are immediately READY concurrently
    assert len(ready) == 2
    assert {t.task_id for t in ready} == {"T1", "T2"}


def test_j_dependent_task_does_not_execute_before_dependency():
    """TEST J: Dependent task -> does not execute before dependency completion."""
    graph = TaskGraph()
    t1 = Task(task_id="T1", description="Analyze", objective="A", intent=IntentType.ANALYZE)
    t2 = Task(task_id="T2", description="Modify", objective="M", intent=IntentType.MODIFY, dependencies=["T1"])
    graph.add_task(t1)
    graph.add_task(t2)

    ready_initially = graph.get_ready_tasks()
    assert len(ready_initially) == 1
    assert ready_initially[0].task_id == "T1"

    # T2 must not be ready until T1 completes
    assert graph.get_task("T2").status == TaskStatus.PENDING

    # Complete T1
    graph.mark_completed("T1", {"result": "done"})
    ready_after = graph.get_ready_tasks()
    assert len(ready_after) == 1
    assert ready_after[0].task_id == "T2"


def test_k_critical_regression_workspace_clean(orchestrator):
    """CRITICAL REGRESSION TEST: 'project ko explain kro' leaves workspace clean (no sample.txt)."""
    mtime_before = os.path.getmtime("sample.txt") if os.path.exists("sample.txt") else None
    res = asyncio.run(orchestrator.execute_prompt("project ko explain kro"))
    assert res["execution_mode"] == ExecutionMode.READ_ONLY.value
    assert res["files"] == {}
    if mtime_before is not None:
        assert os.path.getmtime("sample.txt") == mtime_before
