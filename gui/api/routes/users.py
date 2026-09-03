"""Users API routes for user listing, creation, and role mapping."""

from __future__ import annotations

import time
from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["Users"])

MOCK_USERS = [
    {"id": "usr_001", "username": "admin", "email": "admin@fractal.internal", "role": "Admin", "created_at": time.time() - 86400 * 30},
    {"id": "usr_002", "username": "developer", "email": "dev@fractal.internal", "role": "Developer", "created_at": time.time() - 86400 * 14},
    {"id": "usr_003", "username": "auditor", "email": "audit@fractal.internal", "role": "Auditor", "created_at": time.time() - 86400 * 7},
]


class UserCreateRequest(BaseModel):
    username: str
    email: str
    role: str = "Developer"


@router.get("/list")
def list_users() -> Dict[str, Any]:
    """List system users."""
    return {"total": len(MOCK_USERS), "users": MOCK_USERS}


@router.post("/create")
def create_user(req: UserCreateRequest) -> Dict[str, Any]:
    """Create new system user."""
    new_user = {
        "id": f"usr_{len(MOCK_USERS) + 1:03d}",
        "username": req.username,
        "email": req.email,
        "role": req.role,
        "created_at": time.time(),
    }
    MOCK_USERS.append(new_user)
    return {"status": "SUCCESS", "user": new_user}
