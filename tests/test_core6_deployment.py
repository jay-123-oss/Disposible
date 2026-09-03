"""Comprehensive test suite for the 6-Agent Core Auto-Deployment System."""

from __future__ import annotations

import json
import os
import pytest
from fastapi.testclient import TestClient

from agents.coding_agent import CodingAgent
from agents.embedding_agent import EmbeddingAgent
from agents.infrastructure_agent import InfrastructureAgent
from agents.quality_agent import QualityAgent
from agents.security_agent import SecurityAgent
from agents.testing_agent import TestingAgent
from orchestrator import Core6Orchestrator
from server import app
from gui.api.main import app as gui_app
from utils.colab_utils import ColabDeployer
from utils.kaggle_utils import KaggleDeployer
from utils.notebook_generator import (
    generate_colab_notebook,
    generate_kaggle_notebook,
    generate_and_save_all,
)
from utils.tunnel_manager import TunnelManager


client = TestClient(app)


class TestCore6Agents:
    """Validate individual lightweight agent behaviors and fallbacks."""

    def test_coding_agent(self):
        agent = CodingAgent()
        assert agent.agent_id == "coding"
        assert agent.model == "qwen2.5-coder:3b"
        res = agent.run("Create a Fibonacci function")
        assert res["success"] is True
        assert res["agent"] == "coding"
        assert "Fibonacci" in res["output"] or "def" in res["output"]

    def test_testing_agent(self):
        agent = TestingAgent()
        assert agent.agent_id == "testing"
        assert agent.model == "qwen2.5-coder:3b"
        res = agent.run("Test Fibonacci function")
        assert res["success"] is True
        assert res["agent"] == "testing"
        assert "pytest" in res["output"]

    def test_security_agent(self):
        agent = SecurityAgent()
        assert agent.agent_id == "security"
        assert agent.model == "qwen2.5-coder:3b"
        res = agent.run("Audit authentication service")
        assert res["success"] is True
        assert res["agent"] == "security"
        assert "Security Audit" in res["output"]

    def test_quality_agent(self):
        agent = QualityAgent()
        assert agent.agent_id == "quality"
        assert agent.model == "llama3.2:3b"
        res = agent.run("Review user service module")
        assert res["success"] is True
        assert res["agent"] == "quality"
        assert "Quality" in res["output"]

    def test_infrastructure_agent(self):
        agent = InfrastructureAgent()
        assert agent.agent_id == "infrastructure"
        assert agent.model == "llama3.2:3b"
        res = agent.run("Generate Dockerfile for FastAPI")
        assert res["success"] is True
        assert res["agent"] == "infrastructure"
        assert "FROM" in res["output"] or "Dockerfile" in res["output"]

    def test_embedding_agent(self):
        agent = EmbeddingAgent()
        assert agent.agent_id == "embedding"
        assert agent.model == "nomic-embed-text"
        vector = agent.embed("Sample semantic search query")
        assert len(vector) == 768
        res = agent.run("Search database")
        assert res["success"] is True
        assert res["dimensions"] == 768


class TestCoreOrchestrator:
    """Validate 6-agent orchestration, pipeline execution, and parallel processing."""

    def test_available_agents(self):
        orch = Core6Orchestrator()
        agents = orch.get_available_agents()
        assert len(agents) == 6
        agent_ids = {a["id"] for a in agents}
        assert agent_ids == {"coding", "testing", "security", "quality", "infrastructure", "embedding"}

    def test_process_single_agent(self):
        orch = Core6Orchestrator()
        res = orch.process("Build a REST API", "coding")
        assert res["success"] is True
        assert res["agent"] == "coding"
        assert "latency_seconds" in res

    def test_process_all_agents_sequential(self):
        orch = Core6Orchestrator()
        res = orch.process_all("Implement user registration")
        assert res["success"] is True
        assert res["total_agents"] == 6
        assert "coding" in res["results"]
        assert "testing" in res["results"]
        assert "security" in res["results"]
        assert "quality" in res["results"]
        assert "infrastructure" in res["results"]
        assert "embedding" in res["results"]

    def test_process_parallel(self):
        orch = Core6Orchestrator()
        res = orch.process_parallel("Quick check", agent_types=["coding", "testing"])
        assert res["success"] is True
        assert res["parallel_count"] == 2
        assert "coding" in res["results"]
        assert "testing" in res["results"]


