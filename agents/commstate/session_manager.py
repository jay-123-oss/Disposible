"""SessionManager agent handling multi-agent session contexts, persistence, timeouts, and teardown."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from agents.commstate.exceptions import SessionError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.CommState.SessionManager")


# ==============================================================================
# L5 Atomic Session Subagents
# ==============================================================================

class SessionCreator(BaseAgent):
    """L5 agent initializing new session contexts with timeouts and active agent trackers."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SessionCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        session_id = payload.get("session_id") or f"SES_{uuid.uuid4().hex[:8]}"
        timeout = payload.get("timeout_seconds", 3600)
        session = {
            "session_id": session_id,
            "status": "ACTIVE",
            "created_at": time.time(),
            "expires_at": time.time() + timeout,
            "metadata": payload.get("metadata", {}),
            "agents": [],
            "tasks": [],
        }
        return {"status": "COMPLETED", "session": session}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "session" not in result:
            raise SessionError("SessionCreator produced invalid session.")
        return result

    def cleanup(self) -> None:
        logger.debug("SessionCreator %s cleaned up.", self.agent_id)


class SessionLoader(BaseAgent):
    """L5 agent loading existing session state from storage."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SessionLoader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        store = payload.get("session_store", {})
        session_id = payload.get("session_id")

        matched = store.get(session_id) if session_id else None
        return {"status": "COMPLETED", "session": matched, "found": matched is not None}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SessionLoader %s cleaned up.", self.agent_id)


class SessionSaver(BaseAgent):
    """L5 agent committing session mutations to memory store."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SessionSaver %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        session = dict(payload.get("session", {}))
        updates = payload.get("updates", {})
        session.update(updates)
        session["updated_at"] = time.time()
        return {"status": "COMPLETED", "session": session}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SessionSaver %s cleaned up.", self.agent_id)


class SessionCleaner(BaseAgent):
    """L5 agent terminating and pruning expired session contexts."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SessionCleaner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        store = dict(payload.get("session_store", {}))
        now = time.time()

        cleaned = []
        for s_id, s in list(store.items()):
            if now > s.get("expires_at", now + 1):
                del store[s_id]
                cleaned.append(s_id)

        return {"status": "COMPLETED", "session_store": store, "cleaned_count": len(cleaned)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SessionCleaner %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 SessionManager Agent
# ==============================================================================

class SessionManager(BaseAgent):
    """L4 coordinator overseeing execution sessions, timeout enforcement, and cleanup."""

    def __init__(
        self,
        name: str = "SessionManager",
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
            "session_management",
            "session_lifecycle",
            "timeout_enforcement",
            "session_restoration",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C9_SESSION_MANAGER",
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
        self.register_tool("cleanup_expired_sessions", self.cleanup_expired_sessions)

    def _spawn_subagents(self) -> None:
        """Spawn atomic session subagents (Rule 1 & Rule 5)."""
        logger.info("SessionManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.creator = self.spawn_subagent(
            SessionCreator,
            name="SessionCreator",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.loader = self.spawn_subagent(
            SessionLoader,
            name="SessionLoader",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.saver = self.spawn_subagent(
            SessionSaver,
            name="SessionSaver",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.cleaner = self.spawn_subagent(
            SessionCleaner,
            name="SessionCleaner",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SessionManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        s = self.create_session(metadata=payload.get("metadata", {}))
        return {"status": "COMPLETED", "session": s}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SessionManager %s cleanup complete.", self.agent_id)

    def create_session(self, metadata: Optional[Dict[str, Any]] = None, timeout_seconds: int = 3600) -> Dict[str, Any]:
        """Initialize new session context."""
        p_env = {"payload": {"metadata": metadata or {}, "timeout_seconds": timeout_seconds}}
        res = self.creator.process(p_env) if self.creator else {"session": {"session_id": "SES_FB", "status": "ACTIVE"}}
        s = res["session"]
        self._sessions[s["session_id"]] = s
        return s

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve active session by ID."""
        p_env = {"payload": {"session_store": self._sessions, "session_id": session_id}}
        res = self.loader.process(p_env) if self.loader else {"session": self._sessions.get(session_id)}
        return res.get("session")

    def cleanup_expired_sessions(self) -> int:
        """Purge sessions that have exceeded their TTL."""
        p_env = {"payload": {"session_store": self._sessions}}
        res = self.cleaner.process(p_env) if self.cleaner else {"cleaned_count": 0}
        self._sessions = res.get("session_store", self._sessions)
        return res.get("cleaned_count", 0)
