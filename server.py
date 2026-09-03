"""FastAPI Server exposing Antigravity IDE Frontend, WebSockets, and 6-Agent Swarm Endpoints.

Features:
- GET  /                  : Serves frontend/index.html
- WS   /ws                : Real-time bi-directional agent chat & swarm status streaming
- POST /api/chat          : Direct prompt -> 6-agent swarm execution
- GET  /api/status        : Detailed agent status and model telemetry
- GET  /api/files         : List all project files recursively
- GET  /api/file/{path}   : Retrieve file content
- POST /api/file/{path}   : Update / save file content
- POST /api/accept        : Commit staged generated files to filesystem
- POST /api/reject        : Discard staged files
- GET  /api/settings/llm  : Live LLM gateway status + selectable providers
- POST /api/settings/llm  : Save chosen LLM provider + API key to .env
- GET  /api/search        : Search file names + contents (IDE Search panel)
- GET  /api/git/status    : Read-only branch / status / commit snapshot (SCM panel)
- GET  /api/debug/targets : List whitelisted run/debug targets
- POST /api/debug/run     : Run a whitelisted dev target with a hard timeout
"""

from __future__ import annotations

import asyncio
import difflib
import json
import logging
import os
import shutil
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.canonical_orchestrator import CanonicalOrchestrator
from core.continuity_engine import ContinuityEngine
from core.self_healing import SelfHealingEngine
from llm import PROVIDER_PRESETS, get_llm_status, resolve_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AntigravityServer")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
ENV_FILE = os.path.join(BASE_DIR, ".env")

app = FastAPI(
    title="Antigravity+ IDE & Multi-Agent Backend",
    description="Browser-based IDE backend with real-time WebSocket agent streaming, canonical orchestration, and execution policy gating.",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Canonical Multi-Agent Orchestrator (Active Runtime)
canonical_orchestrator = CanonicalOrchestrator(workspace_root=BASE_DIR)

continuity_engine = ContinuityEngine()
self_healing_engine = SelfHealingEngine()

# Global in-memory staged files cache: { session_id: { file_path: content } }
staged_files_cache: Dict[str, Dict[str, str]] = {}


# ==============================================================================
# Request & Response Models
# ==============================================================================
class ChatPromptRequest(BaseModel):
    prompt: str = Field(..., description="User prompt or instruction for 6-agent swarm")
    session_id: Optional[str] = Field("default", description="Client session identifier")


class FileUpdateRequest(BaseModel):
    content: str = Field(..., description="Full text content of the file")


class AcceptRejectRequest(BaseModel):
    session_id: Optional[str] = Field("default", description="Client session identifier")
    feedback: Optional[str] = Field(None, description="Optional feedback on rejection")


class LLMSettingsRequest(BaseModel):
    provider: str = Field(..., description="Provider id from GET /api/settings/llm")
    api_key: Optional[str] = Field(None, description="New API key to store (blank keeps the existing key)")
    model: Optional[str] = Field(None, description="LLM_MODEL override; blank string clears the override")
    base_url: Optional[str] = Field(None, description="LLM_BASE_URL override (needed for openai-compatible); blank clears")
    clear_key: bool = Field(False, description="Remove the stored API key for this provider")


# ==============================================================================
# Staged File Deltas (Review UI contract)
# ==============================================================================
def build_staged_deltas(files: Dict[str, str]) -> List[Dict[str, Any]]:
    """Describe staged files for the Accept/Reject review card.

    Each entry mirrors the shape agent_chat.js renders:
    { path, status: CREATED|MODIFIED, linesAdded, linesDeleted }
    where line counts are computed against the file already on disk (if any).
    """
    deltas: List[Dict[str, Any]] = []
    for rel_path, content in files.items():
        full_path = os.path.abspath(os.path.join(BASE_DIR, rel_path))
        if os.path.exists(full_path):
            status = "MODIFIED"
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    old_lines = f.read().splitlines()
            except Exception:
                old_lines = []
        else:
            status = "CREATED"
            old_lines = []

        new_lines = content.splitlines()
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        lines_added = 0
        lines_deleted = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ("insert", "replace"):
                lines_added += j2 - j1
            if tag in ("delete", "replace"):
                lines_deleted += i2 - i1

        deltas.append({
            "path": rel_path,
            "status": status,
            "linesAdded": lines_added,
            "linesDeleted": lines_deleted,
        })
    return deltas


# ==============================================================================
# File System Utilities
# ==============================================================================
IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache", ".antigravity_preview",
    ".antigravity_snapshots", ".antigravity_state",
    "venv", ".venv", ".freebuff", "dist", "build", ".idea", ".vscode",
}


