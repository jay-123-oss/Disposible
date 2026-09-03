"""Git integration and checkpoint tools for change tracking and rollback."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.tools.base import BaseTool, SafetyLevel, ToolResult
from core.tools.terminal_tools import RunCommandTool


class GitStatusTool(BaseTool):
    name = "git_status"
    description = "Inspect git status for unstaged, staged, and untracked changes."
    safety_level = SafetyLevel.SAFE

    def _run(self) -> ToolResult:
        res = RunCommandTool().execute(command="git status --short")
        if not res.success:
            return res

        lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        res.output = {"changed_files": lines, "total_changes": len(lines)}
        return res


class GitDiffTool(BaseTool):
    name = "git_diff"
    description = "Generate git diff for workspace changes."
    safety_level = SafetyLevel.SAFE

    def _run(self, filepath: Optional[str] = None) -> ToolResult:
        cmd = f"git diff {filepath}" if filepath else "git diff"
        return RunCommandTool().execute(command=cmd)


class GitLogTool(BaseTool):
    name = "git_log"
    description = "Inspect recent git commits."
    safety_level = SafetyLevel.SAFE

    def _run(self, limit: int = 5) -> ToolResult:
        cmd = f"git log -n {limit} --oneline"
        return RunCommandTool().execute(command=cmd)
