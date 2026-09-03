"""Central Tool Manager for AI Engineering Agent.

Registers all engineering tools:
- File tools (list, read, write, edit, delete)
- Terminal tools (run_command, run_python, run_tests)
- Git tools (status, diff, log)
- Search tools (text, symbol)

Enforces safety levels (SAFE, CAUTION, DANGEROUS) and records every tool observation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.tools.base import BaseTool, SafetyLevel, ToolResult
from core.tools.file_tools import (
    DeleteFileTool,
    EditFileTool,
    ListFilesTool,
    ReadFileTool,
    WriteFileTool,
)
from core.tools.git_tools import GitDiffTool, GitLogTool, GitStatusTool
from core.tools.search_tools import SearchSymbolTool, SearchTextTool
from core.tools.terminal_tools import RunCommandTool, RunPythonTool, RunTestsTool

logger = logging.getLogger("AIhenge.ToolManager")


class ToolManager:
    """Central registry and policy-enforcing dispatcher for all tools."""

    def __init__(self, autoconfirm_caution: bool = True):
        self._tools: Dict[str, BaseTool] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self.autoconfirm_caution = autoconfirm_caution

        self._register_default_tools()

    def _register_default_tools(self) -> None:
        default_tools: List[BaseTool] = [
            ListFilesTool(),
            ReadFileTool(),
            WriteFileTool(),
            EditFileTool(),
            DeleteFileTool(),
            RunCommandTool(),
            RunPythonTool(),
            RunTestsTool(),
            GitStatusTool(),
            GitDiffTool(),
            GitLogTool(),
            SearchTextTool(),
            SearchSymbolTool(),
        ]
        for tool in default_tools:
            self.register_tool(tool)

    def register_tool(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s (%s)", tool.name, tool.safety_level.value)

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "safety_level": t.safety_level.value,
            }
            for t in self._tools.values()
        ]

    def execute(self, tool_name: str, **kwargs: Any) -> ToolResult:
        tool = self.get_tool(tool_name)
        if not tool:
            res = ToolResult(
                success=False,
                output=None,
                error=f"Tool '{tool_name}' is not registered.",
                exit_code=1,
            )
            self._record_invocation(tool_name, kwargs, res)
            return res

        # Safety Gate Check
        if tool.safety_level == SafetyLevel.DANGEROUS and not kwargs.get("allow_dangerous", False):
            res = ToolResult(
                success=False,
                output=None,
                error=f"Tool '{tool_name}' is classified as DANGEROUS and requires explicit user confirmation.",
                safety_level=SafetyLevel.DANGEROUS,
            )
            self._record_invocation(tool_name, kwargs, res)
            return res

        result = tool.execute(**kwargs)
        self._record_invocation(tool_name, kwargs, result)
        return result

    def _record_invocation(self, tool_name: str, args: Dict[str, Any], result: ToolResult) -> None:
        entry = {
            "tool": tool_name,
            "arguments": {k: str(v)[:200] for k, v in args.items()},
            "success": result.success,
            "duration": round(result.duration_seconds, 3),
            "safety": result.safety_level.value,
            "error": result.error,
        }
        self._execution_history.append(entry)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._execution_history)