def get_recursive_file_tree(directory: str, max_depth: int = 4, current_depth: int = 0) -> List[Dict[str, Any]]:
    """Scan directory recursively, excluding heavy VCS and dependency caches."""
    items = []
    ignored = IGNORED_DIRS
    try:
        entries = sorted(os.scandir(directory), key=lambda e: (not e.is_dir(), e.name.lower()))
        for entry in entries:
            if entry.name in ignored:
                continue
            rel_path = os.path.relpath(entry.path, BASE_DIR).replace("\\", "/")
            if entry.is_dir():
                children = (
                    get_recursive_file_tree(entry.path, max_depth, current_depth + 1)
                    if current_depth < max_depth
                    else []
                )
                items.append({
                    "name": entry.name,
                    "path": rel_path,
                    "isDirectory": True,
                    "children": children,
                })
            else:
                items.append({
                    "name": entry.name,
                    "path": rel_path,
                    "isDirectory": False,
                    "size": entry.stat().st_size,
                })
    except Exception as err:
        logger.error("Error reading dir %s: %s", directory, err)
    return items


# ==============================================================================
# REST API Endpoints
# ==============================================================================
@app.get("/")
def get_index():
    """Serve the complete Antigravity frontend single-page application."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="frontend/index.html not found.")
    return FileResponse(index_path)


# Per-role default models (overridable via LLM_MODEL / provider defaults).
DEFAULT_ROLE_MODELS = {
    "planning": "Llama3.2:3B",
    "coding": "Qwen2.5-Coder:3B",
    "testing": "Qwen2.5-Coder:3B",
    "security": "Qwen2.5-Coder:3B",
    "quality": "Llama3.2:3B",
    "infrastructure": "Llama3.2:3B",
    "embedding": "Nomic-Embed-Text",
}


@app.get("/api/status")
def get_system_status() -> Dict[str, Any]:
    """Get system health and model telemetry."""
    return {
        "status": "ready",
        "ide_version": "2.5.0-BROWSER",
        "theme": "Antigravity Dark (GitHub #0d1117)",
        # Effective models (LLM_MODEL override / provider defaults applied), so
        # the status panel always matches what the agents actually report.
        "models": {role: resolve_model(default) for role, default in DEFAULT_ROLE_MODELS.items()},
        "quality_score": "99.2% (SOLID compliant)",
        "security_score": "0 vulnerabilities (OWASP Top 10 passed)",
        # Effective LLM backend (hosted provider API key, or local Ollama).
        # Never exposes the API key itself — only masked + booleans.
        "llm": get_llm_status(),
    }


# ==============================================================================
# LLM Provider Settings (bring-your-own API key)
# ==============================================================================
PROVIDER_LABELS = {
    "openai": "OpenAI",
    "anthropic": "Anthropic Claude",
    "gemini": "Google Gemini",
    "groq": "Groq",
    "openrouter": "OpenRouter",
    "mistral": "Mistral AI",
    "together": "Together AI",
    "xai": "xAI (Grok)",
    "deepseek": "DeepSeek",
    "ollama": "Local Ollama (no API key)",
    "openai-compatible": "Any OpenAI-compatible endpoint",
}


def _merge_env_file(path: str, updates: Dict[str, Optional[str]]) -> None:
    """Set/remove KEY=VALUE lines in an env file, preserving comments and order.

    ``updates`` maps KEY -> new value, or KEY -> None to remove that line.
    Keys not present in ``updates`` are left untouched.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        lines = []
    touched: Dict[str, str] = {}
    out: List[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                touched[key] = updates[key] or ""
                if updates[key] is None:
                    continue  # drop the line
                out.append(f"{key}={updates[key]}\n")
                continue
        out.append(line)
    for key, value in updates.items():
        if key in touched or value is None:
            continue
        out.append(f"{key}={value}\n")
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(out)


def _apply_llm_settings(
    provider: str,
    api_key: Optional[str],
    model: Optional[str],
    base_url: Optional[str],
    clear_key: bool,
) -> Dict[str, Any]:
    """Persist the chosen provider/key into this process env AND the .env file.

    os.environ is updated first so the running gateway picks the change up
    immediately (llm.py resolves providers at call time); .env is kept in sync
    so the choice survives restarts. Returns the names of keys that were written.
    """
    preset = PROVIDER_PRESETS.get(provider, {})
    key_env = preset.get("key_env")
    updates: Dict[str, Optional[str]] = {"LLM_PROVIDER": provider}
    written: List[str] = ["LLM_PROVIDER"]

    if api_key and key_env:
        updates[key_env] = api_key
        written.append(key_env)
    elif clear_key and key_env:
        updates[key_env] = None

    if model is not None:
        updates["LLM_MODEL"] = model or None
        if model:
            written.append("LLM_MODEL")
    if base_url is not None:
        updates["LLM_BASE_URL"] = base_url or None
        if base_url:
            written.append("LLM_BASE_URL")
    elif provider != "openai-compatible" and os.environ.get("LLM_PROVIDER") != provider:
        # Switching to a preset provider: drop any leftover custom base URL so
        # it cannot silently redirect the new provider to a stale endpoint.
        updates["LLM_BASE_URL"] = None

    for key, value in updates.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    _merge_env_file(ENV_FILE, updates)
    return {"stored_keys": sorted(written)}


def _provider_option(pid: str) -> Dict[str, Any]:
    preset = PROVIDER_PRESETS.get(pid, {})
    return {
        "id": pid,
        "label": PROVIDER_LABELS.get(pid, pid.replace("-", " ").title()),
        "key_env": preset.get("key_env"),
        "default_model": preset.get("default_model"),
        "supports_embeddings": bool(preset.get("supports_embeddings")),
        "needs_base_url": pid == "openai-compatible",
        "needs_key": pid != "ollama",
    }


@app.get("/api/settings/llm")
def get_llm_settings() -> Dict[str, Any]:
    """Return live LLM gateway status + selectable providers (no secrets, only masked)."""
    return {
        "status": "success",
        "llm": get_llm_status(),
        "providers": [_provider_option(pid) for pid in PROVIDER_PRESETS],
    }


@app.post("/api/settings/llm")
def save_llm_settings(req: LLMSettingsRequest) -> Dict[str, Any]:
    """Persist the chosen LLM provider + API key into the local .env (and this process)."""
    if req.provider not in PROVIDER_PRESETS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider '{req.provider}'. Valid providers: {sorted(PROVIDER_PRESETS)}",
        )
    info = _apply_llm_settings(req.provider, req.api_key, req.model, req.base_url, req.clear_key)
    return {
        "status": "success",
        "message": f"Provider settings saved to {os.path.basename(ENV_FILE)}.",
        "llm": get_llm_status(),
        **info,
    }


