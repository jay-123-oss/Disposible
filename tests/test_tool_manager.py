"""Unit tests for Central Tool Manager and Safety Policy."""

import pytest
from core.tools import ToolManager, SafetyLevel, CommandPolicy


def test_tool_manager_registration():
    mgr = ToolManager()
    tools = mgr.list_tools()
    assert len(tools) >= 10
    assert any(t["name"] == "read_file" for t in tools)
    assert any(t["name"] == "run_command" for t in tools)


def test_command_policy_classification():
    safe_level, _ = CommandPolicy.evaluate("pytest")
    assert safe_level == SafetyLevel.SAFE

    caution_level, _ = CommandPolicy.evaluate("pip install requests")
    assert caution_level == SafetyLevel.CAUTION

    danger_level, _ = CommandPolicy.evaluate("rm -rf /")
    assert danger_level == SafetyLevel.DANGEROUS


def test_file_read_and_write(tmp_path):
    mgr = ToolManager()
    test_file = tmp_path / "hello_tool.txt"

    # Write file
    write_res = mgr.execute("write_file", filepath=str(test_file), content="Line 1\nLine 2\n")
    assert write_res.success
    assert write_res.metadata["lines_added"] == 2

    # Read file
    read_res = mgr.execute("read_file", filepath=str(test_file))
    assert read_res.success
    assert "Line 1" in read_res.output["content"]


def test_dangerous_tool_blocking():
    mgr = ToolManager()
    # Delete without allow_dangerous must fail
    res = mgr.execute("delete_file", filepath="dummy_path.txt", allow_dangerous=False)
    assert not res.success
    assert res.safety_level == SafetyLevel.DANGEROUS
