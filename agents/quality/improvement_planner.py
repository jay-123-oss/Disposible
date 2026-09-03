"""ImprovementPlanner agent prioritizing debt remediation, synthesizing action items, and estimating timelines."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.quality.exceptions import QualityError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Quality.ImprovementPlanner")


# ==============================================================================
# L5 Atomic Planning Subagents
# ==============================================================================

class PrioritySetting(BaseAgent):
    """L5 agent sorting detected quality and architectural flaws by impact and urgency."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PrioritySetting %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        findings = payload.get("findings", [])
        prioritized = sorted(
            findings,
            key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x.get("severity", "LOW"), 4),
        )
        return {"status": "COMPLETED", "prioritized_findings": prioritized}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PrioritySetting %s cleaned up.", self.agent_id)


class ActionGenerator(BaseAgent):
    """L5 agent mapping quality gaps to concrete, step-by-step developer actions."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ActionGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        findings = payload.get("findings", [])

        actions: List[Dict[str, str]] = []
        if not findings:
            actions.append({
                "task": "Maintain Code Standards",
                "description": "Ensure CI linters and quality gate checks remain mandatory on all pull requests.",
                "effort": "30 mins",
            })
        else:
            for f in findings:
                actions.append({
                    "task": f"Remediate: {f.get('issue', 'Quality Gap')}",
                    "description": f.get("remediation", "Refactor targeted code."),
                    "effort": "2 hours",
                })

        return {"status": "COMPLETED", "actions": actions}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ActionGenerator %s cleaned up.", self.agent_id)


class TimelineEstimator(BaseAgent):
    """L5 agent aggregating effort estimates into developer sprints and calendar estimates."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TimelineEstimator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        actions_count = payload.get("actions_count", 1)
        est_hours = actions_count * 2
        return {
            "status": "COMPLETED",
            "estimated_engineering_hours": est_hours,
            "target_completion": "Current Sprint",
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TimelineEstimator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 ImprovementPlanner Agent
# ==============================================================================

class ImprovementPlanner(BaseAgent):
    """L4 coordinator formulating actionable technical debt remediation roadmaps and timeline estimates."""

    def __init__(
        self,
        name: str = "ImprovementPlanner",
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
            "improvement_planning",
            "prioritization",
            "action_generation",
            "effort_estimation",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "Q13_IMPROVEMENT_PLANNER",
        )

        self.priority_setter: Optional[PrioritySetting] = None
        self.action_generator: Optional[ActionGenerator] = None
        self.timeline_estimator: Optional[TimelineEstimator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("create_improvement_plan", self.create_improvement_plan)

    def _spawn_subagents(self) -> None:
        """Spawn atomic improvement planning subagents (Rule 1 & Rule 5)."""
        logger.info("ImprovementPlanner %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.priority_setter = self.spawn_subagent(
            PrioritySetting,
            name="PrioritySetting",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.action_generator = self.spawn_subagent(
            ActionGenerator,
            name="ActionGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.timeline_estimator = self.spawn_subagent(
            TimelineEstimator,
            name="TimelineEstimator",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ImprovementPlanner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        plan = self.create_improvement_plan(findings=payload.get("findings", []))
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "improvement_plan": plan,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        plan = result.get("improvement_plan")
        if not plan or "actions" not in plan:
            raise QualityError("ImprovementPlanner produced incomplete plan.")
        return result

    def cleanup(self) -> None:
        logger.debug("ImprovementPlanner %s cleanup complete.", self.agent_id)

    def create_improvement_plan(self, findings: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Aggregate prioritization, concrete tasks, and timeline estimates."""
        f_list = findings or []
        p_res = self.priority_setter.process({"payload": {"findings": f_list}}) if self.priority_setter else {"prioritized_findings": f_list}
        a_res = self.action_generator.process({"payload": {"findings": p_res.get("prioritized_findings", [])}}) if self.action_generator else {"actions": []}
        actions = a_res.get("actions", [])
        t_res = self.timeline_estimator.process({"payload": {"actions_count": len(actions)}}) if self.timeline_estimator else {"estimated_engineering_hours": 2}

        return {
            "actions": actions,
            "timeline": t_res,
            "total_action_items": len(actions),
            "passed": True,
        }
