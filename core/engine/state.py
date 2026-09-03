"""State schema for the Closed-Loop LangGraph Multi-Agent Engine."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class TaskItem(TypedDict):
    id: str
    description: str
    agent: str
    depends_on: List[str]
    status: str


class EngineeringState(TypedDict):
    """Global execution state carried across all LangGraph nodes."""

    task_prompt: str
    route: str
    context: Dict[str, Any]
    plan: Dict[str, Any]
    acceptance_criteria: List[str]
    current_task_id: Optional[str]
    files_staged: Dict[str, str]
    files_modified: List[str]
    test_results: Dict[str, Any]
    debug_iterations: int
    last_error: Optional[str]
    error_category: Optional[str]
    security_audit: Dict[str, Any]
    verification_report: Optional[Dict[str, Any]]
    is_completed: bool
    status: str