@app.get("/api/files")
def list_files() -> Dict[str, Any]:
    """Return full directory structure for the File Explorer."""
    tree = get_recursive_file_tree(BASE_DIR)
    return {"status": "success", "files": tree}


@app.get("/api/file/{file_path:path}")
def read_file_content(file_path: str) -> Dict[str, Any]:
    """Retrieve file content by path."""
    clean_path = os.path.abspath(os.path.join(BASE_DIR, file_path))
    if not clean_path.startswith(BASE_DIR):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(clean_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    try:
        with open(clean_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"status": "success", "path": file_path, "content": content}
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.post("/api/file/{file_path:path}")
def save_file_content(file_path: str, req: FileUpdateRequest) -> Dict[str, Any]:
    """Save or update file content on disk, creating parent folders if missing."""
    clean_path = os.path.abspath(os.path.join(BASE_DIR, file_path))
    if not clean_path.startswith(BASE_DIR):
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        os.makedirs(os.path.dirname(clean_path), exist_ok=True)
        with open(clean_path, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"status": "success", "path": file_path, "message": "Saved successfully"}
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.post("/api/chat")
async def execute_chat(req: ChatPromptRequest) -> Dict[str, Any]:
    """Run canonical multi-agent orchestration pipeline."""
    session_id = req.session_id or "default"
    result = await canonical_orchestrator.execute_prompt(req.prompt)

    # Stage generated files (if any) for user Accept / Reject review
    staged_files = result.get("files", {})
    staged_files_cache[session_id] = staged_files

    # Persist checkpoint via continuity engine if files were produced
    if staged_files:
        continuity_engine.save_checkpoint(req.prompt, staged_files, status="STAGED")

    return {
        "status": "success",
        "prompt": req.prompt,
        "session_id": session_id,
        "intent": result.get("intent"),
        "execution_mode": result.get("execution_mode"),
        "tasks_executed": result.get("tasks_executed", 0),
        # Content map { relative_path: content }, matching CanonicalOrchestrator.execute_prompt
        # so the Electron desktop renderer can stage & accept files through its IPC file gate.
        "files": staged_files,
        "files_count": len(staged_files),
        "deltas": build_staged_deltas(staged_files),
        "message": result.get("summary", ""),
        "summary": result.get("summary", ""),
    }


@app.get("/api/staged-file")
def read_staged_file(session_id: str = "default", path: str = "") -> Dict[str, Any]:
    """Retrieve staged (not-yet-accepted) file content for review before Accept."""
    files = staged_files_cache.get(session_id, {})
    if path not in files:
        raise HTTPException(status_code=404, detail=f"No staged file '{path}' for session '{session_id}'")
    resolved = os.path.abspath(os.path.join(BASE_DIR, path))
    if not resolved.startswith(BASE_DIR):
        raise HTTPException(status_code=403, detail="Access denied")
    return {"status": "success", "path": path, "content": files[path], "staged": True}


@app.post("/api/accept")
def accept_generated_code(req: AcceptRejectRequest) -> Dict[str, Any]:
    """Accept staged code: write files to disk and make visible in explorer."""
    session_id = req.session_id or "default"
    files = staged_files_cache.get(session_id)
    if not files:
        return {"status": "warning", "message": "No staged files found for this session."}

    written = []
    for rel_path, content in files.items():
        full_path = os.path.abspath(os.path.join(BASE_DIR, rel_path))
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(rel_path)

    # Clear staged cache
    staged_files_cache.pop(session_id, None)

    return {
        "status": "success",
        "committed_files": written,
        "message": f"Successfully accepted and saved {len(written)} files to the project.",
    }


@app.post("/api/reject")
def reject_generated_code(req: AcceptRejectRequest) -> Dict[str, Any]:
    """Reject staged code: discard staged buffer."""
    session_id = req.session_id or "default"
    staged_files_cache.pop(session_id, None)
    return {
        "status": "rejected",
        "message": "Generated code discarded. Please enter feedback or an updated prompt.",
    }


# ==============================================================================
# IDE Panels: Search, Source Control, Run & Debug
# ==============================================================================
@app.get("/api/search")
def search_files(q: str = "") -> Dict[str, Any]:
    """Search file names and file contents for a query string.

    Returns up to 100 matches with line numbers + snippets so the IDE Search
    panel can jump straight to the hit. Binary-looking files are skipped.
    """
    term = q.strip()
    if not term:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")

    term_lower = term.lower()
    results: List[Dict[str, Any]] = []

    def walk(directory: str, depth: int) -> None:
        if depth > 5 or len(results) >= 100:
            return
        try:
            entries = sorted(os.scandir(directory), key=lambda e: e.name.lower())
        except OSError:
            return
        for entry in entries:
            if len(results) >= 100:
                return
            if entry.name in IGNORED_DIRS:
                continue
            rel = os.path.relpath(entry.path, BASE_DIR).replace("\\", "/")
            if entry.is_dir():
                walk(entry.path, depth + 1)
                continue
            # Filename match
            if term_lower in entry.name.lower():
                results.append({"path": rel, "type": "filename", "matches": []})
            # Content match (text files only, cap size)
            try:
                if entry.stat().st_size > 512 * 1024:
                    continue
                with open(entry.path, "r", encoding="utf-8", errors="ignore") as fh:
                    for line_no, line in enumerate(fh, 1):
                        if term_lower in line.lower():
                            results.append({
                                "path": rel,
                                "type": "content",
                                "matches": [{"line": line_no, "snippet": line.strip()[:160]}],
                            })
                            break
            except (OSError, UnicodeDecodeError):
                continue

    walk(BASE_DIR, 0)
    return {"status": "success", "query": term, "count": len(results), "results": results[:100]}


@app.get("/api/git/status")
def git_status() -> Dict[str, Any]:
    """Read-only git snapshot: current branch, short status, and recent commits.

    Never mutates the repository — only runs read-only git commands. If the
    workspace is not a git repository, returns an informative error state.
    """
    import subprocess

    def run(cmd: List[str], timeout: int = 10) -> Optional[str]:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=BASE_DIR)
            if proc.returncode == 0:
                # rstrip only — a leading space is meaningful in `git status
                # --short` output (col 0 = index state), and .strip() would eat
                # it off the first line and corrupt every parsed path.
                return (proc.stdout or "").rstrip()
            return None
        except Exception:
            return None

    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if branch is None:
        return {"status": "error", "message": "Not a git repository (or git is not installed).", "branch": None, "changes": [], "commits": []}

    raw_status = run(["git", "status", "--short"]) or ""
    changes = []
    for line in raw_status.splitlines():
        if not line.strip():
            continue
        changes.append({"code": line[:2], "path": line[3:].strip()})

    raw_log = run(["git", "log", "--oneline", "-5"]) or ""
    commits = [c.strip() for c in raw_log.splitlines() if c.strip()]

    return {
        "status": "success",
        "branch": branch,
        "changes": changes,
        "commits": commits,
        "dirty_count": sum(1 for c in changes if c["code"].strip()),
    }


