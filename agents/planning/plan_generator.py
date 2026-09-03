"""PlanGenerator agent for compiling holistic, phase-based execution roadmaps."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.planning.exceptions import PlanGenerationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Planning.PlanGenerator")


class PlanGenerator(BaseAgent):
    """Integrates requirements, architectures, tasks, and risk assessments into an actionable master execution plan."""

    def __init__(
        self,
        name: str = "PlanGenerator",
        capabilities: Optional[List[str]] = None,
        model: str = "llama3.2:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or [
            "plan_generation",
            "phase_orchestration",
            "resource_allocation",
            "timeline_estimation",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P10_PLAN_GENERATOR",
        )
        self.register_tool("generate_plan", self.generate_plan)
        self.register_tool("allocate_resources", self.allocate_resources)
        self.register_tool("estimate_timeline", self.estimate_timeline)

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PlanGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        full_plan = self.generate_plan(payload)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "plan": full_plan,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        plan = result.get("plan")
        if not plan or "phases" not in plan or "total_tasks" not in plan:
            raise PlanGenerationError("PlanGenerator produced incomplete master plan.", details={"result": result})
        return result

    def cleanup(self) -> None:
        logger.debug("PlanGenerator %s cleaned up.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def generate_plan(self, all_data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate decomposed tasks, risks, and architecture into the master plan."""
        project_name = all_data.get("project_name", "FractalAutonomousProject")
        tasks = all_data.get("tasks", [])
        risks = all_data.get("risks", [])

        # Partition tasks into phases
        phase_map: Dict[str, List[Dict[str, Any]]] = {}
        for t in tasks:
            ph = t.get("phase", "General")
            if ph not in phase_map:
                phase_map[ph] = []
            phase_map[ph].append(t)

        phases: List[Dict[str, Any]] = []
        for ph_name, ph_tasks in phase_map.items():
            phases.append({
                "name": ph_name,
                "tasks": ph_tasks,
                "task_count": len(ph_tasks),
                "duration": f"{len(ph_tasks) * 15} min",
                "dependencies": list({d for t in ph_tasks for d in t.get("dependencies", []) if d not in [pt["id"] for pt in ph_tasks]}),
            })

        timeline_data = self.estimate_timeline(tasks)
        resources = self.allocate_resources(tasks, all_data.get("available_agents", []))

        success_criteria = [
            "All unit and integration tests pass with 100% green rate",
            "Code coverage satisfies or exceeds 90%",
            "Zero critical/high security vulnerabilities detected by SAST",
            "Working tree is clean with zero uncommitted drift files",
            "Total token budget consumed remains <= 5,000 tokens",
        ]

        return {
            "project_name": project_name,
            "phases": phases,
            "total_tasks": len(tasks),
            "total_estimated_time": timeline_data.get("total_time_str", "2 hours"),
            "resource_requirements": resources,
            "risks": risks,
            "success_criteria": success_criteria,
            "contingency_plans": [
                "Auto-rollback to last green checkpoint upon 2 failed task iterations",
                "Fallback to deterministic templates if 3B parameter model produces malformed syntax",
                "Quarantine and alert if memory exceeds 92% of 8GB threshold",
            ],
        }

    def allocate_resources(self, tasks: List[Dict[str, Any]], agents: List[str]) -> Dict[str, Any]:
        """Determine agent process allocations and tools needed for execution."""
        assigned_domains = list({t.get("assigned_to", "DEVELOPER") for t in tasks})
        return {
            "agents": assigned_domains if assigned_domains else ["PLANNER", "DEVELOPER", "TESTER", "SECURITY"],
            "tools": ["python3", "pytest", "bandit", "git"],
            "infrastructure": ["Local Subprocess Sandbox (256MB RAM cap)", "JSON State Store", "Stigmergy Blackboard"],
        }

    def estimate_timeline(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate total execution duration based on task count and critical path."""
        total_mins = len(tasks) * 15
        hours = total_mins // 60
        mins = total_mins % 60
        time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

        return {
            "total_estimated_minutes": total_mins,
            "total_time_str": time_str,
            "milestones": [
                {"milestone": "Setup & Models Complete", "target": "25% of timeline"},
                {"milestone": "Services & Routes Implemented", "target": "60% of timeline"},
                {"milestone": "Test & Security Gates Green", "target": "100% of timeline"},
            ],
        }
