"""Closed-Loop Multi-Agent StateGraph Workflow compiled with LangGraph."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from core.engine.agents import AgentNodes
from core.engine.state import EngineeringState
from core.tools import ToolManager

logger = logging.getLogger("AIhenge.ClosedLoopEngine")


def build_closed_loop_graph(tool_manager: Optional[ToolManager] = None):
    """Constructs the closed-loop LangGraph StateGraph workflow."""
    nodes = AgentNodes(tool_manager=tool_manager)

    graph = StateGraph(EngineeringState)

    graph.add_node("understand_and_context", nodes.understand_and_context_node)
    graph.add_node("planner", nodes.planner_node)
    graph.add_node("coder", nodes.coder_node)
    graph.add_node("tester", nodes.tester_node)
    graph.add_node("debugger", nodes.debugger_node)
    graph.add_node("security", nodes.security_node)
    graph.add_node("verifier", nodes.verifier_node)

    # Workflow entry
    graph.set_entry_point("understand_and_context")
    graph.add_edge("understand_and_context", "planner")
    graph.add_edge("planner", "coder")
    graph.add_edge("coder", "tester")

    # Conditional branching: Self-healing debug loop
    def decide_after_testing(state: EngineeringState) -> str:
        test_res = state.get("test_results", {})
        debug_iter = state.get("debug_iterations", 0)

        if not test_res.get("success", False) and debug_iter < 3:
            logger.info("Tests failed. Routing to debugger (Iteration %d)", debug_iter + 1)
            return "debugger"
        return "security"

    graph.add_conditional_edges(
        "tester",
        decide_after_testing,
        {
            "debugger": "debugger",
            "security": "security",
        },
    )

    # Debugger loops back to tester
    graph.add_edge("debugger", "tester")

    # Security flows to verifier and closes loop
    graph.add_edge("security", "verifier")
    graph.add_edge("verifier", END)

    return graph.compile()


class ClosedLoopEngineeringEngine:
    """Production interface to execute autonomous engineering tasks."""

    def __init__(self, tool_manager: Optional[ToolManager] = None):
        self.tool_manager = tool_manager or ToolManager()
        self.graph = build_closed_loop_graph(self.tool_manager)

    def run_task(self, prompt: str) -> Dict[str, Any]:
        """Execute closed-loop task from prompt to verified resolution."""
        initial_state: EngineeringState = {
            "task_prompt": prompt,
            "route": "CODE",
            "context": {},
            "plan": {},
            "acceptance_criteria": [],
            "current_task_id": None,
            "files_staged": {},
            "files_modified": [],
            "test_results": {},
            "debug_iterations": 0,
            "last_error": None,
            "error_category": None,
            "security_audit": {},
            "verification_report": None,
            "is_completed": False,
            "status": "Initiated",
        }

        logger.info("Starting Closed-Loop Engineering task: %s", prompt)
        final_state = self.graph.invoke(initial_state)
        return final_state