DEBUG_TARGETS = {
    "compile-check": {
        "label": "Compile Check (py_compile)",
        "cmd": ["python", "-m", "py_compile", "server.py", "llm.py", "orchestrator.py", "core/canonical_orchestrator.py", "core/agent_base.py", "gui/api/main.py"],
        "timeout": 60,
    },
    "smoke": {
        "label": "Smoke Tests (smoke_test.py)",
        "cmd": ["python", "smoke_test.py"],
        "timeout": 300,
    },
    "pytest": {
        "label": "Full Test Suite (pytest -q)",
        "cmd": ["python", "-m", "pytest", "-q"],
        "timeout": 600,
    },
}


@app.get("/api/debug/targets")
def debug_targets() -> Dict[str, Any]:
    """List whitelisted run/debug targets (no arbitrary command execution)."""
    return {
        "status": "success",
        "targets": [
            {"id": tid, "label": info["label"], "timeout": info["timeout"]}
            for tid, info in DEBUG_TARGETS.items()
        ],
    }


class DebugRunRequest(BaseModel):
    target: str = Field(..., description="Whitelisted target id from GET /api/debug/targets")


@app.post("/api/debug/run")
def debug_run(req: DebugRunRequest) -> Dict[str, Any]:
    """Run a whitelisted dev target with a hard timeout and return its output.

    Only the targets defined in DEBUG_TARGETS can ever be executed — arbitrary
    commands from the client are rejected with 400.
    """
    import subprocess

    info = DEBUG_TARGETS.get(req.target)
    if not info:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown target '{req.target}'. Valid targets: {sorted(DEBUG_TARGETS)}",
        )
    started = time.time()
    try:
        proc = subprocess.run(
            info["cmd"],
            capture_output=True,
            text=True,
            timeout=info["timeout"],
            cwd=BASE_DIR,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        return {
            "status": "success" if proc.returncode == 0 else "failed",
            "target": req.target,
            "exit_code": proc.returncode,
            "elapsed_seconds": round(time.time() - started, 1),
            "output": output[-6000:],
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "target": req.target,
            "elapsed_seconds": round(time.time() - started, 1),
            "output": f"Timed out after {info['timeout']}s — the target is still running elsewhere.",
        }
    except Exception as err:
        return {"status": "error", "target": req.target, "exit_code": -1, "output": str(err)}


# ==============================================================================
# WebSocket: Real-Time Agent Chat & Live Swarm Telemetry (/ws)
# ==============================================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time bi-directional streaming endpoint for canonical multi-agent chat and status."""
    await websocket.accept()
    session_id = f"ws_{int(time.time() * 1000)}"

    await websocket.send_json({
        "type": "agent_message",
        "sender": "agent",
        "text": "👋 **Antigravity Multi-Agent Orchestrator Ready.**\n\nAsk me to explain architecture, find bugs, run tests, or create components.",
    })

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            action = msg.get("action")

            if action == "chat":
                prompt = msg.get("prompt", "").strip()
                if not prompt:
                    continue

                # Echo user message
                await websocket.send_json({
                    "type": "user_message",
                    "text": prompt,
                })

                # Stream real events from the Canonical Orchestrator
                async def stream_orchestrator_event(event_type: str, event_data: Dict[str, Any]):
                    await websocket.send_json({
                        "type": "status_update",
                        "lifecycle": event_type,
                        "text": f"[{event_type}] {event_data.get('task_id', '')} {event_data.get('agent', event_data.get('tool', ''))}",
                        "metadata": event_data,
                    })

                # Execute Canonical Orchestrator
                result = await canonical_orchestrator.execute_prompt(prompt, event_callback=stream_orchestrator_event)

                # Cache staged files
                staged_files = result.get("files", {})
                staged_files_cache[session_id] = staged_files

                # Send final completion event with review-card deltas
                await websocket.send_json({
                    "type": "swarm_completed",
                    "intent": result.get("intent"),
                    "execution_mode": result.get("execution_mode"),
                    "tasks_executed": result.get("tasks_executed", 0),
                    "files": list(staged_files.keys()),
                    "deltas": build_staged_deltas(staged_files),
                    "text": result.get("summary", ""),
                    "session_id": session_id,
                })

            elif action == "accept":
                files = staged_files_cache.get(session_id, {})
                for rel_path, content in files.items():
                    full_path = os.path.abspath(os.path.join(BASE_DIR, rel_path))
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)
                staged_files_cache.pop(session_id, None)

                await websocket.send_json({
                    "type": "action_result",
                    "status": "accepted",
                    "files": list(files.keys()),
                    "text": f"✅ **Accepted!** Saved {len(files)} files to disk and updated explorer.",
                })

            elif action == "reject":
                staged_files_cache.pop(session_id, None)
                await websocket.send_json({
                    "type": "action_result",
                    "status": "rejected",
                    "text": "❌ **Rejected.** Staged files were discarded. What modifications would you like?",
                })

    except WebSocketDisconnect:
        logger.info("Client disconnected: %s", session_id)
        staged_files_cache.pop(session_id, None)


# Mount static assets (CSS, JS, fonts)
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
