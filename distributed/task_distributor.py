"""TaskDistributor agent partitioning, dispatching, tracking, and recovering distributed tasks.

Implements the complete Task Distributor hierarchy (D8):
- L4 TaskDistributor coordinator
- L5 atomic workers: TaskSplitter, TaskAssigner, TaskTracker, TaskRecoverer
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from distributed.exceptions import TaskDistributionError

logger = logging.getLogger("FractalCore.Distributed.TaskDistributor")


# ==============================================================================
# L5 Atomic Task Distributor Subagents
# ==============================================================================

class TaskSplitter(BaseAgent):
    """L5 agent decomposing coarse batches or complex tasks into parallelizable chunks."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TaskSplitter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        task = task_envelope.get("task", {})
        items = task.get("items", [task])
        chunk_size = task_envelope.get("chunk_size", 5)
        chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
        subtasks = []
        for idx, chunk in enumerate(chunks):
            subtasks.append({
                "subtask_id": f"{task.get('id', 'task')}_sub_{idx}",
                "parent_id": task.get("id", "task"),
                "items": chunk,
                "status": "pending",
            })
        return {"status": "COMPLETED", "subtasks": subtasks, "subtask_count": len(subtasks)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TaskSplitter %s cleaned up.", self.agent_id)


class TaskAssigner(BaseAgent):
    """L5 agent binding subtasks to available compute nodes based on load and affinity."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TaskAssigner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        subtasks = task_envelope.get("subtasks", [])
        nodes = task_envelope.get("nodes", ["node-local"])
        assignments = []
        for idx, st in enumerate(subtasks):
            assigned_node = nodes[idx % len(nodes)]
            assigned_st = dict(st)
            assigned_st["assigned_node"] = assigned_node
            assigned_st["assigned_at"] = time.time()
            assigned_st["status"] = "assigned"
            assignments.append(assigned_st)
        return {"status": "COMPLETED", "assignments": assignments}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TaskAssigner %s cleaned up.", self.agent_id)


class TaskTracker(BaseAgent):
    """L5 agent recording task execution states, completions, and latency metrics."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TaskTracker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        tasks = task_envelope.get("tasks", {})
        counts = {"pending": 0, "assigned": 0, "completed": 0, "failed": 0}
        for t in tasks.values():
            st = t.get("status", "pending")
            counts[st] = counts.get(st, 0) + 1
        return {"status": "COMPLETED", "summary": counts, "total_tasks": len(tasks)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TaskTracker %s cleaned up.", self.agent_id)


class TaskRecoverer(BaseAgent):
    """L5 agent detecting orphaned or timed-out subtasks and rescheduling on healthy nodes."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TaskRecoverer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        tasks = task_envelope.get("tasks", {})
        timeout = task_envelope.get("timeout", 60.0)
        healthy_nodes = task_envelope.get("healthy_nodes", ["node-local"])
        now = time.time()
        recovered = []

        for tid, t in tasks.items():
            if t.get("status") == "assigned" and (now - t.get("assigned_at", 0)) > timeout:
                t["status"] = "pending"
                t["assigned_node"] = healthy_nodes[0] if healthy_nodes else "node-local"
                t["retries"] = t.get("retries", 0) + 1
                recovered.append(tid)

        return {"status": "COMPLETED", "recovered_tasks": recovered, "count": len(recovered)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TaskRecoverer %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 TaskDistributor Agent
# ==============================================================================

class TaskDistributor(BaseAgent):
    """L4 coordinator splitting, assigning, monitoring, and recovering distributed tasks."""

    def __init__(
        self,
        name: str = "TaskDistributor",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "task_distributor",
            "task_splitter",
            "task_assigner",
            "task_tracker",
            "task_recoverer",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "D8_TASK_DISTRIBUTOR",
        )
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.available_nodes: List[str] = ["node-1"]

        self.splitter: Optional[TaskSplitter] = None
        self.assigner: Optional[TaskAssigner] = None
        self.tracker: Optional[TaskTracker] = None
        self.recoverer: Optional[TaskRecoverer] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("distribute_task", self.distribute_task)
        self.register_tool("get_task_status", self.get_task_status)

    def _spawn_subagents(self) -> None:
        """Spawn atomic task distributor subagents (Rule 1 & Rule 5)."""
        logger.info("TaskDistributor %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.splitter = self.spawn_subagent(TaskSplitter, name="TaskSplitter", max_depth=child_depth, resources_mb=32)
        self.assigner = self.spawn_subagent(TaskAssigner, name="TaskAssigner", max_depth=child_depth, resources_mb=32)
        self.tracker = self.spawn_subagent(TaskTracker, name="TaskTracker", max_depth=child_depth, resources_mb=32)
        self.recoverer = self.spawn_subagent(TaskRecoverer, name="TaskRecoverer", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TaskDistributor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return self.distribute_task(task_envelope.get("task", {}), task_envelope.get("nodes"))

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TaskDistributor %s cleaned up.", self.agent_id)

    def set_nodes(self, nodes: List[str]) -> None:
        """Update available node targets for task assignments."""
        self.available_nodes = list(nodes)

    def distribute_task(self, task: Dict[str, Any], nodes: Optional[List[str]] = None) -> Dict[str, Any]:
        """Split a task into subtasks and assign each to an available cluster node."""
        target_nodes = nodes or self.available_nodes
        res_split = self.splitter.process({"task": task}) if self.splitter else {"subtasks": [task]}
        subtasks = res_split["subtasks"]

        res_assign = self.assigner.process({"subtasks": subtasks, "nodes": target_nodes}) if self.assigner else {
            "assignments": subtasks
        }
        assignments = res_assign["assignments"]
        for a in assignments:
            tid = a.get("subtask_id", task.get("id", f"st_{time.time()}"))
            self.tasks[tid] = a

        return {
            "distributed": True,
            "task_id": task.get("id"),
            "subtask_count": len(assignments),
            "assignments": assignments,
        }

    def get_task_status(self) -> Dict[str, Any]:
        """Aggregate completion metrics across all submitted tasks."""
        if self.tracker:
            res = self.tracker.process({"tasks": self.tasks})
            return res.get("summary", {})
        return {"total": len(self.tasks)}
