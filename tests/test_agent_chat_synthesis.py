"""Tests for routing /api/chat + /ws EXPLAIN/ANALYZE/DEBUG through the six
API-key agents (llm.py gateway) instead of canned deterministic templates.

The code under test is core.canonical_orchestrator.execute_prompt, which both
/api/chat and /ws call. Hosted-agent synthesis only fires when the canonical
orchestrator's ``is_key_configured()`` is true — we force that on and swap the
six agent classes for deterministic stubs, so the tests prove the
routing/assembly/context plumbing without any real network call.
"""

from __future__ import annotations

import asyncio
import json
import os

import pytest
from fastapi.testclient import TestClient

import core.canonical_orchestrator as co
import server as root_server

client = TestClient(root_server.app)

_AGENT_CLASS = {
    "coding": "CodingAgent",
    "testing": "TestingAgent",
    "security": "SecurityAgent",
    "quality": "QualityAgent",
    "infrastructure": "InfrastructureAgent",
    "embedding": "EmbeddingAgent",
}

LLM_KEYS = [
    "LLM_PROVIDER",
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "ANTHROPIC_API_KEY",
    "LLM_API_KEY",
    "LLM_MODEL",
    "LLM_BASE_URL",
]

STUB_ANSWERS = {
    "coding": "REAL-CODING-ANSWER: this project is an Electron + FastAPI multi-agent IDE.",
    "testing": "REAL-TESTING-ANSWER: pytest should cover the orchestrator lifecycle.",
    "security": "REAL-SECURITY-ANSWER: no hardcoded secrets found in staged changes.",
    "quality": "REAL-QUALITY-ANSWER: SOLID-compliant structure overall.",
    "infrastructure": "REAL-INFRA-ANSWER: runs fine under docker-compose.",
    "embedding": "vector-summary-only",
}


def _install_agent_stubs(monkeypatch, answers=None, capture=None):
    """Replace the six agent classes used by the canonical orchestrator.

    ``capture`` (optional list) collects every task prompt the stubs receive.
    """
    answers = answers or STUB_ANSWERS

    class StubAgent:
        def __init__(self, agent_id, text):
            self.agent_id = agent_id
            self._text = text

        def run(self, task, context=None):
            if capture is not None:
                capture.append(task)
            return {"success": True, "agent": self.agent_id, "model": "stub", "output": self._text}

    for agent_id, cls_name in _AGENT_CLASS.items():
        factory = type(
            cls_name,
            (),
            {"__new__": (lambda cls, aid=agent_id, txt=answers[agent_id]: StubAgent(aid, txt))},
        )
        monkeypatch.setattr(co, cls_name, factory)


@pytest.fixture(autouse=True)
def _clean_llm_env(monkeypatch):
    for key in LLM_KEYS:
        monkeypatch.delenv(key, raising=False)


def _force_keyed_mode(monkeypatch):
    monkeypatch.setattr(co, "is_key_configured", lambda: True)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-never-used-1234567890")


