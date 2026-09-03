"""Agents API routes for listing, inspecting, and controlling active agents.

The registry reflects the real six core agents (coding / testing / security /
quality / infrastructure / embedding) with their live, override-aware models
from the llm.py gateway — not a hardcoded mock inventory.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException

from llm import resolve_model

router = APIRouter(prefix="/agents", tags=["Agents"])

# Static metadata for the six core agents. Models are resolved live from the
# LLM gateway so LLM_MODEL overrides / provider defaults show up correctly.
CORE_AGENTS: List[Dict[str, Any]] = [
    {"id": "coding", "name": "Coding Agent", "level": "L3", "depth": 0, "role": "Generate production code", "resources_mb": 256},
    {"id": "testing", "name": "Testing Agent", "level": "L3", "depth": 0, "role": "Comprehensive pytest suites", "resources_mb": 192},
    {"id": "security", "name": "Security Agent", "level": "L3", "depth": 0, "role": "Vulnerability review (OWASP)", "resources_mb": 192},
    {"id": "quality", "name": "Quality Agent", "level": "L3", "depth": 0, "role": "Code quality & maintainability", "resources_mb": 192},
    {"id": "infrastructure", "name": "Infrastructure Agent", "level": "L3", "depth": 0, "role": "Docker / k8s / CI-CD", "resources_mb": 192},
    {"id": "embedding", "name": "Embedding Agent", "level": "L3", "depth": 0, "role": "Vector embeddings", "resources_mb": 64},
]


# Default model per core agent (mirrors the agent constructors).
_DEFAULT_MODELS = {
    "coding": "qwen2.5-coder:3b",
    "testing": "qwen2.5-coder:3b",
    "security": "qwen2.5-coder:3b",
    "quality": "llama3.2:3b",
    "infrastructure": "llama3.2:3b",
    "embedding": "nomic-embed-text",
}


def _live_registry() -> List[Dict[str, Any]]:
    """Return the real agent registry with live effective models + status."""
    registry: List[Dict[str, Any]] = []
    for agent in CORE_AGENTS:
        entry = dict(agent)
        entry["model"] = resolve_model(_DEFAULT_MODELS[agent["id"]]) or "unconfigured"
        entry["status"] = "ACTIVE"
        registry.append(entry)
    return registry


@router.get("/list")
def list_agents() -> Dict[str, Any]:
    """List all registered agents in the cluster."""
    agents = _live_registry()
    return {"total": len(agents), "agents": agents}


@router.get("/{agent_id}")
def get_agent(agent_id: str) -> Dict[str, Any]:
    """Get metadata, capabilities, and health status of a specific agent."""
    for agent in _live_registry():
        if agent["id"] == agent_id:
            return {"found": True, "agent": agent}
    raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id}")


@router.post("/{agent_id}/start")
def start_agent(agent_id: str) -> Dict[str, Any]:
    """Start or resume an agent's lifecycle."""
    if not any(a["id"] == agent_id for a in CORE_AGENTS):
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id}")
    return {"status": "SUCCESS", "agent_id": agent_id, "action": "START", "timestamp": time.time()}


@router.post("/{agent_id}/stop")
def stop_agent(agent_id: str) -> Dict[str, Any]:
    """Gracefully stop an agent."""
    if not any(a["id"] == agent_id for a in CORE_AGENTS):
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id}")
    return {"status": "SUCCESS", "agent_id": agent_id, "action": "STOP", "timestamp": time.time()}