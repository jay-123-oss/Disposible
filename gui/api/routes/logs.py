"""Logs API routes for searching, filtering, and streaming structured logs."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/logs", tags=["Logs"])


class LogSearchRequest(BaseModel):
    query: Optional[str] = ""
    level: Optional[str] = "INFO"
    limit: Optional[int] = 50


MOCK_LOGS = [
    {"timestamp": time.time() - 40, "level": "INFO", "logger": "FractalCore.Registry", "message": "Registered agent 'GUIOrchestrator' [G1_GUI_ORCHESTRATOR] (Level 0, RAM: 256 MB)"},
    {"timestamp": time.time() - 30, "level": "INFO", "logger": "FractalCore.AgentBase", "message": "Agent G1_GUI_ORCHESTRATOR spawned 13 UI coordinators"},
    {"timestamp": time.time() - 20, "level": "INFO", "logger": "FractalCore.QualityGate", "message": "Quality Gate QG_3_SYNTAX PASSED with score 98.25/100"},
    {"timestamp": time.time() - 10, "level": "INFO", "logger": "FractalCore.Orchestrator", "message": "WebSocket broadcasting telemetry tick to active connections"},
]


@router.post("/search")
def search_logs(req: LogSearchRequest) -> Dict[str, Any]:
    """Search and filter system logs."""
    filtered: List[Dict[str, Any]] = []
    q = (req.query or "").lower()
    lvl = (req.level or "INFO").upper()

    for item in MOCK_LOGS:
        if q and q not in item["message"].lower():
            continue
        filtered.append(item)

    return {"total": len(filtered), "logs": filtered[: req.limit or 50]}
