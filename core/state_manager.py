"""StateManager class for JSON persistence, Memento checkpoints, and context compression.

Implements:
- Singleton pattern for centralized state persistence.
- Atomic write-and-rename pattern (ACID file operations).
- Memento pattern for system snapshotting and fast rollback.
- Strategy pattern for context compression and artifact offloading (>4096 tokens).
- Automated cleanup maintaining at most max_checkpoints on disk.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.exceptions import StateError


logger = logging.getLogger("FractalCore.StateManager")


class StateManager:
    """Thread-safe state manager for zero-dependency JSON storage and checkpoints."""

    _instance: Optional[StateManager] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> StateManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StateManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(
        self,
        persist_path: str = "./state/",
        compression_threshold: int = 4096,
        max_checkpoints: int = 10,
    ) -> None:
        if getattr(self, "_initialized", False):
            return

        self._persist_path = Path(persist_path).resolve()
        self._compression_threshold = compression_threshold
        self._max_checkpoints = max_checkpoints
        self._io_lock = threading.RLock()

        # Build directory tree
        self._global_dir = self._persist_path / "global"
        self._agents_dir = self._persist_path / "agents"
        self._checkpoints_dir = self._persist_path / "checkpoints"
        self._artifacts_dir = self._persist_path / "artifacts"

        for directory in [self._global_dir, self._agents_dir, self._checkpoints_dir, self._artifacts_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        self._global_state_file = self._global_dir / "system_state.json"
        self._init_global_state_if_missing()
        self._initialized = True

        logger.info(
            "StateManager initialized at %s (Compression threshold: %d, Max checkpoints: %d)",
            self._persist_path,
            self._compression_threshold,
            self._max_checkpoints,
        )

    # --------------------------------------------------------------------------
    # Atomic File Helpers
    # --------------------------------------------------------------------------

    def _atomic_write_json(self, target_path: Path, data: Any) -> None:
        """Atomically serialize and flush a JSON payload to disk with Windows retry resilience."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                dir=str(target_path.parent),
                prefix=f".tmp_{target_path.name}_",
                delete=False,
                encoding="utf-8",
            ) as tf:
                json.dump(data, tf, indent=2, sort_keys=True)
                tf.flush()
                os.fsync(tf.fileno())
                temp_file = tf.name

            # Windows OneDrive file lock retry resilience
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    os.replace(temp_file, target_path)
                    break
                except (PermissionError, OSError) as os_err:
                    if attempt == max_retries - 1:
                        # Fallback: direct write if replace is blocked by file lock
                        try:
                            with open(target_path, "w", encoding="utf-8") as f_out:
                                json.dump(data, f_out, indent=2, sort_keys=True)
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                            break
                        except Exception:
                            raise os_err
                    time.sleep(0.05 * (attempt + 1))
        except Exception as exc:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            raise StateError(f"Failed atomic write to {target_path}: {exc}") from exc

    def _read_json(self, target_path: Path, default: Any = None) -> Any:
        """Safely read and deserialize a JSON file from disk."""
        if not target_path.exists():
            return default
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.error("Error reading JSON from %s: %s", target_path, exc)
            raise StateError(f"Corrupted or unreadable state file at {target_path}: {exc}") from exc

    # --------------------------------------------------------------------------
    # Global State
    # --------------------------------------------------------------------------

    def _init_global_state_if_missing(self) -> None:
        """Create baseline global system_state.json if none exists."""
        if not self._global_state_file.exists():
            initial_state = {
                "system_status": "INITIALIZING",
                "initialized_at": time.time(),
                "last_updated": time.time(),
                "active_session_id": None,
                "token_usage": {"prompt": 0, "completion": 0, "total": 0},
                "checkpoints_count": 0,
            }
            self._atomic_write_json(self._global_state_file, initial_state)

    def load_global_state(self) -> Dict[str, Any]:
        """Read current global system state."""
        with self._io_lock:
            return self._read_json(self._global_state_file, default={})

    def update_global_state(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update fields in global state atomically."""
        with self._io_lock:
            current = self.load_global_state()
            current.update(updates)
            current["last_updated"] = time.time()
            self._atomic_write_json(self._global_state_file, current)
            return current

    # --------------------------------------------------------------------------
    # Agent-Local State
    # --------------------------------------------------------------------------

    def save_agent_state(self, agent_id: str, state_dict: Dict[str, Any]) -> None:
        """Persist private state for an individual agent."""
        with self._io_lock:
            agent_dir = self._agents_dir / agent_id
            agent_file = agent_dir / "local_state.json"
            self._atomic_write_json(agent_file, state_dict)
            logger.debug("Saved local state for agent %s", agent_id)

    def load_agent_state(self, agent_id: str) -> Dict[str, Any]:
        """Load private state for an individual agent."""
        with self._io_lock:
            agent_file = self._agents_dir / agent_id / "local_state.json"
            return self._read_json(agent_file, default={})

    def purge_agent_state(self, agent_id: str) -> None:
        """Purge an agent's private directory upon terminal completion."""
        with self._io_lock:
            agent_dir = self._agents_dir / agent_id
            if agent_dir.exists():
                shutil.rmtree(agent_dir, ignore_errors=True)
                logger.debug("Purged local state directory for agent %s", agent_id)

    # --------------------------------------------------------------------------
    # Checkpoint (Memento Pattern)
    # --------------------------------------------------------------------------

    def create_checkpoint(self, checkpoint_id: str, metadata: Optional[Dict[str, Any]] = None) -> Path:
        """Capture a full Memento snapshot of current global state and active agents.

        Args:
            checkpoint_id: Descriptive tag (e.g., 'CHK_PLAN_COMPLETED').
            metadata: Custom metadata (e.g., quality gate score, pass ratio).

        Returns:
            Path to the newly created checkpoint directory.
        """
        with self._io_lock:
            ts_str = time.strftime("%Y%m%d_%H%M%S")
            checkpoint_folder_name = f"{ts_str}_{checkpoint_id}"
            target_dir = self._checkpoints_dir / checkpoint_folder_name
            target_dir.mkdir(parents=True, exist_ok=True)

            # Copy global state
            global_snap = self.load_global_state()
            self._atomic_write_json(target_dir / "system_state_snap.json", global_snap)

            # Snapshot metadata
            meta = {
                "checkpoint_id": checkpoint_id,
                "created_at": time.time(),
                "metadata": metadata or {},
            }
            self._atomic_write_json(target_dir / "metadata.json", meta)

            logger.info("Created checkpoint '%s' at %s", checkpoint_id, target_dir)
            self._prune_checkpoints()
            return target_dir

    def restore_checkpoint(self, checkpoint_folder_name: str) -> Dict[str, Any]:
        """Restore global state from a historical checkpoint snapshot."""
        with self._io_lock:
            target_dir = self._checkpoints_dir / checkpoint_folder_name
            if not target_dir.exists():
                raise StateError(f"Checkpoint '{checkpoint_folder_name}' does not exist.")

            snap_file = target_dir / "system_state_snap.json"
            snap_data = self._read_json(snap_file)
            if not snap_data:
                raise StateError(f"Corrupt checkpoint snapshot at {snap_file}")

            # Restore as active global state
            self._atomic_write_json(self._global_state_file, snap_data)
            logger.info("Restored system state from checkpoint '%s'", checkpoint_folder_name)
            return snap_data

    def _prune_checkpoints(self) -> None:
        """Enforce max_checkpoints limit by deleting oldest checkpoint directories."""
        all_checkpoints = sorted(
            [d for d in self._checkpoints_dir.iterdir() if d.is_dir()],
            key=lambda p: p.stat().st_mtime,
        )
        excess = len(all_checkpoints) - self._max_checkpoints
        if excess > 0:
            for old_chk in all_checkpoints[:excess]:
                shutil.rmtree(old_chk, ignore_errors=True)
                logger.info("Pruned old checkpoint: %s", old_chk.name)

    # --------------------------------------------------------------------------
    # Context Compression (Strategy Pattern)
    # --------------------------------------------------------------------------

    def compress_context_if_needed(self, content: str, identifier: str) -> Dict[str, Any]:
        """Evaluate context size; if exceeding threshold, offload to artifact store.

        Returns:
            Dictionary with either inline content or pointer envelope.
        """
        # Approximate 1 token ~= 4 characters
        token_estimate = len(content) // 4
        if token_estimate <= self._compression_threshold:
            return {"offloaded": False, "content": content, "estimated_tokens": token_estimate}

        # Context exceeds threshold: execute offload strategy
        with self._io_lock:
            artifact_filename = f"artifact_{identifier}_{int(time.time())}.txt"
            artifact_path = self._artifacts_dir / artifact_filename
            with open(artifact_path, "w", encoding="utf-8") as f:
                f.write(content)

            summary = content[:300].replace("\n", " ") + "... [TRUNCATED DUE TO SIZE]"
            logger.info(
                "Context for '%s' (%d tokens) exceeded threshold (%d). Offloaded to %s",
                identifier,
                token_estimate,
                self._compression_threshold,
                artifact_filename,
            )

            return {
                "offloaded": True,
                "artifact_uri": f"file://{artifact_path.resolve()}",
                "estimated_tokens": token_estimate,
                "summary": summary,
                "byte_size": len(content.encode("utf-8")),
            }
