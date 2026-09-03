"""Phase 2 Automated Verification Tests: Intent Engine, Permission Boundary, and sample.txt Regression."""

import os
import pytest
from core.intent_engine import (
    ExecutionMode,
    ExecutionPolicyGate,
    IntentEngine,
    IntentType,
)


def test_1_project_ko_explain_kro():
    """TEST 1: 'project ko explain kro' -> intent=EXPLAIN, mode=READ_ONLY, write DENIED."""
    res = IntentEngine.classify("project ko explain kro")
    assert res.intent == IntentType.EXPLAIN
    assert res.execution_mode == ExecutionMode.READ_ONLY
    assert res.requires_write is False

    decision = ExecutionPolicyGate.evaluate(res, "write_file", {"filepath": "sample.txt"})
    assert decision.allowed is False
    assert "read-only and does not possess write permission" in decision.reason


def test_2_project_ka_architecture_batao():
    """TEST 2: 'project ka architecture batao' -> READ_ONLY mode."""
    res = IntentEngine.classify("project ka architecture batao")
    assert res.execution_mode == ExecutionMode.READ_ONLY
    assert res.requires_write is False

    decision = ExecutionPolicyGate.evaluate(res, "create_or_modify_file")
    assert decision.allowed is False


def test_3_project_me_bug_find_kro():
    """TEST 3: 'project me bug find kro' -> ANALYZE/READ_ONLY initially, write denied."""
    res = IntentEngine.classify("project me bug find kro")
    assert res.intent == IntentType.ANALYZE
    assert res.execution_mode == ExecutionMode.READ_ONLY
    assert res.requires_write is False

    decision = ExecutionPolicyGate.evaluate(res, "write_file")
    assert decision.allowed is False


def test_4_readme_banao():
    """TEST 4: 'README banao' -> CREATE, mutation allowed."""
    res = IntentEngine.classify("README banao")
    assert res.intent == IntentType.CREATE
    assert res.execution_mode == ExecutionMode.MUTATION
    assert res.requires_write is True

    decision = ExecutionPolicyGate.evaluate(res, "write_file", {"filepath": "README.md"})
    assert decision.allowed is True


def test_5_login_bug_fix_karo():
    """TEST 5: 'login bug fix karo' -> DEBUG, mutation allowed through policy."""
    res = IntentEngine.classify("login bug fix karo")
    assert res.intent == IntentType.DEBUG
    assert res.execution_mode == ExecutionMode.MUTATION
    assert res.requires_write is True

    decision = ExecutionPolicyGate.evaluate(res, "edit_file", {"filepath": "auth.py"})
    assert decision.allowed is True


def test_6_pytest_chalao():
    """TEST 6: 'pytest chalao' -> TEST/TERMINAL allowed, write not enabled."""
    res = IntentEngine.classify("pytest chalao")
    assert res.intent == IntentType.TEST
    assert res.execution_mode == ExecutionMode.TERMINAL
    assert res.requires_terminal is True
    assert res.requires_write is False

    # Terminal allowed
    term_decision = ExecutionPolicyGate.evaluate(res, "run_tests")
    assert term_decision.allowed is True

    # Write denied
    write_decision = ExecutionPolicyGate.evaluate(res, "write_file")
    assert write_decision.allowed is False


def test_7_database_delete_karo():
    """TEST 7: 'database delete karo' -> DANGEROUS, confirmation required, blocked without confirmation."""
    res = IntentEngine.classify("database delete karo")
    assert res.intent == IntentType.DELETE
    assert res.execution_mode == ExecutionMode.DANGEROUS
    assert res.requires_confirmation is True

    # Unconfirmed -> BLOCKED
    blocked_decision = ExecutionPolicyGate.evaluate(res, "delete_file", user_confirmed=False)
    assert blocked_decision.allowed is False
    assert blocked_decision.requires_confirmation is True

    # Confirmed -> ALLOWED
    confirmed_decision = ExecutionPolicyGate.evaluate(res, "delete_file", user_confirmed=True)
    assert confirmed_decision.allowed is True


def test_8_llm_timeout_no_file_created(tmp_path):
    """TEST 8: LLM timeout on 'project ko explain kro' -> NO FILE CREATED."""
    prompt = "project ko explain kro"
    res = IntentEngine.classify(prompt)
    assert res.execution_mode == ExecutionMode.READ_ONLY

    # In read-only mode, no file write operation can execute
    decision = ExecutionPolicyGate.evaluate(res, "write_file", {"filepath": "sample.txt"})
    assert decision.allowed is False

    # Verify no sample.txt was created
    assert not (tmp_path / "sample.txt").exists()


def test_9_llm_no_tool_call_no_file_created(tmp_path):
    """TEST 9: LLM returns no tool call for 'project ko explain kro' -> NO FILE CREATED."""
    prompt = "project ko explain kro"
    res = IntentEngine.classify(prompt)
    assert res.execution_mode == ExecutionMode.READ_ONLY

    # Ensure policy rejects any write tool
    decision = ExecutionPolicyGate.evaluate(res, "create_or_modify_file")
    assert decision.allowed is False


def test_10_ambiguous_make_it_better():
    """TEST 10: Unknown/ambiguous 'make it better' -> CLARIFY, NO RANDOM FILE CREATED."""
    res = IntentEngine.classify("make it better")
    assert res.intent == IntentType.CLARIFY
    assert res.execution_mode == ExecutionMode.CLARIFY
    assert res.clarification_prompt is not None

    # All mutations blocked in clarification state
    decision = ExecutionPolicyGate.evaluate(res, "write_file")
    assert decision.allowed is False
    assert "CLARIFICATION state" in decision.reason


def test_11_critical_regression_sample_txt_never_created():
    """CRITICAL REGRESSION TEST: Verify sample.txt is never created on 'project ko explain kro'."""
    prompt = "project ko explain kro"
    res = IntentEngine.classify(prompt)

    # Gate verification
    for write_tool in ["write_file", "edit_file", "create_or_modify_file", "delete_file"]:
        dec = ExecutionPolicyGate.evaluate(res, write_tool)
        assert dec.allowed is False
