"""CheckpointManager agent managing system snapshots, rollbacks, and retention pruning."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from agents.commstate.exceptions import CheckpointError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.CommState.CheckpointManager")


# ==============================================================================
# L5 Atomic Checkpoint Subagents
# ==============================================================================

class CheckpointCreator(BaseAgent):
    """L5 agent capturing consistent snapshots of global system, task, and agent state."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CheckpointCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        label = payload.get("label", "AUTO_CHECKPOINT")
        state_data = payload.get("state_data", {})
        chk_id = f"chk_{uuid.uuid4().hex[:10]}"

        record = {
            "checkpoint_id": chk_id,
            "label": label,
            "timestamp": time.time(),
            "state_data": state_data,
            "valid": True,
        }
        return {"status": "COMPLETED", "checkpoint": record}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "checkpoint" not in result:
            raise CheckpointError("CheckpointCreator produced invalid record.")
        return result

    def cleanup(self) -> None:
        logger.debug("CheckpointCreator %s cleaned up.", self.agent_id)


class CheckpointRestorer(BaseAgent):
    """L5 agent deserializing and validating state snapshots for rollbacks."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CheckpointRestorer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        chk_store = payload.get("checkpoint_store", {})
        chk_id = payload.get("checkpoint_id")

        matched = chk_store.get(chk_id) if chk_id else None
        return {
            "status": "COMPLETED",
            "restored_state": matched.get("state_data") if matched else None,
            "success": matched is not None,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CheckpointRestorer %s cleaned up.", self.agent_id)


class CheckpointList(BaseAgent):
    """L5 agent indexing available snapshots with metadata and timestamps."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CheckpointList %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        chk_store = payload.get("checkpoint_store", {})

        summary = [
            {
                "checkpoint_id": c.get("checkpoint_id"),
                "label": c.get("label"),
                "timestamp": c.get("timestamp"),
            }
            for c in chk_store.values()
        ]
        return {"status": "COMPLETED", "checkpoints": summary, "count": len(summary)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CheckpointList %s cleaned up.", self.agent_id)


class CheckpointCleaner(BaseAgent):
    """L5 agent enforcing snapshot retention ceilings by pruning oldest checkpoints."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CheckpointCleaner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        chk_store = dict(payload.get("checkpoint_store", {}))
        max_retained = payload.get("max_checkpoints", 10)

        pruned = 0
        if len(chk_store) > max_retained:
            sorted_keys = sorted(chk_store.keys(), key=lambda k: chk_store[k].get("timestamp", 0))
            to_remove = sorted_keys[: len(chk_store) - max_retained]
            for k in to_remove:
                del chk_store[k]
                pruned += 1

        return {"status": "COMPLETED", "checkpoint_store": chk_store, "pruned": pruned}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CheckpointCleaner %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 CheckpointManager Agent
# ==============================================================================

class CheckpointManager(BaseAgent):
    """L4 coordinator overseeing system checkpoint snapshots, restore points, and pruning."""

    def __init__(
        self,
        name: str = "CheckpointManager",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "checkpoint_management",
            "snapshot_creation",
            "rollback_restoration",
            "checkpoint_pruning",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C10_CHECKPOINT_MANAGER",
        )

        self._checkpoints: Dict[str, Dict[str, Any]] = {}
        self.creator: Optional[CheckpointCreator] = None
        self.restorer: Optional[CheckpointRestorer] = None
        self.lister: Optional[CheckpointList] = None
        self.cleaner: Optional[CheckpointCleaner] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("create_checkpoint", self.create_checkpoint)
        self.register_tool("restore_checkpoint", self.restore_checkpoint)
        self.register_tool("list_checkpoints", self.list_checkpoints)

    def _spawn_subagents(self) -> None:
        """Spawn atomic checkpoint subagents (Rule 1 & Rule 5)."""
        logger.info("CheckpointManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.creator = self.spawn_subagent(
            CheckpointCreator,
            name="CheckpointCreator",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.restorer = self.spawn_subagent(
            CheckpointRestorer,
            name="CheckpointRestorer",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.lister = self.spawn_subagent(
            CheckpointList,
            name="CheckpointList",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.cleaner = self.spawn_subagent(
            CheckpointCleaner,
            name="CheckpointCleaner",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CheckpointManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        chk = self.create_checkpoint(
            label=payload.get("label", "MANUAL"),
            state_data=payload.get("state_data", {}),
        )
        return {"status": "COMPLETED", "checkpoint": chk}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CheckpointManager %s cleanup complete.", self.agent_id)

    def create_checkpoint(self, label: str, state_data: Any) -> Dict[str, Any]:
        """Capture new state snapshot and enforce retention limit."""
        p_env = {"payload": {"label": label, "state_data": state_data}}
        res = self.creator.process(p_env) if self.creator else {"checkpoint": {"checkpoint_id": "chk_fb", "label": label}}
        chk = res["checkpoint"]
        self._checkpoints[chk["checkpoint_id"]] = chk

        if self.cleaner:
            c_env = {"payload": {"checkpoint_store": self._checkpoints, "max_checkpoints": 10}}
            c_res = self.cleaner.process(c_env)
            self._checkpoints = c_res.get("checkpoint_store", self._checkpoints)

        return chk

    def restore_checkpoint(self, checkpoint_id: str) -> Optional[Any]:
        """Retrieve state data from snapshot."""
        p_env = {"payload": {"checkpoint_store": self._checkpoints, "checkpoint_id": checkpoint_id}}
        res = self.restorer.process(p_env) if self.restorer else {"restored_state": None}
        return res.get("restored_state")

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List metadata for all stored snapshots."""
        p_env = {"payload": {"checkpoint_store": self._checkpoints}}
        res = self.lister.process(p_env) if self.lister else {"checkpoints": []}
        return res.get("checkpoints", [])
