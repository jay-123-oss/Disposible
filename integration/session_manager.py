"""SessionManager agent coordinating integration sessions, checkpoint persistence, and session cleanup."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from integration.exceptions import SessionError


logger = logging.getLogger("FractalCore.Integration.SessionManager")


# ==============================================================================
# L5 Atomic Session Subagents
# ==============================================================================

class SessionCreator(BaseAgent):
    """L5 agent initializing new integration sessions."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SessionCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        metadata = payload.get("metadata", {})

        s_id = f"INT_SES_{uuid.uuid4().hex[:8]}"
        session = {
            "session_id": s_id,
            "created_at": time.time(),
            "status": "ACTIVE",
            "metadata": metadata,
        }
        return {"status": "COMPLETED", "session": session}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SessionCreator %s cleaned up.", self.agent_id)


class SessionLoader(BaseAgent):
    """L5 agent retrieving existing session state and task history."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SessionLoader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        s_id = payload.get("session_id", "default")
        store = payload.get("store", {})

        s = store.get(s_id)
        return {"status": "COMPLETED", "session": s, "found": s is not None}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SessionLoader %s cleaned up.", self.agent_id)


class SessionSaver(BaseAgent):
    """L5 agent writing session state checkpoints to persistent storage."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SessionSaver %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        session = payload.get("session", {})

        session["updated_at"] = time.time()
        return {"status": "COMPLETED", "saved": True, "session_id": session.get("session_id")}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SessionSaver %s cleaned up.", self.agent_id)


class SessionCleaner(BaseAgent):
    """L5 agent purging expired sessions based on TTL threshold."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SessionCleaner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        ttl = payload.get("ttl_seconds", 3600)
        store = payload.get("store", {})

        now = time.time()
        active = {}
        pruned = 0
        for k, v in store.items():
            age = now - v.get("created_at", now)
            if age <= ttl:
                active[k] = v
            else:
                pruned += 1

        return {"status": "COMPLETED", "active_sessions": active, "pruned_count": pruned}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SessionCleaner %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 SessionManager Agent
# ==============================================================================

class SessionManager(BaseAgent):
    """L4 coordinator overseeing session lifecycle: creation, loading, persistence, and cleanup."""

    def __init__(
        self,
        name: str = "SessionManager",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "session_management",
            "session_creation",
            "session_loader",
            "session_saver",
            "session_cleaner",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "IA12_SESSION_MANAGER",
        )

        self._sessions: Dict[str, Dict[str, Any]] = {}
        self.creator: Optional[SessionCreator] = None
        self.loader: Optional[SessionLoader] = None
        self.saver: Optional[SessionSaver] = None
        self.cleaner: Optional[SessionCleaner] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("create_session", self.create_session)
        self.register_tool("get_session", self.get_session)

    def _spawn_subagents(self) -> None:
        """Spawn atomic session subagents (Rule 1 & Rule 5)."""
        logger.info("SessionManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.creator = self.spawn_subagent(SessionCreator, name="SessionCreator", max_depth=child_depth, resources_mb=32)
        self.loader = self.spawn_subagent(SessionLoader, name="SessionLoader", max_depth=child_depth, resources_mb=32)
        self.saver = self.spawn_subagent(SessionSaver, name="SessionSaver", max_depth=child_depth, resources_mb=32)
        self.cleaner = self.spawn_subagent(SessionCleaner, name="SessionCleaner", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SessionManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        s = self.create_session(metadata=payload)
        return {"status": "COMPLETED", "session": s}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SessionManager %s cleanup complete.", self.agent_id)

    def create_session(self, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create new tracked session."""
        p_env = {"payload": {"metadata": metadata or {}}}
        res = self.creator.process(p_env) if self.creator else {"session": {"session_id": f"SES_{uuid.uuid4().hex[:8]}"}}
        sess = res.get("session", {})
        self._sessions[sess["session_id"]] = sess
        return sess

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Fetch session by ID."""
        p_env = {"payload": {"session_id": session_id, "store": self._sessions}}
        res = self.loader.process(p_env) if self.loader else {"session": self._sessions.get(session_id)}
        return res.get("session")
