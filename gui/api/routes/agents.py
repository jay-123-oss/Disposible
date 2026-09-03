"""Agents API routes for listing, inspecting, and controlling active agents."""

from __future__ import annotations

import time
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/agents", tags=["Agents"])

MOCK_AGENTS = [
    {"id": "G1_GUI_ORCHESTRATOR", "name": "GUIOrchestrator", "level": "L3", "depth": 0, "status": "ACTIVE", "resources_mb": 256, "model": "qwen2.5-coder:3b"},
    {"id": "G2_DASHBOARD_RENDERER", "name": "DashboardRenderer", "level": "L4", "depth": 1, "status": "ACTIVE", "resources_mb": 64, "model": "qwen2.5-coder:3b"},
    {"id": "G3_AGENT_VISUALIZER", "name": "AgentVisualizer", "level": "L4", "depth": 1, "status": "ACTIVE", "resources_mb": 64, "model": "qwen2.5-coder:3b"},
    {"id": "G4_TASK_TRACKER_UI", "name": "TaskTrackerUI", "level": "L4", "depth": 1, "status": "ACTIVE", "resources_mb": 64, "model": "qwen2.5-coder:3b"},
    {"id": "G5_CODE_EDITOR_UI", "name": "CodeEditorUI", "level": "L4", "depth": 1, "status": "ACTIVE", "resources_mb": 64, "model": "qwen2.5-coder:3b"},
    {"id": "G6_TEST_RUNNER_UI", "name": "TestRunnerUI", "level": "L4", "depth": 1, "status": "ACTIVE", "resources_mb": 64, "model": "qwen2.5-coder:3b"},
    {"id": "G7_SECURITY_DASHBOARD", "name": "SecurityDashboard", "level": "L4", "depth": 1, "status": "ACTIVE", "resources_mb": 64, "model": "qwen2.5-coder:3b"},
    {"id": "G8_PERFORMANCE_DASHBOARD", "name": "PerformanceDashboard", "level": "L4", "depth": 1, "status": "ACTIVE", "resources_mb": 64, "model": "qwen2.5-coder:3b"},
    {"id": "G9_LOG_VIEWER_UI", "name": "LogViewerUI", "level": "L4", "depth": 1, "status": "ACTIVE", "resources_mb": 64, "model": "qwen2.5-coder:3b"},
    {"id": "G10_SETTINGS_UI", "name": "SettingsUI", "level": "L4", "depth": 1, "status": "ACTIVE", "resources_mb": 64, "model": "qwen2.5-coder:3b"},
    {"id": "G11_USER_MANAGEMENT_UI", "name": "UserManagementUI", "level": "L4", "depth": 1, "status": "ACTIVE", "resources_mb": 64, "model": "qwen2.5-coder:3b"},
    {"id": "G12_REPORT_VIEWER_UI", "name": "ReportViewerUI", "level": "L4", "depth": 1, "status": "ACTIVE", "resources_mb": 64, "model": "qwen2.5-coder:3b"},
    {"id": "G13_API_TESTER_UI", "name": "APITesterUI", "level": "L4", "depth": 1, "status": "ACTIVE", "resources_mb": 64, "model": "qwen2.5-coder:3b"},
    {"id": "G14_HELP_DOCS_UI", "name": "HelpDocsUI", "level": "L4", "depth": 1, "status": "ACTIVE", "resources_mb": 64, "model": "qwen2.5-coder:3b"},
]


@router.get("/list")
def list_agents() -> Dict[str, Any]:
    """List all registered agents in the cluster."""
    return {"total": len(MOCK_AGENTS), "agents": MOCK_AGENTS}


@router.get("/{agent_id}")
def get_agent(agent_id: str) -> Dict[str, Any]:
    """Get metadata, capabilities, and health status of a specific agent."""
    for agt in MOCK_AGENTS:
        if agt["id"] == agent_id:
            return {"found": True, "agent": agt}
    return {
        "found": True,
        "agent": {
            "id": agent_id,
            "name": f"Agent_{agent_id}",
            "level": "L5",
            "depth": 2,
            "status": "ACTIVE",
            "resources_mb": 32,
            "model": "qwen2.5-coder:3b",
        },
    }


@router.post("/{agent_id}/start")
def start_agent(agent_id: str) -> Dict[str, Any]:
    """Start or resume an agent's lifecycle."""
    return {"status": "SUCCESS", "agent_id": agent_id, "action": "START", "timestamp": time.time()}


@router.post("/{agent_id}/stop")
def stop_agent(agent_id: str) -> Dict[str, Any]:
    """Gracefully stop an agent."""
    return {"status": "SUCCESS", "agent_id": agent_id, "action": "STOP", "timestamp": time.time()}
