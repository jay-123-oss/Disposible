"""TaskQueue class for priority-based task scheduling and DAG dependency resolution.

Implements:
- Priority-based queuing (HIGH, MEDIUM, LOW) using priority ordering.
- Dependency tracking where tasks are released only when upstream tasks are COMPLETED.
- Exponential backoff retry logic (1s, 2s, 4s; max 3 retries).
- Execution timeout detection and task status transitions (PENDING, RUNNING, COMPLETED, FAILED).
"""

from __future__ import annotations

import heapq
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from core.exceptions import OrchestratorError


logger = logging.getLogger("FractalCore.TaskQueue")


class TaskPriority(int, Enum):
    """Task priority levels (lower integer value corresponds to higher priority)."""
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class TaskStatus(str, Enum):
    """Task lifecycle states."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


@dataclass(order=True)
class PrioritizedTask:
    """Wrapper used for priority queue heap ordering."""
    priority: int
    created_at: float = field(compare=True)
    task_id: str = field(compare=False)


@dataclass
class TaskItem:
    """Full task descriptor within the task queue and DAG."""
    task_id: str
    intent: str
    assigned_capability: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: Set[str] = field(default_factory=set)
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: float = 30.0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    next_retry_time: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TaskQueue:
    """Thread-safe priority task queue with DAG dependency resolution."""

    def __init__(self, max_retries: int = 3, default_timeout_seconds: float = 30.0) -> None:
        self._max_retries = max_retries
        self._default_timeout_seconds = default_timeout_seconds
        self._lock = threading.RLock()
        self._tasks: Dict[str, TaskItem] = {}
        self._priority_heap: List[PrioritizedTask] = []
        self._completed_task_ids: Set[str] = set()
        logger.info(
            "TaskQueue initialized (Max Retries: %d, Default Timeout: %.1fs)",
            self._max_retries,
            self._default_timeout_seconds,
        )

    # --------------------------------------------------------------------------
    # Task Ingestion
    # --------------------------------------------------------------------------

    def add_task(
        self,
        task_id: str,
        intent: str,
        assigned_capability: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: Optional[List[str]] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> TaskItem:
        """Add a task to the queue and DAG registry.

        Args:
            task_id: Unique identifier for the task.
            intent: High-level purpose or goal.
            assigned_capability: Required capability to execute this task.
            payload: Input dictionary / artifact references.
            priority: TaskPriority (HIGH, MEDIUM, LOW).
            dependencies: List of task_ids that must complete before this can run.
            timeout_seconds: Max execution duration before timeout.
            max_retries: Number of retry attempts.

        Returns:
            The created TaskItem.
        """
        with self._lock:
            if task_id in self._tasks:
                raise OrchestratorError(f"Task with ID '{task_id}' already exists in TaskQueue.")

            dep_set = set(dependencies or [])
            # Check if any dependencies are currently unmet
            unmet_deps = dep_set - self._completed_task_ids
            initial_status = TaskStatus.BLOCKED if unmet_deps else TaskStatus.PENDING

            item = TaskItem(
                task_id=task_id,
                intent=intent,
                assigned_capability=assigned_capability,
                payload=payload or {},
                priority=priority,
                dependencies=dep_set,
                status=initial_status,
                max_retries=max_retries if max_retries is not None else self._max_retries,
                timeout_seconds=timeout_seconds or self._default_timeout_seconds,
            )

            self._tasks[task_id] = item

            # Only enqueue in priority heap if all dependencies are satisfied
            if initial_status == TaskStatus.PENDING:
                heapq.heappush(
                    self._priority_heap,
                    PrioritizedTask(priority=priority.value, created_at=item.created_at, task_id=task_id),
                )
                logger.debug("Task '%s' enqueued directly as PENDING (Priority: %s)", task_id, priority.name)
            else:
                logger.debug("Task '%s' BLOCKED waiting on dependencies: %s", task_id, list(unmet_deps))

            return item

    # --------------------------------------------------------------------------
    # Task Dispatch & Scheduling
    # --------------------------------------------------------------------------

    def get_next_task(self) -> Optional[TaskItem]:
        """Fetch the highest-priority runnable task whose dependencies are satisfied.

        Returns:
            TaskItem marked as RUNNING, or None if no task is currently ready.
        """
        with self._lock:
            now = time.time()
            self._check_timeouts()

            temp_stash: List[PrioritizedTask] = []
            selected_task: Optional[TaskItem] = None

            while self._priority_heap:
                prioritized = heapq.heappop(self._priority_heap)
                task_id = prioritized.task_id
                item = self._tasks.get(task_id)

                if not item:
                    continue

                # Verify task is runnable
                if item.status == TaskStatus.PENDING:
                    # Check backoff timing if this was a retry
                    if item.next_retry_time > now:
                        temp_stash.append(prioritized)
                        continue

                    # Verify all dependencies are completed
                    unmet = item.dependencies - self._completed_task_ids
                    if unmet:
                        item.status = TaskStatus.BLOCKED
                        logger.debug("Task '%s' blocked during dequeue due to unmet: %s", task_id, unmet)
                        continue

                    item.status = TaskStatus.RUNNING
                    item.started_at = now
                    selected_task = item
                    break

            # Restore temporarily postponed tasks back to heap
            for stashed in temp_stash:
                heapq.heappush(self._priority_heap, stashed)

            return selected_task

    # --------------------------------------------------------------------------
    # Task Completion & Retries
    # --------------------------------------------------------------------------

    def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark a task as COMPLETED, record output, and unblock dependent tasks."""
        with self._lock:
            item = self._tasks.get(task_id)
            if not item:
                logger.warning("Attempted to complete unknown task '%s'", task_id)
                return

            item.status = TaskStatus.COMPLETED
            item.completed_at = time.time()
            item.result = result or {}
            self._completed_task_ids.add(task_id)

            logger.info("Task '%s' COMPLETED successfully", task_id)
            self._unblock_dependents(task_id)

    def fail_task(self, task_id: str, error_message: str) -> None:
        """Handle task failure with exponential backoff (1s, 2s, 4s) or transition to FAILED."""
        with self._lock:
            item = self._tasks.get(task_id)
            if not item:
                logger.warning("Attempted to fail unknown task '%s'", task_id)
                return

            item.error_message = error_message
            item.retry_count += 1

            if item.retry_count <= item.max_retries:
                # Exponential backoff formula: 2^(retry - 1) -> 1s, 2s, 4s
                delay = float(2 ** (item.retry_count - 1))
                item.status = TaskStatus.PENDING
                item.next_retry_time = time.time() + delay
                heapq.heappush(
                    self._priority_heap,
                    PrioritizedTask(priority=item.priority.value, created_at=time.time(), task_id=task_id),
                )
                logger.warning(
                    "Task '%s' failed (Attempt %d/%d): %s. Scheduled retry in %.1fs.",
                    task_id,
                    item.retry_count,
                    item.max_retries,
                    error_message,
                    delay,
                )
            else:
                item.status = TaskStatus.FAILED
                item.completed_at = time.time()
                logger.error(
                    "Task '%s' PERMANENTLY FAILED after %d retries. Error: %s",
                    task_id,
                    item.max_retries,
                    error_message,
                )

    def _unblock_dependents(self, completed_task_id: str) -> None:
        """Inspect blocked tasks and enqueue any whose dependencies are now fully satisfied."""
        for task_id, item in self._tasks.items():
            if item.status == TaskStatus.BLOCKED:
                if completed_task_id in item.dependencies:
                    unmet = item.dependencies - self._completed_task_ids
                    if not unmet:
                        item.status = TaskStatus.PENDING
                        heapq.heappush(
                            self._priority_heap,
                            PrioritizedTask(
                                priority=item.priority.value,
                                created_at=item.created_at,
                                task_id=task_id,
                            ),
                        )
                        logger.info("Task '%s' unblocked and ready for execution", task_id)

    def _check_timeouts(self) -> None:
        """Scan running tasks and fail any that exceed their allotted execution timeout."""
        now = time.time()
        for task_id, item in list(self._tasks.items()):
            if item.status == TaskStatus.RUNNING and item.started_at:
                elapsed = now - item.started_at
                if elapsed > item.timeout_seconds:
                    logger.error("Task '%s' TIMED OUT after %.1fs (Limit: %.1fs)", task_id, elapsed, item.timeout_seconds)
                    self.fail_task(task_id, f"Execution timed out after {elapsed:.1f}s")

    # --------------------------------------------------------------------------
    # Status & Introspection
    # --------------------------------------------------------------------------

    def get_task(self, task_id: str) -> Optional[TaskItem]:
        """Fetch a task by its ID."""
        with self._lock:
            return self._tasks.get(task_id)

    def is_all_completed(self) -> bool:
        """Check if all tasks currently registered in the queue have reached a terminal state."""
        with self._lock:
            if not self._tasks:
                return True
            for item in self._tasks.values():
                if item.status in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.BLOCKED):
                    return False
            return True

    def get_dag_summary(self) -> Dict[str, Any]:
        """Return a structured summary of queue and DAG status."""
        with self._lock:
            status_counts: Dict[str, int] = {}
            for item in self._tasks.values():
                status_counts[item.status.value] = status_counts.get(item.status.value, 0) + 1

            return {
                "total_tasks": len(self._tasks),
                "completed_count": len(self._completed_task_ids),
                "pending_queue_size": len(self._priority_heap),
                "status_breakdown": status_counts,
            }
