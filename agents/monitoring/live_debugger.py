"""LiveDebugger agent providing real-time breakpoint management, variable inspection, and stack trace analysis."""

from __future__ import annotations

import logging
import traceback
from typing import Any, Dict, List, Optional

from agents.monitoring.exceptions import DebuggerError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Monitoring.LiveDebugger")


# ==============================================================================
# L5 Atomic Debugger Subagents
# ==============================================================================

class BreakpointManager(BaseAgent):
    """L5 agent managing conditional breakpoints and error-triggered halts."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("BreakpointManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        file_path = payload.get("file_path", "main.py")
        line_no = payload.get("line_no", 1)
        condition = payload.get("condition")

        bp = {
            "file_path": file_path,
            "line_no": line_no,
            "condition": condition,
            "hit_count": 0,
            "enabled": True,
        }
        return {"status": "COMPLETED", "breakpoint": bp}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "breakpoint" not in result:
            raise DebuggerError("BreakpointManager produced invalid breakpoint.")
        return result

    def cleanup(self) -> None:
        logger.debug("BreakpointManager %s cleaned up.", self.agent_id)


class VariableInspector(BaseAgent):
    """L5 agent capturing and sanitizing local and global variable scopes during execution."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("VariableInspector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        scope = payload.get("scope", {})

        inspected = {}
        for k, v in scope.items():
            if str(k).startswith("__"):
                continue
            inspected[str(k)] = {
                "type": type(v).__name__,
                "value_repr": repr(v)[:200],
            }
        return {"status": "COMPLETED", "inspected_variables": inspected}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("VariableInspector %s cleaned up.", self.agent_id)


class StackTraceAnalyzer(BaseAgent):
    """L5 agent parsing stack frames, extracting call hierarchies, and pinpointing source locations."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("StackTraceAnalyzer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        tb_str = payload.get("traceback_str")

        frames = []
        if tb_str:
            lines = tb_str.strip().split("\n")
            for line in lines:
                if line.strip().startswith("File "):
                    frames.append(line.strip())

        return {
            "status": "COMPLETED",
            "frame_count": len(frames),
            "top_frame": frames[-1] if frames else "No active exception frame",
            "frames": frames,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("StackTraceAnalyzer %s cleaned up.", self.agent_id)


class InteractiveDebugger(BaseAgent):
    """L5 agent controlling interactive stepping (step into, step over, resume)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("InteractiveDebugger %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        action = payload.get("step_action", "STEP_OVER")
        current_line = payload.get("current_line", 1)

        next_line = current_line + 1 if action != "RESUME" else None
        return {
            "status": "COMPLETED",
            "action": action,
            "resumed": action == "RESUME",
            "next_line": next_line,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("InteractiveDebugger %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 LiveDebugger Agent
# ==============================================================================

class LiveDebugger(BaseAgent):
    """L4 coordinator overseeing execution breakpoint management, variable inspection, and interactive debugging."""

    def __init__(
        self,
        name: str = "LiveDebugger",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "live_debugging",
            "breakpoint_management",
            "variable_inspection",
            "stack_trace_analysis",
            "interactive_debugging",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M2_LIVE_DEBUGGER",
        )

        self._breakpoints: List[Dict[str, Any]] = []
        self.bp_mgr: Optional[BreakpointManager] = None
        self.var_inspector: Optional[VariableInspector] = None
        self.st_analyzer: Optional[StackTraceAnalyzer] = None
        self.interactive_dbg: Optional[InteractiveDebugger] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("set_breakpoint", self.set_breakpoint)
        self.register_tool("inspect_scope", self.inspect_scope)
        self.register_tool("analyze_stack", self.analyze_stack)

    def _spawn_subagents(self) -> None:
        """Spawn atomic debugger subagents (Rule 1 & Rule 5)."""
        logger.info("LiveDebugger %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.bp_mgr = self.spawn_subagent(
            BreakpointManager,
            name="BreakpointManager",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.var_inspector = self.spawn_subagent(
            VariableInspector,
            name="VariableInspector",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.st_analyzer = self.spawn_subagent(
            StackTraceAnalyzer,
            name="StackTraceAnalyzer",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.interactive_dbg = self.spawn_subagent(
            InteractiveDebugger,
            name="InteractiveDebugger",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LiveDebugger %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        scope = payload.get("scope", {"task_id": "TSK_1", "status": "ACTIVE"})
        inspected = self.inspect_scope(scope)
        return {"status": "COMPLETED", "debugging_session": inspected}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("LiveDebugger %s cleanup complete.", self.agent_id)

    def set_breakpoint(self, file_path: str, line_no: int, condition: Optional[str] = None) -> Dict[str, Any]:
        """Register breakpoint at target line."""
        p_env = {"payload": {"file_path": file_path, "line_no": line_no, "condition": condition}}
        res = self.bp_mgr.process(p_env) if self.bp_mgr else {"breakpoint": {"file_path": file_path, "line_no": line_no}}
        bp = res["breakpoint"]
        self._breakpoints.append(bp)
        return bp

    def inspect_scope(self, scope_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect variables within active execution frame."""
        p_env = {"payload": {"scope": scope_dict}}
        res = self.var_inspector.process(p_env) if self.var_inspector else {"inspected_variables": {}}
        return res.get("inspected_variables", {})

    def analyze_stack(self, traceback_str: str) -> Dict[str, Any]:
        """Analyze exception stack frames."""
        p_env = {"payload": {"traceback_str": traceback_str}}
        res = self.st_analyzer.process(p_env) if self.st_analyzer else {"frames": []}
        return res
