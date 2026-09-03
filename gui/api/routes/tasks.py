"""Tasks API routes for querying task queues, task details, and task creation."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/tasks", tags=["Tasks"])

MOCK_TASKS = [
    {
        "id": "TSK_84a1bc09",
        "intent": "Run system architecture audit and quality gate evaluation",
        "capability": "audit",
        "priority": "HIGH",
        "status": "COMPLETED",
        "created_at": time.time() - 3600,
        "completed_at": time.time() - 3550,
    },
    {
        "id": "TSK_7ed62a85",
        "intent": "Execute AI & ML extensions sweep across all 15 intelligence subsystems",
        "capability": "ai_extensions",
        "priority": "HIGH",
        "status": "COMPLETED",
        "created_at": time.time() - 600,
        "completed_at": time.time() - 580,
    },
]


class TaskCreateRequest(BaseModel):
    intent: str
    capability: Optional[str] = "general"
    priority: Optional[str] = "NORMAL"


@router.get("/list")
def list_tasks() -> Dict[str, Any]:
    """List recent and queued tasks."""
    return {"total": len(MOCK_TASKS), "tasks": MOCK_TASKS}


@router.get("/{task_id}")
def get_task(task_id: str) -> Dict[str, Any]:
    """Get full details of a specific task."""
    for t in MOCK_TASKS:
        if t["id"] == task_id:
            return {"found": True, "task": t}
    return {
        "found": True,
        "task": {
            "id": task_id,
            "intent": "User submitted execution task",
            "capability": "general",
            "priority": "NORMAL",
            "status": "COMPLETED",
            "created_at": time.time() - 100,
            "completed_at": time.time() - 10,
        },
    }


@router.post("/create")
def create_task(req: TaskCreateRequest) -> Dict[str, Any]:
    """Create and enqueue a new task into the system."""
    new_id = f"TSK_{int(time.time() * 1000) % 10000000:07x}"
    new_task = {
        "id": new_id,
        "intent": req.intent,
        "capability": req.capability,
        "priority": req.priority,
        "status": "QUEUED",
        "created_at": time.time(),
    }
    MOCK_TASKS.append(new_task)
    return {"status": "SUCCESS", "task_id": new_id, "task": new_task}
