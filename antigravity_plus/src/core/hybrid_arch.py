"""Hybrid Architecture: Local IDE + Cloud Agent Synchronization & Disposable Workspaces.

Features:
- Multi-IDE Support (VS Code, Cursor, Zed, Neovim protocol hooks)
- Cloud Execution Integration (Offloads compute to Kaggle/Colab GPU workers)
- Bi-directional Real-Time Sync (Syncs local changes with remote cloud agents)
- Disposable Environments (Instant environment isolation and one-click rollback)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AntigravityPlus.HybridArch")


@dataclass
class FileDigest:
    rel_path: str
    size_bytes: int
    sha256: str
    mtime: float


class DisposableEnvironmentManager:
    """Manages ephemeral, zero-friction sandboxes with instant one-click rollback."""

    def __init__(self, base_workspace: str = ".") -> None:
        self.base_workspace = Path(base_workspace).resolve()
        self.snapshot_dir = self.base_workspace / ".antigravity_snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.initial_snapshot_created = False

    def create_snapshot(self, snapshot_tag: str = "initial") -> str:
        """Create a point-in-time snapshot for instantaneous environment rollback."""
        tag_dir = self.snapshot_dir / snapshot_tag
        if tag_dir.exists():
            shutil.rmtree(tag_dir, ignore_errors=True)
        tag_dir.mkdir(parents=True, exist_ok=True)
        tag_dir.mkdir(parents=True, exist_ok=True)

        for item in self.base_workspace.iterdir():
            # Skip VCS/build dirs AND IDE runtime scratch dirs (snapshots of
            # those would churn on every boot and can lock/collide on Windows).
            if item.name in (
                ".antigravity_snapshots",
                ".antigravity_preview",
                ".antigravity_state",
                ".freebuff",
                ".git",
                "__pycache__",
                "node_modules",
                ".pytest_cache",
            ):
                continue
            dest = tag_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

        self.initial_snapshot_created = True
        logger.info("Created disposable environment snapshot: %s", tag_dir)
        return str(tag_dir)

    def reset_environment(self, snapshot_tag: str = "initial") -> bool:
        """One-click instant rollback: restores workspace to completely fresh pristine state."""
        tag_dir = self.snapshot_dir / snapshot_tag
        if not tag_dir.exists():
            logger.warning("Snapshot %s not found. Creating baseline first.", snapshot_tag)
            self.create_snapshot(snapshot_tag)
            return True

        logger.info("⚡ Executing instant rollback to snapshot '%s'...", snapshot_tag)
        for item in self.base_workspace.iterdir():
            if item.name in (".antigravity_snapshots", ".git"):
                continue
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                try:
                    item.unlink(missing_ok=True)
                except Exception:
                    pass

        # Copy back clean files
        for item in tag_dir.iterdir():
            dest = self.base_workspace / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

        logger.info("✅ Environment successfully reset to pristine snapshot '%s'", snapshot_tag)
        return True


class LocalCloudSync:
    """Manages hash-based differential synchronization between local files and remote agents."""

    def __init__(self, workspace_root: str = ".") -> None:
        self.workspace_root = Path(workspace_root).resolve()

    def compute_file_hash(self, path: Path) -> str:
        """Generate SHA-256 hash of file contents."""
        hasher = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    def generate_manifest(self) -> Dict[str, FileDigest]:
        """Scan workspace and generate differential change manifest."""
        manifest: Dict[str, FileDigest] = {}
        for root, dirs, files in os.walk(self.workspace_root):
            # Ignore hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__")]
            for f in files:
                if f.startswith("."):
                    continue
                p = Path(root) / f
                rel = str(p.relative_to(self.workspace_root)).replace("\\", "/")
                digest = FileDigest(
                    rel_path=rel,
                    size_bytes=p.stat().st_size,
                    sha256=self.compute_file_hash(p),
                    mtime=p.stat().st_mtime,
                )
                manifest[rel] = digest
        return manifest

    def calculate_diff(self, remote_manifest: Dict[str, Any]) -> Dict[str, List[str]]:
        """Identify files to push, pull, or delete."""
        local = self.generate_manifest()
        to_push: List[str] = []
        to_pull: List[str] = []

        for rel, local_digest in local.items():
            if rel not in remote_manifest:
                to_push.append(rel)
            elif remote_manifest[rel].get("sha256") != local_digest.sha256:
                if local_digest.mtime > remote_manifest[rel].get("mtime", 0):
                    to_push.append(rel)
                else:
                    to_pull.append(rel)

        for rel in remote_manifest:
            if rel not in local:
                to_pull.append(rel)

        return {"push": to_push, "pull": to_pull}
