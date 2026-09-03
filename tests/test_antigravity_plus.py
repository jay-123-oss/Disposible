"""Unit and integration test suite for the Antigravity+ System."""

from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

from antigravity_plus.src.core.agent_swarm import AgentSwarmCoordinator, WorkspaceMode
from antigravity_plus.src.core.continuity_engine import (
    ContinuityEngine,
    IntelligentModelRouter,
    TokenAwareTaskSplitter,
)
from antigravity_plus.src.core.hybrid_arch import DisposableEnvironmentManager, LocalCloudSync
from antigravity_plus.src.core.self_healing import SelfHealingEngine
from antigravity_plus.src.tools.browser_tools import BrowserAutomationTool
from antigravity_plus.src.tools.file_tools import FileTools
from antigravity_plus.src.tools.preview_tools import CircleAnnotation, PreviewManager
from antigravity_plus.src.server import app


client = TestClient(app)


class TestContinuityEngine:
    def test_model_router_selection(self):
        router = IntelligentModelRouter()
        assert router.select_model("Write a simple add function") == "qwen2.5-coder:3b"
        assert router.select_model("Architect a distributed multi-tenant consensus algorithm") == "llama3.2:3b"

    def test_task_splitter_multi_chunk(self):
        splitter = TokenAwareTaskSplitter()
        chunks = splitter.split_task("Build fullstack web application")
        assert len(chunks) == 3
        assert chunks[0].index == 0

    def test_continuity_execution(self, tmp_path):
        engine = ContinuityEngine(storage_dir=str(tmp_path))
        def mock_runner(prompt, model, ctx):
            return {"result": f"Executed: {prompt} using {model}"}

        res = engine.execute_with_continuity("test-sess", "Build login flow", mock_runner)
        assert res["success"] is True
        assert res["chunks_processed"] == 3


class TestAgentSwarm:
    def test_dynamic_subagent_spawning(self, tmp_path):
        swarm = AgentSwarmCoordinator(workspace_root=str(tmp_path), max_workers=10)
        handoff = swarm.invoke_subagent(
            role="frontend",
            task_prompt="Build navbar",
            workspace_mode=WorkspaceMode.INHERIT,
        )
        assert handoff.status == "COMPLETED"
        assert handoff.role == "frontend"
        assert "subagent_id" in handoff.__dict__

    def test_parallel_mission_launch(self, tmp_path):
        swarm = AgentSwarmCoordinator(workspace_root=str(tmp_path), max_workers=10)
        def mock_worker(role, prompt, sandbox):
            return {"summary": f"Completed {role}", "files_modified": []}

        res = swarm.launch_mission(
            mission_name="Auth Service",
            roles=["coding", "testing"],
            task_prompts={},
            worker_func=mock_worker,
            workspace_mode=WorkspaceMode.INHERIT,
        )
        assert res["roles_executed"] == 2
        assert "coding" in res["handoffs"]
        assert "testing" in res["handoffs"]


class TestSelfHealing:
    def test_syntax_check(self, tmp_path):
        engine = SelfHealingEngine(workspace_root=str(tmp_path))
        good_file = tmp_path / "valid.py"
        good_file.write_text("x = 10\n", encoding="utf-8")
        assert engine.check_syntax(str(good_file)) is True

        bad_file = tmp_path / "invalid.py"
        bad_file.write_text("def broken_func(\n", encoding="utf-8")
        assert engine.check_syntax(str(bad_file)) is False


class TestHybridArch:
    def test_disposable_environment_snapshot_and_reset(self, tmp_path):
        test_ws = tmp_path / "workspace"
        test_ws.mkdir()
        (test_ws / "app.py").write_text("print('version 1')", encoding="utf-8")

        mgr = DisposableEnvironmentManager(base_workspace=str(test_ws))
        mgr.create_snapshot("initial")

        # Mutate
        (test_ws / "app.py").write_text("print('version 2 - corrupted')", encoding="utf-8")
        assert "version 2" in (test_ws / "app.py").read_text(encoding="utf-8")

        # Rollback
        mgr.reset_environment("initial")
        assert "version 1" in (test_ws / "app.py").read_text(encoding="utf-8")


class TestTools:
    def test_file_tools(self, tmp_path):
        ft = FileTools(workspace_root=str(tmp_path))
        write_res = ft.write_file("test.txt", "Hello World")
        assert write_res["success"] is True

        read_res = ft.read_file("test.txt")
        assert read_res["content"] == "Hello World"

        rep_res = ft.replace_content("test.txt", "World", "Antigravity+")
        assert rep_res["success"] is True
        assert ft.read_file("test.txt")["content"] == "Hello Antigravity+"

    def test_circle_to_edit_prompt_composition(self):
        pm = PreviewManager()
        annotation = CircleAnnotation(
            x=150.0,
            y=220.0,
            radius=45.0,
            instruction="Make button purple",
            target_element_tag="button",
        )
        bundle = pm.compose_circle_to_edit_prompt(annotation)
        assert "Make button purple" in bundle["prompt"]
        assert bundle["annotation"]["radius"] == 45.0


class TestFastAPIServer:
    def test_health_endpoint(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ONLINE"
        assert "UNLIMITED" in data["continuity_tokens"]

    def test_files_endpoint(self):
        resp = client.get("/api/files")
        assert resp.status_code == 200
        assert "files" in resp.json()

    def test_circle_to_edit_endpoint(self):
        resp = client.post("/api/circle-to-edit", json={
            "x": 100.0,
            "y": 150.0,
            "radius": 30.0,
            "instruction": "Change heading color to cyan"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["preview_reloaded"] is True

    def test_preview_endpoint(self):
        resp = client.get("/preview")
        assert resp.status_code == 200
        assert "html" in resp.headers.get("content-type", "").lower()
