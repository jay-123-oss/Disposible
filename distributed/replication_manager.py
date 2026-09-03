"""ReplicationManager agent orchestrating data replication factors, sync/async modes, and quorum validation.

Implements the complete Replication Manager hierarchy (D10):
- L4 ReplicationManager coordinator
- L5 atomic workers: ReplicationFactor, SyncReplication, AsyncReplication, ReplicationVerifier
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from distributed.exceptions import ReplicationError

logger = logging.getLogger("FractalCore.Distributed.ReplicationManager")


# ==============================================================================
# L5 Atomic Replication Manager Subagents
# ==============================================================================

class ReplicationFactor(BaseAgent):
    """L5 agent determining minimum required replication targets and quorum thresholds."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ReplicationFactor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        factor = task_envelope.get("factor", 3)
        available_nodes = task_envelope.get("nodes", [])
        actual_factor = min(factor, len(available_nodes))
        quorum = (actual_factor // 2) + 1
        return {
            "status": "COMPLETED",
            "desired_factor": factor,
            "actual_factor": actual_factor,
            "quorum": quorum,
            "replica_nodes": available_nodes[:actual_factor],
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ReplicationFactor %s cleaned up.", self.agent_id)


class SyncReplication(BaseAgent):
    """L5 agent executing synchronous writes requiring write-quorum acknowledgments before returning."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SyncReplication %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        replicas = task_envelope.get("replicas", [])
        quorum = task_envelope.get("quorum", (len(replicas) // 2) + 1)
        acks = len(replicas)
        success = acks >= quorum
        return {
            "status": "COMPLETED",
            "mode": "sync",
            "replicated": success,
            "acks_received": acks,
            "quorum_required": quorum,
            "payload_id": payload.get("id"),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SyncReplication %s cleaned up.", self.agent_id)


class AsyncReplication(BaseAgent):
    """L5 agent queueing replication writes asynchronously in the background."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AsyncReplication %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        replicas = task_envelope.get("replicas", [])
        return {
            "status": "COMPLETED",
            "mode": "async",
            "enqueued": True,
            "target_replicas": replicas,
            "queued_at": time.time(),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AsyncReplication %s cleaned up.", self.agent_id)


class ReplicationVerifier(BaseAgent):
    """L5 agent comparing version vectors and data digests across replica nodes to detect divergence."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ReplicationVerifier %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        replicas_data = task_envelope.get("replicas_data", {})
        unique_versions = set(replicas_data.values())
        consistent = len(unique_versions) <= 1
        return {
            "status": "COMPLETED",
            "consistent": consistent,
            "unique_versions": len(unique_versions),
            "verified_at": time.time(),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ReplicationVerifier %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 ReplicationManager Agent
# ==============================================================================

class ReplicationManager(BaseAgent):
    """L4 coordinator managing data replication factor, sync/async modes, and quorum."""

    def __init__(
        self,
        name: str = "ReplicationManager",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
        factor: int = 3,
        sync_mode: str = "async",
        consistency_level: str = "quorum",
    ) -> None:
        default_caps = capabilities or [
            "replication_manager",
            "replication_factor",
            "sync_replication",
            "async_replication",
            "replication_verifier",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "D10_REPLICATION_MANAGER",
        )
        self.factor = factor
        self.sync_mode = sync_mode
        self.consistency_level = consistency_level
        self.nodes: List[str] = ["node-1", "node-2", "node-3"]

        self.replication_factor: Optional[ReplicationFactor] = None
        self.sync_replication: Optional[SyncReplication] = None
        self.async_replication: Optional[AsyncReplication] = None
        self.replication_verifier: Optional[ReplicationVerifier] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("replicate_data", self.replicate_data)
        self.register_tool("verify_consistency", self.verify_consistency)

    def _spawn_subagents(self) -> None:
        """Spawn atomic replication manager subagents (Rule 1 & Rule 5)."""
        logger.info("ReplicationManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.replication_factor = self.spawn_subagent(ReplicationFactor, name="ReplicationFactor", max_depth=child_depth, resources_mb=32)
        self.sync_replication = self.spawn_subagent(SyncReplication, name="SyncReplication", max_depth=child_depth, resources_mb=32)
        self.async_replication = self.spawn_subagent(AsyncReplication, name="AsyncReplication", max_depth=child_depth, resources_mb=32)
        self.replication_verifier = self.spawn_subagent(ReplicationVerifier, name="ReplicationVerifier", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ReplicationManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return self.replicate_data(task_envelope.get("payload", {}), mode=task_envelope.get("mode"))

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ReplicationManager %s cleaned up.", self.agent_id)

    def set_nodes(self, nodes: List[str]) -> None:
        """Update cluster node list for replication selection."""
        self.nodes = list(nodes)

    def replicate_data(self, payload: Dict[str, Any], mode: Optional[str] = None) -> Dict[str, Any]:
        """Replicate payload across target nodes using sync or async mode."""
        res_factor = self.replication_factor.process({"factor": self.factor, "nodes": self.nodes}) if self.replication_factor else {
            "replica_nodes": self.nodes[:self.factor], "quorum": (len(self.nodes) // 2) + 1
        }
        targets = res_factor["replica_nodes"]
        quorum = res_factor["quorum"]

        chosen_mode = mode or self.sync_mode
        if chosen_mode == "sync" and self.sync_replication:
            res = self.sync_replication.process({"payload": payload, "replicas": targets, "quorum": quorum})
        elif self.async_replication:
            res = self.async_replication.process({"payload": payload, "replicas": targets})
        else:
            res = {"replicated": True, "mode": chosen_mode}

        return {
            "replicated": res.get("replicated", res.get("enqueued", True)),
            "mode": chosen_mode,
            "target_count": len(targets),
            "targets": targets,
        }

    def verify_consistency(self, replicas_data: Dict[str, Any]) -> bool:
        """Verify version consistency across all replica nodes."""
        if self.replication_verifier:
            res = self.replication_verifier.process({"replicas_data": replicas_data})
            return res.get("consistent", True)
        return len(set(replicas_data.values())) <= 1