class TestFastAPIServer:
    """End-to-end validation of the REAL API surfaces.

    server.py      -> GET /, /api/status, /api/files, /api/file, /api/chat,
                      /api/staged-file, /api/accept, /api/reject, /ws
    gui/api/main.py -> POST /run, POST /run-all, GET /api/v1/agents/list

    Each test drives a live endpoint through TestClient and asserts its actual
    response contract (no fake/aspirational endpoints such as /agents, /status,
    /run-all on server.py, or /v1/chat/completions).
    """

    PROBE = "qa_core6_probe.py"
    REJECT = "qa_core6_reject.py"
    WS_PROBE = "qa_core6_ws.py"

    def _cleanup(self):
        for name in (self.PROBE, self.REJECT, self.WS_PROBE):
            if os.path.exists(name):
                os.remove(name)

    def test_get_root_serves_ide_frontend(self):
        """GET / on server.py serves the IDE single-page frontend (HTML)."""
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        assert "Antigravity" in resp.text

    def test_get_api_status_reports_models_and_health(self):
        """GET /api/status reports a ready system and the 6-agent model map."""
        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data.get("ide_version")
        models = data.get("models", {})
        # The six core swarm agents (plus planning/embedding) must be mapped to real models.
        for role in ("planning", "coding", "testing", "security", "quality", "infrastructure", "embedding"):
            assert role in models, f"missing model mapping for {role}"
            assert models[role], f"empty model name for {role}"

    def test_api_status_models_reflect_llm_model_override(self, monkeypatch):
        """/api/status model telemetry must honour LLM_MODEL, matching agent results."""
        monkeypatch.setenv("LLM_MODEL", "override-test-model")
        resp = client.get("/api/status")
        assert resp.status_code == 200
        models = resp.json()["models"]
        assert models["coding"] == "override-test-model"
        assert models["embedding"] == "override-test-model"

    def test_get_files_tree_and_file_read(self):
        """GET /api/files returns the explorer tree; GET /api/file reads content."""
        resp = client.get("/api/files")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        top_level = {entry["name"]: entry for entry in data.get("files", [])}
        assert "server.py" in top_level
        for entry in data["files"]:
            assert "name" in entry and "path" in entry and "isDirectory" in entry

        file_resp = client.get("/api/file/server.py")
        assert file_resp.status_code == 200
        body = file_resp.json()
        assert body["status"] == "success"
        assert "FastAPI" in body["content"]

    def test_gui_agents_registry_list(self):
        """GET /api/v1/agents/list returns the REAL six core agents with live models."""
        with TestClient(gui_app) as c:
            resp = c.get("/api/v1/agents/list")
        assert resp.status_code == 200
        data = resp.json()
        agents = data.get("agents", [])
        assert data["total"] == len(agents) == 6
        ids = [a["id"] for a in agents]
        # The real core swarm, deterministic order.
        assert ids == ["coding", "testing", "security", "quality", "infrastructure", "embedding"]
        for agent in agents:
            assert agent["id"]
            assert agent["name"]
            assert "level" in agent
            assert agent["status"] == "ACTIVE"
            assert agent["model"], "every core agent must report a live model"

    def test_gui_agents_registry_unknown_agent_404(self):
        """GET /api/v1/agents/{id} returns 404 for agents that do not exist."""
        with TestClient(gui_app) as c:
            resp = c.get("/api/v1/agents/G1_GUI_ORCHESTRATOR")
        assert resp.status_code == 404
        with TestClient(gui_app) as c:
            known = c.get("/api/v1/agents/coding")
        assert known.status_code == 200
        assert known.json()["agent"]["id"] == "coding"

    def test_gui_run_single_agent(self):
        """POST /run dispatches a task to one core agent through Core6Orchestrator."""
        with TestClient(gui_app) as c:
            resp = c.post("/run", json={"task": "Create healthcheck", "agent": "coding"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["agent"] == "coding"
        assert data["model"] == "qwen2.5-coder:3b"
        assert data.get("output")  # real output (Ollama response or offline fallback)
        assert "latency_seconds" in data

    def test_gui_run_all_agents(self):
        """POST /run-all executes the full 6-agent pipeline and returns each result."""
        with TestClient(gui_app) as c:
            resp = c.post("/run-all", json={"task": "Deploy microservice"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["total_agents"] == 6
        results = data.get("results", {})
        assert set(results.keys()) == {"coding", "testing", "security", "quality", "infrastructure", "embedding"}
        for agent_id, agent_result in results.items():
            assert agent_result["success"] is True, f"{agent_id} failed: {agent_result}"

    def test_chat_mutation_accept_lifecycle(self):
        """POST /api/chat -> staged content map + deltas -> staged-file preview -> accept/reject."""
        self._cleanup()
        try:
            # --- chat stages a file (nothing written to disk yet) -------------------
            resp = client.post(
                "/api/chat",
                json={"prompt": f"create {self.PROBE} hello world", "session_id": "core6-acc"},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "success"
            assert body["intent"] == "CREATE"
            assert body["execution_mode"] == "MUTATION"
            assert body["files_count"] == 1

            files = body["files"]
            assert isinstance(files, dict), "files must be a {path: content} map"
            assert self.PROBE in files
            assert "Hello" in files[self.PROBE]
            assert not os.path.exists(self.PROBE), "staged files must not hit disk before accept"

            deltas = body["deltas"]
            assert len(deltas) == 1
            assert deltas[0]["path"] == self.PROBE
            assert deltas[0]["status"] == "CREATED"
            assert deltas[0]["linesAdded"] >= 1
            assert deltas[0]["linesDeleted"] == 0

            # --- staged-file endpoint serves the not-yet-written content -------------
            staged = client.get(
                "/api/staged-file",
                params={"session_id": "core6-acc", "path": self.PROBE},
            )
            assert staged.status_code == 200
            staged_body = staged.json()
            assert staged_body["status"] == "success"
            assert staged_body["staged"] is True
            assert "Hello" in staged_body["content"]

            # --- accept commits the file to disk -------------------------------------
            accepted = client.post("/api/accept", json={"session_id": "core6-acc"})
            assert accepted.status_code == 200
            assert accepted.json()["status"] == "success"
            assert self.PROBE in accepted.json()["committed_files"]
            assert os.path.exists(self.PROBE)
            with open(self.PROBE, encoding="utf-8") as f:
                assert "Hello" in f.read()

            # --- reject discards a separate staged file -------------------------------
            chat2 = client.post(
                "/api/chat",
                json={"prompt": f"create {self.REJECT} hello world", "session_id": "core6-rej"},
            )
            assert chat2.json()["files_count"] == 1
            rejected = client.post("/api/reject", json={"session_id": "core6-rej"})
            assert rejected.json()["status"] == "rejected"
            assert not os.path.exists(self.REJECT)
        finally:
            self._cleanup()

    def test_websocket_chat_stream_and_accept(self):
        """/ws streams real orchestrator events and accepts staged files end to end."""
        self._cleanup()
        try:
            with TestClient(app) as c:
                with c.websocket_connect("/ws") as ws:
                    greeting = ws.receive_json()
                    assert greeting["type"] == "agent_message"
                    assert greeting["sender"] == "agent"

                    ws.send_json({"action": "chat", "prompt": f"create {self.WS_PROBE} hello world"})
                    event_types = []
                    completed = None
                    for _ in range(40):
                        msg = ws.receive_json()
                        event_types.append(msg["type"])
                        if msg["type"] == "swarm_completed":
                            completed = msg
                            break
                    assert completed is not None, f"no swarm_completed; events={event_types}"
                    assert self.WS_PROBE in completed["files"]
                    assert len(completed.get("deltas") or []) == 1
                    assert "status_update" in event_types  # real-time stream observed

                    ws.send_json({"action": "accept"})
                    action_result = None
                    for _ in range(5):
                        msg = ws.receive_json()
                        if msg["type"] == "action_result":
                            action_result = msg
                            break
                    assert action_result is not None
                    assert action_result["status"] == "accepted"
                    assert self.WS_PROBE in action_result["files"]
                    assert os.path.exists(self.WS_PROBE)
                    with open(self.WS_PROBE, encoding="utf-8") as f:
                        assert "Hello" in f.read()
        finally:
            self._cleanup()


class TestNotebookGenerator:
    """Validate notebook structures for Kaggle and Colab."""

    def test_kaggle_notebook_structure(self):
        nb = generate_kaggle_notebook()
        assert nb["nbformat"] == 4
        # 1 markdown header + 7 code cells = 8 cells
        assert len(nb["cells"]) >= 7
        all_sources = "".join("".join(c["source"]) for c in nb["cells"])
        assert "qwen2.5-coder:3b" in all_sources
        assert "llama3.2:3b" in all_sources
        assert "nomic-embed-text" in all_sources
        assert "CodingAgent" in all_sources
        assert "TestingAgent" in all_sources
        assert "SecurityAgent" in all_sources
        assert "QualityAgent" in all_sources
        assert "InfrastructureAgent" in all_sources
        assert "EmbeddingAgent" in all_sources
        assert "cloudflared" in all_sources

    def test_colab_notebook_structure(self):
        nb = generate_colab_notebook()
        assert nb["nbformat"] == 4
        assert len(nb["cells"]) >= 7
        all_sources = "".join("".join(c["source"]) for c in nb["cells"])
        assert "qwen2.5-coder:3b" in all_sources
        assert "pyngrok" in all_sources

    def test_generate_and_save_all(self, tmp_path):
        out_dir = str(tmp_path / "notebooks_test")
        paths = generate_and_save_all(out_dir)
        assert os.path.exists(paths["kaggle"])
        assert os.path.exists(paths["colab"])


class TestDeployersAndTunnels:
    """Validate Kaggle/Colab deployers and tunnel managers."""

    def test_kaggle_deployer_load_config(self):
        deployer = KaggleDeployer()
        assert "username" in deployer.config
        assert "models" in deployer.config

    def test_colab_deployer_load_config(self):
        deployer = ColabDeployer()
        assert "runtime" in deployer.config

    def test_tunnel_manager_default(self):
        mgr = TunnelManager(port=8000, tunnel_type="cloudflare")
        url = mgr.get_public_url()
        assert "trycloudflare.com" in url
