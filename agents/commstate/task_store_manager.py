"""TaskStoreManager agent coordinating task lifecycle persistence, state tracking, and dependency queries."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from agents.commstate.exceptions import TaskStoreError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.CommState.TaskStoreManager")


# ==============================================================================
# L5 Atomic Task Store Subagents
# ==============================================================================

class TaskCreator(BaseAgent):
    """L5 agent creating new task records with unique IDs, priority, and timestamps."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TaskCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        task_id = payload.get("task_id") or f"TSK_{uuid.uuid4().hex[:8]}"
        record = {
            "task_id": task_id,
            "intent": payload.get("intent", "unspecified"),
            "status": "QUEUED",
            "priority": payload.get("priority", "MEDIUM"),
            "capability": payload.get("capability", "general"),
            "dependencies": payload.get("dependencies", []),
            "created_at": time.time(),
            "updated_at": time.time(),
            "result": None,
        }
        return {"status": "COMPLETED", "task_record": record}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "task_record" not in result:
            raise TaskStoreError("TaskCreator produced invalid record.")
        return result

    def cleanup(self) -> None:
        logger.debug("TaskCreator %s cleaned up.", self.agent_id)


class TaskUpdater(BaseAgent):
    """L5 agent updating task execution status, results, and progress metrics."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TaskUpdater %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        record = dict(payload.get("task_record", {}))
        new_status = payload.get("status", record.get("status", "IN_PROGRESS"))
        result_data = payload.get("result", record.get("result"))

        record["status"] = new_status
        record["result"] = result_data
        record["updated_at"] = time.time()
        return {"status": "COMPLETED", "task_record": record}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TaskUpdater %s cleaned up.", self.agent_id)


class TaskFinder(BaseAgent):
    """L5 agent locating tasks by status, capability, or dependency graph."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TaskFinder %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        tasks = payload.get("task_store", {})
        filter_status = payload.get("filter_status")
        filter_cap = payload.get("filter_capability")

        matched = []
        for t_id, task in tasks.items():
            if filter_status and task.get("status") != filter_status:
                continue
            if filter_cap and task.get("capability") != filter_cap:
                continue
            matched.append(task)

        return {"status": "COMPLETED", "matched_tasks": matched, "count": len(matched)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TaskFinder %s cleaned up.", self.agent_id)


class TaskDeleter(BaseAgent):
    """L5 agent pruning completed or expired tasks according to retention policy."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TaskDeleter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        task_store = dict(payload.get("task_store", {}))
        target_id = payload.get("task_id")

        deleted = False
        if target_id and target_id in task_store:
            del task_store[target_id]
            deleted = True

        return {"status": "COMPLETED", "task_store": task_store, "deleted": deleted}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TaskDeleter %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 TaskStoreManager Agent
# ==============================================================================

class TaskStoreManager(BaseAgent):
    """L4 coordinator managing full task lifecycle storage, indexing, and cleanup."""

    def __init__(
        self,
        name: str = "TaskStoreManager",
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
            "task_store_management",
            "task_creation",
            "task_updating",
            "task_querying",
            "task_cleanup",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C2_TASK_STORE_MANAGER",
        )

        self._store: Dict[str, Dict[str, Any]] = {}
        self.creator: Optional[TaskCreator] = None
        self.updater: Optional[TaskUpdater] = None
        self.finder: Optional[TaskFinder] = None
        self.deleter: Optional[TaskDeleter] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("create_task", self.create_task)
        self.register_tool("update_task", self.update_task)
        self.register_tool("find_tasks", self.find_tasks)
        self.register_tool("delete_task", self.delete_task)

    def _spawn_subagents(self) -> None:
        """Spawn atomic task store subagents (Rule 1 & Rule 5)."""
        logger.info("TaskStoreManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.creator = self.spawn_subagent(
            TaskCreator,
            name="TaskCreator",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.updater = self.spawn_subagent(
            TaskUpdater,
            name="TaskUpdater",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.finder = self.spawn_subagent(
            TaskFinder,
            name="TaskFinder",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.deleter = self.spawn_subagent(
            TaskDeleter,
            name="TaskDeleter",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TaskStoreManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        action = payload.get("action", "query")

        if action == "create":
            res = self.create_task(
                intent=payload.get("intent", ""),
                capability=payload.get("capability", "general"),
                priority=payload.get("priority", "MEDIUM"),
            )
            return {"status": "COMPLETED", "result": res}
        elif action == "update":
            res = self.update_task(
                task_id=payload.get("task_id", ""),
                status=payload.get("status", "IN_PROGRESS"),
                result_data=payload.get("result"),
            )
            return {"status": "COMPLETED", "result": res}
        else:
            res = self.find_tasks(
                status=payload.get("filter_status"),
                capability=payload.get("filter_capability"),
            )
            return {"status": "COMPLETED", "result": res}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TaskStoreManager %s cleanup complete.", self.agent_id)

    def create_task(self, intent: str, capability: str = "general", priority: str = "MEDIUM", task_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new task and store in repository."""
        p_env = {"payload": {"intent": intent, "capability": capability, "priority": priority, "task_id": task_id}}
        res = self.creator.process(p_env) if self.creator else {"task_record": {"task_id": task_id or "TSK_FALLBACK"}}
        record = res["task_record"]
        self._store[record["task_id"]] = record
        return record

    def update_task(self, task_id: str, status: str, result_data: Any = None) -> Optional[Dict[str, Any]]:
        """Update existing task state."""
        if task_id not in self._store:
            return None
        p_env = {"payload": {"task_record": self._store[task_id], "status": status, "result": result_data}}
        res = self.updater.process(p_env) if self.updater else {"task_record": self._store[task_id]}
        self._store[task_id] = res["task_record"]
        return self._store[task_id]

    def find_tasks(self, status: Optional[str] = None, capability: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query tasks by filter criteria."""
        p_env = {"payload": {"task_store": self._store, "filter_status": status, "filter_capability": capability}}
        res = self.finder.process(p_env) if self.finder else {"matched_tasks": list(self._store.values())}
        return res.get("matched_tasks", [])

    def delete_task(self, task_id: str) -> bool:
        """Delete task from store."""
        p_env = {"payload": {"task_store": self._store, "task_id": task_id}}
        res = self.deleter.process(p_env) if self.deleter else {"deleted": False}
        if res.get("deleted"):
            self._store.pop(task_id, None)
            return True
        return False