# --------------------------------------------------------------------------
# Offline behaviour must stay exactly as before (no hosted key -> canned)
# --------------------------------------------------------------------------
def test_offline_explain_keeps_deterministic_summary():
    resp = client.post("/api/chat", json={"prompt": "explain this project architecture"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "Project Architecture Overview" in data["summary"]
    assert "Real Analysis by 6-Agent Swarm" not in data["summary"]
    assert data["files"] == {}


# --------------------------------------------------------------------------
# Keyed mode: EXPLAIN / ANALYZE / DEBUG routed through the six stub agents
# --------------------------------------------------------------------------
def test_keyed_explain_routes_through_agents(monkeypatch):
    _force_keyed_mode(monkeypatch)
    _install_agent_stubs(monkeypatch)

    resp = client.post("/api/chat", json={"prompt": "explain what this project does"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    summary = data["summary"]
    assert "Real Analysis by 6-Agent Swarm" in summary
    assert "REAL-CODING-ANSWER" in summary
    assert "REAL-TESTING-ANSWER" in summary
    assert "Backend: openai" in summary
    # Real content replaced the canned template entirely.
    assert "Project Architecture Overview" not in summary
    # Staging/accept contract intact for read-only intents.
    assert data["files"] == {}
    assert data["intent"] == "EXPLAIN"


def test_keyed_analyze_and_debug_route_through_agents(monkeypatch):
    _force_keyed_mode(monkeypatch)
    _install_agent_stubs(monkeypatch)

    for prompt, intent in [("analyze the codebase for bugs", "ANALYZE"),
                           ("fix the bug in server.py", "DEBUG")]:
        resp = client.post("/api/chat", json={"prompt": prompt})
        data = resp.json()
        assert data["intent"] == intent
        assert "Real Analysis by 6-Agent Swarm" in data["summary"]
        assert "REAL-CODING-ANSWER" in data["summary"]


def test_create_still_stages_files_when_keyed(monkeypatch):
    """CREATE keeps the staging flow (files -> staged) even in keyed mode."""
    _force_keyed_mode(monkeypatch)
    _install_agent_stubs(monkeypatch)

    resp = client.post("/api/chat", json={"prompt": "create qa_synth_probe.py hello world"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "CREATE"
    # Deterministic create path (not agent synthesis) + staged content map.
    assert "qa_synth_probe.py" in data["files"]
    assert "Hello" in data["files"]["qa_synth_probe.py"]


# --------------------------------------------------------------------------
# Keyed mode over the /ws chat stream
# --------------------------------------------------------------------------
def test_keyed_explain_over_websocket(monkeypatch):
    _force_keyed_mode(monkeypatch)
    _install_agent_stubs(monkeypatch)

    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"action": "chat", "prompt": "explain the architecture please"}))
        seen = []
        while True:
            msg = json.loads(ws.receive_text())
            seen.append(msg.get("type"))
            if msg.get("type") == "swarm_completed":
                assert "Real Analysis by 6-Agent Swarm" in msg.get("text", "")
                assert msg.get("files") == []
                break
            if len(seen) > 80:
                pytest.fail("swarm_completed never arrived")
    assert "swarm_completed" in seen


# --------------------------------------------------------------------------
# Unit level: context digest + graceful degrade when the backend is down
# --------------------------------------------------------------------------
def test_synthesize_includes_real_context(monkeypatch):
    _force_keyed_mode(monkeypatch)
    tasks = []
    _install_agent_stubs(monkeypatch, capture=tasks)

    orch = co.CanonicalOrchestrator(workspace_root=os.path.abspath("."))
    context = {"selected_files": ["server.py"], "budget_remaining": 10}

    # The digest embeds real file content for the agents to reason over.
    digest = orch._build_context_digest("explain the server", context)
    assert "server.py" in digest and "FastAPI" in digest

    text = asyncio.run(orch._synthesize_agent_response(
        "explain the server", "explain", context, {"new.py": "print('hi')"}
    ))
    assert "Real Analysis by 6-Agent Swarm" in text
    assert "REAL-CODING-ANSWER" in text
    # Every one of the six agents actually received the task prompt.
    assert len(tasks) == 6
    assert all(t.startswith("[User request]\nexplain the server") for t in tasks)
    # Staged file names are surfaced to the agents (never their contents).
    assert all("[Files staged for review] new.py" in t for t in tasks)


def test_synthesize_degrades_when_backend_down(monkeypatch):
    _force_keyed_mode(monkeypatch)
    offline = {
        aid: "```python\n# Solution for: [User request]\nwrite actual code here\n```"
        for aid in _AGENT_CLASS
    }
    _install_agent_stubs(monkeypatch, answers=offline)

    orch = co.CanonicalOrchestrator(workspace_root=os.path.abspath("."))
    text = asyncio.run(orch._synthesize_agent_response(
        "explain the server", "explain", {"selected_files": [], "budget_remaining": 0}, {}
    ))
    # Every agent returned its offline fallback -> caller uses the canned summary.
    assert text == ""
