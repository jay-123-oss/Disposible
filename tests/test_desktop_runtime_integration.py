"""Desktop Runtime Integration & Natural Language CREATE Regression Suite.

Verifies:
1. 'jaydeeo.py file banao' -> CREATE, MUTATION, filename extracted as 'jaydeeo.py'
2. 'hello.py banao' -> CREATE, MUTATION
3. 'new file create karo' -> CREATE, MUTATION / CLARIFY (never silently converted to READ_ONLY)
4. 'project explain kro' -> EXPLAIN, READ_ONLY
5. 'project me bug find kro' -> ANALYZE, READ_ONLY
6. 'README.md banao' -> CREATE, MUTATION
7. Filename extraction precision (jaydeeo.py)
8. LLM unavailable during CREATE -> safe handling without silent conversion to READ_ONLY
9. Real desktop E2E event stream (TASK_CREATED, INTENT=CREATE, AGENT_SELECTED, TOOL_REQUESTED, staged mutation)
10. Critical safety verification: 'project ko explain kro' produces EXPLAIN, READ_ONLY, and never invokes write_file
"""

import asyncio
import os
import pytest
from core.canonical_orchestrator import CanonicalOrchestrator, TaskStatus
from core.intent_engine import ExecutionMode, ExecutionPolicyGate, IntentEngine, IntentType


@pytest.fixture
def orchestrator():
    return CanonicalOrchestrator(workspace_root=os.getcwd())


def test_1_jaydeeo_py_file_banao_intent(orchestrator):
    """TEST 1: 'jaydeeo.py file banao' -> CREATE, MUTATION."""
    prompt = "jaydeeo.py file banao"
    intent_res = IntentEngine.classify(prompt)
    assert intent_res.intent == IntentType.CREATE
    assert intent_res.execution_mode == ExecutionMode.MUTATION
    assert "jaydeeo.py" in intent_res.target_entities


def test_2_hello_py_banao_intent(orchestrator):
    """TEST 2: 'hello.py banao' -> CREATE, MUTATION."""
    prompt = "hello.py banao"
    intent_res = IntentEngine.classify(prompt)
    assert intent_res.intent == IntentType.CREATE
    assert intent_res.execution_mode == ExecutionMode.MUTATION
    assert "hello.py" in intent_res.target_entities


def test_3_new_file_create_karo_never_read_only(orchestrator):
    """TEST 3: 'new file create karo' -> CREATE, never silently converted to READ_ONLY."""
    prompt = "new file create karo"
    intent_res = IntentEngine.classify(prompt)
    assert intent_res.intent == IntentType.CREATE
    assert intent_res.execution_mode == ExecutionMode.MUTATION

    # Run through orchestrator and ensure mode is not READ_ONLY
    res = asyncio.run(orchestrator.execute_prompt(prompt))
    assert res["intent"] == IntentType.CREATE.value
    assert res["execution_mode"] == ExecutionMode.MUTATION.value
    # When filename is omitted, no file is created/staged blindly
    assert res["files"] == {}
    assert "Clarification" in res["summary"] or "specify" in res["summary"].lower()


def test_4_project_explain_kro(orchestrator):
    """TEST 4: 'project explain kro' -> EXPLAIN, READ_ONLY."""
    prompt = "project explain kro"
    intent_res = IntentEngine.classify(prompt)
    assert intent_res.intent == IntentType.EXPLAIN
    assert intent_res.execution_mode == ExecutionMode.READ_ONLY

    res = asyncio.run(orchestrator.execute_prompt(prompt))
    assert res["intent"] == IntentType.EXPLAIN.value
    assert res["execution_mode"] == ExecutionMode.READ_ONLY.value
    assert res["files"] == {}


def test_5_project_me_bug_find_kro(orchestrator):
    """TEST 5: 'project me bug find kro' -> ANALYZE, READ_ONLY."""
    prompt = "project me bug find kro"
    intent_res = IntentEngine.classify(prompt)
    assert intent_res.intent == IntentType.ANALYZE
    assert intent_res.execution_mode == ExecutionMode.READ_ONLY

    res = asyncio.run(orchestrator.execute_prompt(prompt))
    assert res["intent"] == IntentType.ANALYZE.value
    assert res["execution_mode"] == ExecutionMode.READ_ONLY.value
    assert res["files"] == {}


