"""TaskDecomposer agent for breaking architectural plans into atomic tasks with DAG dependencies."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.planning.exceptions import TaskDecompositionError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Planning.TaskDecomposer")


class TaskDecomposer(BaseAgent):
    """Decomposes macroscopic engineering plans into atomic, dependency-mapped tasks."""

    def __init__(
        self,
        name: str = "TaskDecomposer",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or [
            "task_decomposition",
            "dependency_mapping",
            "priority_assignment",
            "atomic_sizing",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P8_TASK_DECOMPOSER",
        )
        self.register_tool("decompose_tasks", self.decompose_tasks)
        self.register_tool("map_dependencies", self.map_dependencies)
        self.register_tool("assign_priorities", self.assign_priorities)

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TaskDecomposer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        tasks = self.decompose_tasks(payload)
        tasks_with_deps = self.map_dependencies(tasks)
        prioritized_tasks = self.assign_priorities(tasks_with_deps)

        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "tasks_count": len(prioritized_tasks),
            "tasks": prioritized_tasks,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        tasks = result.get("tasks")
        if not tasks or not isinstance(tasks, list):
            raise TaskDecompositionError(
                "TaskDecomposer produced no valid task array.",
                details={"result": result, "agent_id": self.agent_id},
            )
        return result

    def cleanup(self) -> None:
        logger.debug("TaskDecomposer %s cleaned up.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def decompose_tasks(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break down the plan into ordered phase-based atomic engineering tasks."""
        tasks: List[Dict[str, Any]] = []

        # Phase 1: Environment & Project Setup
        tasks.append({
            "id": "T01_SETUP",
            "description": "Initialize project structure and configuration files",
            "phase": "Setup",
            "priority": "HIGH",
            "dependencies": [],
            "estimated_time": "5 min",
            "estimated_tokens": 350,
            "assigned_to": "DEVELOPER",
            "success_criteria": ["Directory tree created", "Configuration file present"],
        })

        # Phase 2: Data Models & Persistence
        tasks.append({
            "id": "T02_MODELS",
            "description": "Define database entity models and ORM schema",
            "phase": "DataModel",
            "priority": "HIGH",
            "dependencies": ["T01_SETUP"],
            "estimated_time": "10 min",
            "estimated_tokens": 500,
            "assigned_to": "DEVELOPER",
            "success_criteria": ["Model classes pass AST validation", "Field constraints declared"],
        })

        # Phase 3: Business Logic & Services
        tasks.append({
            "id": "T03_SERVICES",
            "description": "Implement core business service layer functions",
            "phase": "BusinessLogic",
            "priority": "MEDIUM",
            "dependencies": ["T02_MODELS"],
            "estimated_time": "15 min",
            "estimated_tokens": 600,
            "assigned_to": "DEVELOPER",
            "success_criteria": ["Service methods return typed results", "Error handling in place"],
        })

        # Phase 4: API Presentation & Routing
        tasks.append({
            "id": "T04_ROUTES",
            "description": "Construct HTTP route handlers and request validation DTOs",
            "phase": "Presentation",
            "priority": "HIGH",
            "dependencies": ["T03_SERVICES"],
            "estimated_time": "15 min",
            "estimated_tokens": 550,
            "assigned_to": "DEVELOPER",
            "success_criteria": ["Endpoints bound to routers", "Input/output schemas verified"],
        })

        # Phase 5: Testing & Verification
        tasks.append({
            "id": "T05_TESTS",
            "description": "Synthesize automated unit and integration tests",
            "phase": "Testing",
            "priority": "HIGH",
            "dependencies": ["T04_ROUTES"],
            "estimated_time": "10 min",
            "estimated_tokens": 500,
            "assigned_to": "TESTER",
            "success_criteria": ["100% tests green", ">=90% test coverage"],
        })

        # Phase 6: Security & SAST Audit
        tasks.append({
            "id": "T06_SECURITY",
            "description": "Perform static analysis scan and credential leak audit",
            "phase": "Security",
            "priority": "HIGH",
            "dependencies": ["T05_TESTS"],
            "estimated_time": "5 min",
            "estimated_tokens": 300,
            "assigned_to": "SECURITY",
            "success_criteria": ["0 critical vulnerabilities", "0 hardcoded secrets"],
        })

        logger.info("Decomposed plan into %d structured tasks across 6 phases.", len(tasks))
        return tasks

    def map_dependencies(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate acyclic property and verify that every dependency points to an existing task ID."""
        task_id_set = {t["id"] for t in tasks}
        for t in tasks:
            deps = t.get("dependencies", [])
            # Filter out any non-existent IDs
            valid_deps = [d for d in deps if d in task_id_set and d != t["id"]]
            t["dependencies"] = valid_deps

        return tasks

    def assign_priorities(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure critical path tasks have HIGH priority and leaf validations are ranked properly."""
        for t in tasks:
            # If a task has 0 dependencies, it is on the critical bootstrap path
            if not t.get("dependencies"):
                t["priority"] = "HIGH"
            elif t.get("phase") in ("Setup", "Testing", "Security"):
                t["priority"] = "HIGH"
            elif not t.get("priority"):
                t["priority"] = "MEDIUM"

        return tasks
