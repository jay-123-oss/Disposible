"""Tests for the LLM provider settings endpoints (GET/POST /api/settings/llm).

The real repo .env is never touched: ``server.ENV_FILE`` is monkeypatched to a
temp file and every LLM_*/provider key is stripped from os.environ around each
test so llm.py resolution starts from a clean, deterministic state.
"""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

import server
from llm import PROVIDER_PRESETS

client = TestClient(server.app)

# Keys the settings endpoints may touch (env + .env file).
LLM_KEYS = [
    "LLM_PROVIDER",
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "ANTHROPIC_API_KEY",
    "LLM_API_KEY",
    "LLM_MODEL",
    "LLM_BASE_URL",
]


def _isolate(tmp_path, monkeypatch) -> str:
    """Point server.ENV_FILE at a fresh temp file and clean LLM env vars."""
    env_path = str(tmp_path / ".env")
    monkeypatch.setattr(server, "ENV_FILE", env_path)
    for key in LLM_KEYS:
        monkeypatch.delenv(key, raising=False)
    return env_path


def _read_env(path: str) -> dict:
    result = {}
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                k, _, v = stripped.partition("=")
                result[k.strip()] = v.strip()
    return result


def test_get_settings_reports_live_status_and_provider_options(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    resp = client.get("/api/settings/llm")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"

    # Live gateway status (no key configured -> ollama fallback)
    llm = data["llm"]
    assert llm["provider"] == "ollama"
    assert llm["key_configured"] is False
    assert llm["mode"] == "local-ollama"
    assert "supported_providers" in llm

    # Provider option metadata mirrors llm.PROVIDER_PRESETS
    providers = {p["id"]: p for p in data["providers"]}
    assert set(providers) == set(PROVIDER_PRESETS)
    for pid, preset in PROVIDER_PRESETS.items():
        opt = providers[pid]
        assert opt["key_env"] == preset.get("key_env")
        assert opt["default_model"] == preset.get("default_model")
        assert opt["label"]
    assert providers["openai-compatible"]["needs_base_url"] is True
    assert providers["ollama"]["needs_key"] is False
    assert providers["openai"]["needs_key"] is True


def test_save_key_persists_to_env_file_and_process(tmp_path, monkeypatch):
    env_path = _isolate(tmp_path, monkeypatch)
    # Pre-existing unrelated content must survive the merge.
    with open(env_path, "w", encoding="utf-8") as fh:
        fh.write("# keep me\nMODEL1=qwen2.5-coder:3b\nKAGGLE_KEY=old-value\n")

    resp = client.post("/api/settings/llm", json={
        "provider": "openai",
        "api_key": "sk-test-secret-1234",
        "model": "gpt-4o-mini",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "OPENAI_API_KEY" in data["stored_keys"]
    assert "LLM_PROVIDER" in data["stored_keys"]
    assert "LLM_MODEL" in data["stored_keys"]

    # Live process env updated immediately (no restart needed).
    assert os.environ["OPENAI_API_KEY"] == "sk-test-secret-1234"
    assert os.environ["LLM_PROVIDER"] == "openai"

    # Response only ever carries the masked key.
    assert data["llm"]["provider"] == "openai"
    assert data["llm"]["key_configured"] is True
    assert data["llm"]["key_masked"] == "sk-t...1234"
    assert "sk-test-secret-1234" not in str(data)

    # .env file updated, unrelated lines + comments preserved.
    env = _read_env(env_path)
    assert env["LLM_PROVIDER"] == "openai"
    assert env["OPENAI_API_KEY"] == "sk-test-secret-1234"
    assert env["LLM_MODEL"] == "gpt-4o-mini"
    assert env["MODEL1"] == "qwen2.5-coder:3b"
    assert env["KAGGLE_KEY"] == "old-value"
    with open(env_path, "r", encoding="utf-8") as fh:
        assert "# keep me" in fh.read()


def test_clear_key_and_switch_to_ollama(tmp_path, monkeypatch):
    env_path = _isolate(tmp_path, monkeypatch)
    client.post("/api/settings/llm", json={"provider": "openai", "api_key": "sk-abc-1234567890"})
    assert os.environ.get("LLM_PROVIDER") == "openai"

    # Switching to ollama removes the LLM_PROVIDER override usage; the stored
    # key of the previous provider stays saved (harmless, unused) in .env.
    resp = client.post("/api/settings/llm", json={"provider": "ollama"})
    assert resp.status_code == 200
    assert resp.json()["llm"]["mode"] == "local-ollama"
    env = _read_env(env_path)
    assert env["LLM_PROVIDER"] == "ollama"
    assert env["OPENAI_API_KEY"] == "sk-abc-1234567890"

    # Explicitly clearing the key removes the line from .env + process env.
    resp = client.post("/api/settings/llm", json={"provider": "openai", "clear_key": True})
    assert resp.status_code == 200
    assert resp.json()["llm"]["key_configured"] is False
    env = _read_env(env_path)
    assert "OPENAI_API_KEY" not in env
    assert "OPENAI_API_KEY" not in os.environ


def test_key_ignored_for_keyless_provider(tmp_path, monkeypatch):
    """Regression: sending an api_key together with a keyless provider (ollama)
    must not crash (key_env is None for ollama) and must not persist a key."""
    env_path = _isolate(tmp_path, monkeypatch)
    resp = client.post("/api/settings/llm", json={
        "provider": "ollama",
        "api_key": "sk-should-be-ignored-12345",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["llm"]["mode"] == "local-ollama"
    assert data["llm"]["key_configured"] is False
    assert "OPENAI_API_KEY" not in data["stored_keys"]
    assert "OPENAI_API_KEY" not in _read_env(env_path)
    assert "OPENAI_API_KEY" not in os.environ


def test_invalid_provider_rejected(tmp_path, monkeypatch):
    env_path = _isolate(tmp_path, monkeypatch)
    resp = client.post("/api/settings/llm", json={"provider": "not-a-provider", "api_key": "x"})
    assert resp.status_code == 400
    assert "not-a-provider" in resp.json()["detail"]
    # Nothing persisted.
    assert not os.path.exists(env_path) or "LLM_PROVIDER=not-a-provider" not in open(env_path, encoding="utf-8").read()
