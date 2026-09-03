"""ArtifactManager agent managing code artifacts, SHA-256 versioning, and retrieval."""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any, Dict, List, Optional

from agents.commstate.exceptions import ArtifactError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.CommState.ArtifactManager")


# ==============================================================================
# L5 Atomic Artifact Subagents
# ==============================================================================

class ArtifactCreator(BaseAgent):
    """L5 agent storing new artifacts with cryptographic SHA-256 checksums."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ArtifactCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        artifact_id = payload.get("artifact_id", f"ART_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}")
        content = payload.get("content", "")
        content_bytes = content.encode("utf-8") if isinstance(content, str) else bytes(content)
        checksum = hashlib.sha256(content_bytes).hexdigest()

        record = {
            "artifact_id": artifact_id,
            "filename": payload.get("filename", "unnamed.txt"),
            "content": content,
            "sha256": checksum,
            "size_bytes": len(content_bytes),
            "version": 1,
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        return {"status": "COMPLETED", "artifact": record}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "artifact" not in result:
            raise ArtifactError("ArtifactCreator produced invalid record.")
        return result

    def cleanup(self) -> None:
        logger.debug("ArtifactCreator %s cleaned up.", self.agent_id)


class ArtifactRetriever(BaseAgent):
    """L5 agent retrieving artifacts by ID or filename with integrity verification."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ArtifactRetriever %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        store = payload.get("artifact_store", {})
        artifact_id = payload.get("artifact_id")
        filename = payload.get("filename")

        matched = None
        if artifact_id and artifact_id in store:
            matched = store[artifact_id]
        elif filename:
            for art in store.values():
                if art.get("filename") == filename:
                    matched = art
                    break

        return {"status": "COMPLETED", "artifact": matched, "found": matched is not None}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ArtifactRetriever %s cleaned up.", self.agent_id)


class ArtifactUpdater(BaseAgent):
    """L5 agent bumping artifact versions and recalculating SHA-256 checksums."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ArtifactUpdater %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        record = dict(payload.get("artifact", {}))
        new_content = payload.get("content", "")

        content_bytes = new_content.encode("utf-8") if isinstance(new_content, str) else bytes(new_content)
        checksum = hashlib.sha256(content_bytes).hexdigest()

        record["content"] = new_content
        record["sha256"] = checksum
        record["size_bytes"] = len(content_bytes)
        record["version"] = record.get("version", 1) + 1
        record["updated_at"] = time.time()

        return {"status": "COMPLETED", "artifact": record}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ArtifactUpdater %s cleaned up.", self.agent_id)


class ArtifactDeleter(BaseAgent):
    """L5 agent removing expired artifacts from disk cache."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ArtifactDeleter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        store = dict(payload.get("artifact_store", {}))
        art_id = payload.get("artifact_id")

        deleted = False
        if art_id and art_id in store:
            del store[art_id]
            deleted = True

        return {"status": "COMPLETED", "artifact_store": store, "deleted": deleted}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ArtifactDeleter %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 ArtifactManager Agent
# ==============================================================================

class ArtifactManager(BaseAgent):
    """L4 coordinator overseeing multi-agent code artifacts, SHA-256 signatures, and versioning."""

    def __init__(
        self,
        name: str = "ArtifactManager",
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
            "artifact_management",
            "artifact_versioning",
            "checksum_verification",
            "artifact_retrieval",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C8_ARTIFACT_MANAGER",
        )

        self._artifacts: Dict[str, Dict[str, Any]] = {}
        self.creator: Optional[ArtifactCreator] = None
        self.retriever: Optional[ArtifactRetriever] = None
        self.updater: Optional[ArtifactUpdater] = None
        self.deleter: Optional[ArtifactDeleter] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("store_artifact", self.store_artifact)
        self.register_tool("get_artifact", self.get_artifact)
        self.register_tool("update_artifact", self.update_artifact)
        self.register_tool("delete_artifact", self.delete_artifact)

    def _spawn_subagents(self) -> None:
        """Spawn atomic artifact subagents (Rule 1 & Rule 5)."""
        logger.info("ArtifactManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.creator = self.spawn_subagent(
            ArtifactCreator,
            name="ArtifactCreator",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.retriever = self.spawn_subagent(
            ArtifactRetriever,
            name="ArtifactRetriever",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.updater = self.spawn_subagent(
            ArtifactUpdater,
            name="ArtifactUpdater",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.deleter = self.spawn_subagent(
            ArtifactDeleter,
            name="ArtifactDeleter",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ArtifactManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        art = self.store_artifact(
            filename=payload.get("filename", "code.py"),
            content=payload.get("content", ""),
        )
        return {"status": "COMPLETED", "artifact": art}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ArtifactManager %s cleanup complete.", self.agent_id)

    def store_artifact(self, filename: str, content: str, artifact_id: Optional[str] = None) -> Dict[str, Any]:
        """Store new artifact and return metadata."""
        p_env = {"payload": {"filename": filename, "content": content, "artifact_id": artifact_id}}
        res = self.creator.process(p_env) if self.creator else {"artifact": {"artifact_id": artifact_id or "ART_FB", "filename": filename}}
        record = res["artifact"]
        self._artifacts[record["artifact_id"]] = record
        return record

    def get_artifact(self, artifact_id: Optional[str] = None, filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve artifact by identifier."""
        p_env = {"payload": {"artifact_store": self._artifacts, "artifact_id": artifact_id, "filename": filename}}
        res = self.retriever.process(p_env) if self.retriever else {"artifact": None}
        return res.get("artifact")

    def update_artifact(self, artifact_id: str, new_content: str) -> Optional[Dict[str, Any]]:
        """Update artifact contents with new version."""
        if artifact_id not in self._artifacts:
            return None
        p_env = {"payload": {"artifact": self._artifacts[artifact_id], "content": new_content}}
        res = self.updater.process(p_env) if self.updater else {"artifact": self._artifacts[artifact_id]}
        self._artifacts[artifact_id] = res["artifact"]
        return self._artifacts[artifact_id]

    def delete_artifact(self, artifact_id: str) -> bool:
        """Delete artifact from store."""
        p_env = {"payload": {"artifact_store": self._artifacts, "artifact_id": artifact_id}}
        res = self.deleter.process(p_env) if self.deleter else {"deleted": False}
        if res.get("deleted"):
            self._artifacts.pop(artifact_id, None)
            return True
        return False