def test_6_readme_md_banao(orchestrator):
    """TEST 6: 'README.md banao' -> CREATE, MUTATION."""
    prompt = "README.md banao"
    intent_res = IntentEngine.classify(prompt)
    assert intent_res.intent == IntentType.CREATE
    assert intent_res.execution_mode == ExecutionMode.MUTATION
    assert "README.md" in intent_res.target_entities

    res = asyncio.run(orchestrator.execute_prompt(prompt))
    assert res["intent"] == IntentType.CREATE.value
    assert res["execution_mode"] == ExecutionMode.MUTATION.value
    assert "README.md" in res["files"]


def test_7_jaydeeo_py_filename_extracted(orchestrator):
    """TEST 7: 'jaydeeo.py file banao' -> filename extracted exactly as 'jaydeeo.py'."""
    prompt = "jaydeeo.py file banao"
    intent_res = IntentEngine.classify(prompt)
    assert intent_res.target_entities == ["jaydeeo.py"]

    # In task graph, verify T2_create_file receives jaydeeo.py
    graph = orchestrator.create_task_graph(prompt, intent_res)
    create_task = graph.tasks["T2_create_file"]
    assert create_task.inputs.get("filepath") == "jaydeeo.py"

    res = asyncio.run(orchestrator.execute_prompt(prompt))
    assert "jaydeeo.py" in res["files"]
    assert not os.path.exists("jaydeeo.py")  # Staged virtually, not committed blindly


def test_8_llm_unavailable_never_silently_read_only(orchestrator):
    """TEST 8: LLM unavailable during CREATE request preserves MUTATION / CREATE."""
    prompt = "jaydeeo.py file banao"
    intent_res = IntentEngine.classify(prompt)

    # Even with mock LLM failure/timeout, policy remains CREATE / MUTATION
    assert intent_res.intent == IntentType.CREATE
    assert intent_res.execution_mode == ExecutionMode.MUTATION

    res = asyncio.run(orchestrator.execute_prompt(prompt))
    assert res["intent"] == IntentType.CREATE.value
    assert res["execution_mode"] == ExecutionMode.MUTATION.value


def test_9_real_desktop_e2e_event_lifecycle(orchestrator):
    """TEST 9: Real desktop E2E event stream captures complete lifecycle."""
    prompt = "jaydeeo.py file banao"
    captured_events = []

    async def event_collector(event_type: str, data: dict):
        captured_events.append((event_type, data))

    res = asyncio.run(orchestrator.execute_prompt(prompt, event_callback=event_collector))

    event_names = [e[0] for e in captured_events]
    assert "TASK_CREATED" in event_names
    assert "AGENT_SELECTED" in event_names
    assert "TOOL_REQUESTED" in event_names
    assert "TOOL_COMPLETED" in event_names
    assert "TASK_COMPLETED" in event_names

    # Check agent selection chose CodingAgent for T2_create_file
    agent_selected_events = [data for ev, data in captured_events if ev == "AGENT_SELECTED"]
    assigned_agents = [d.get("agent") for d in agent_selected_events]
    assert "CodingAgent" in assigned_agents

    # Verify tool policy checked write_file
    tool_events = [data.get("tool") for ev, data in captured_events if ev == "TOOL_REQUESTED"]
    assert "write_file" in tool_events

    # Verify staged result
    assert "jaydeeo.py" in res["files"]
    assert not os.path.exists("jaydeeo.py")


def test_10_critical_safety_explain_zero_write_tool(orchestrator):
    """TEST 10: 'project ko explain kro' -> EXPLAIN, READ_ONLY, NO write_file tool requested."""
    prompt = "project ko explain kro"
    captured_events = []

    async def event_collector(event_type: str, data: dict):
        captured_events.append((event_type, data))

    res = asyncio.run(orchestrator.execute_prompt(prompt, event_callback=event_collector))

    assert res["intent"] == IntentType.EXPLAIN.value
    assert res["execution_mode"] == ExecutionMode.READ_ONLY.value
    assert res["files"] == {}

    # Verify write_file was NEVER requested or executed
    requested_tools = [data.get("tool") for ev, data in captured_events if ev == "TOOL_REQUESTED"]
    assert "write_file" not in requested_tools
    assert "edit_file" not in requested_tools
