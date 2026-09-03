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
    """Validate all server endpoints including OpenAI compatibility."""

    def test_get_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "online"

    def test_get_agents(self):
        resp = client.get("/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 6

    def test_get_status(self):
        resp = client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_ram_required" in data
        assert "models" in data

    def test_post_run_single(self):
        resp = client.post("/run", json={"task": "Create healthcheck", "agent": "coding"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["agent"] == "coding"

    def test_post_run_all(self):
        resp = client.post("/run-all", json={"task": "Deploy microservice"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["total_agents"] == 6

    def test_post_openai_chat_completions(self):
        payload = {
            "model": "coding-agent",
            "messages": [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Create a python hello world function"},
            ],
        }
        resp = client.post("/v1/chat/completions", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "chat.completion"
        assert len(data["choices"]) > 0
        assert "content" in data["choices"][0]["message"]


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
