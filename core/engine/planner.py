"""Planner Agent for task decomposition, DAG generation, and acceptance criteria."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PlanTask(BaseModel):
    id: str = Field(..., description="Unique task identifier, e.g. T1, T2")
    description: str = Field(..., description="Actionable subtask description")
    agent: str = Field(..., description="Assigned agent: analyst | coder | tester | verifier")
    depends_on: List[str] = Field(default_factory=list, description="List of prerequisite task IDs")


class PlanOutput(BaseModel):
    goal: str = Field(..., description="High-level goal statement")
    complexity: str = Field("medium", description="low | medium | high")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Measurable pass/fail criteria")
    tasks: List[PlanTask] = Field(default_factory=list, description="DAG of atomic subtasks")


class PlannerAgent:
    """Generates execution blueprints with atomic tasks and acceptance criteria."""

    def plan(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> PlanOutput:
        lower = prompt.lower()
        tasks: List[PlanTask] = []
        criteria: List[str] = []

        if "auth" in lower or "jwt" in lower or "login" in lower:
            goal = "Implement authentication and automated test coverage"
            complexity = "high"
            criteria = [
                "Authentication endpoint or module exists",
                "Token generation and verification functions implemented",
                "Automated unit tests verify valid and invalid cases",
                "No hardcoded secrets or insecure credentials detected",
            ]
            tasks = [
                PlanTask(id="T1", description="Inspect existing auth architecture and models", agent="analyst"),
                PlanTask(id="T2", description="Implement authentication logic and utilities", agent="coder", depends_on=["T1"]),
                PlanTask(id="T3", description="Create and execute targeted unit tests", agent="tester", depends_on=["T2"]),
                PlanTask(id="T4", description="Verify implementation against acceptance criteria", agent="verifier", depends_on=["T3"]),
            ]
        elif "fix" in lower or "bug" in lower or "error" in lower:
            goal = f"Diagnose and resolve issue: {prompt}"
            complexity = "medium"
            criteria = [
                "Root cause identified in target file",
                "Fix applied with minimal diff",
                "Existing and regression tests pass",
            ]
            tasks = [
                PlanTask(id="T1", description="Analyze error and inspect affected files", agent="analyst"),
                PlanTask(id="T2", description="Apply targeted fix to code", agent="coder", depends_on=["T1"]),
                PlanTask(id="T3", description="Run test suite to verify resolution", agent="tester", depends_on=["T2"]),
                PlanTask(id="T4", description="Verify fix completeness", agent="verifier", depends_on=["T3"]),
            ]
        else:
            goal = f"Execute engineering task: {prompt}"
            complexity = "low"
            criteria = [
                "Requested files created or modified cleanly",
                "Syntax and basic execution verified",
            ]
            tasks = [
                PlanTask(id="T1", description="Implement requested code changes", agent="coder"),
                PlanTask(id="T2", description="Verify output and test files", agent="verifier", depends_on=["T1"]),
            ]

        return PlanOutput(goal=goal, complexity=complexity, acceptance_criteria=criteria, tasks=tasks)
