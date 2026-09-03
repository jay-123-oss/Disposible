"""ContextManager agent propagating hierarchical context, maintaining cross-agent memory, and cleaning scope."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from integration.exceptions import ContextError


logger = logging.getLogger("FractalCore.Integration.ContextManager")


# ==============================================================================
# L5 Atomic Context Manager Subagents
# ==============================================================================

class ContextPropagator(BaseAgent):
    """L5 agent passing parent context down to children or propagating results back to parent."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ContextPropagator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        parent_ctx = payload.get("parent_context", {})
        child_envelope = payload.get("child_envelope", {})

        propagated = dict(parent_ctx)
        propagated.update(child_envelope)
        return {
            "status": "COMPLETED",
            "propagated_context": propagated,
            "keys_propagated": list(propagated.keys()),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ContextPropagator %s cleaned up.", self.agent_id)


class ContextStorage(BaseAgent):
    """L5 agent storing active task contexts in memory."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ContextStorage %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        key = payload.get("context_id", "default")
        data = payload.get("data", {})

        return {
            "status": "COMPLETED",
            "stored": True,
            "context_id": key,
            "stored_at": time.time(),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ContextStorage %s cleaned up.", self.agent_id)


class ContextRetriever(BaseAgent):
    """L5 agent fetching contextual history for a given task or session."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ContextRetriever %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        key = payload.get("context_id", "default")
        store = payload.get("store", {})

        ctx = store.get(key, {})
        return {
            "status": "COMPLETED",
            "context_id": key,
            "context": ctx,
            "found": key in store,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ContextRetriever %s cleaned up.", self.agent_id)


class ContextCleaner(BaseAgent):
    """L5 agent purging completed or orphaned task contexts to prevent memory leakage."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ContextCleaner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        key = payload.get("context_id")
        store = payload.get("store", {})

        removed = False
        if key and key in store:
            del store[key]
            removed = True

        return {
            "status": "COMPLETED",
            "cleaned": removed,
            "context_id": key,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ContextCleaner %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 ContextManager Agent
# ==============================================================================

class ContextManager(BaseAgent):
    """L4 coordinator overseeing hierarchical context propagation, storage, retrieval, and cleanup."""

    def __init__(
        self,
        name: str = "ContextManager",
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
            "context_management",
            "context_propagation",
            "context_storage",
            "context_retrieval",
            "context_cleaner",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "IA14_CONTEXT_MANAGER",
        )

        self._store: Dict[str, Dict[str, Any]] = {}
        self.propagator: Optional[ContextPropagator] = None
        self.storage: Optional[ContextStorage] = None
        self.retriever: Optional[ContextRetriever] = None
        self.cleaner: Optional[ContextCleaner] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("propagate_context", self.propagate_context)
        self.register_tool("store_context", self.store_context)
        self.register_tool("retrieve_context", self.retrieve_context)

    def _spawn_subagents(self) -> None:
        """Spawn atomic context manager subagents (Rule 1 & Rule 5)."""
        logger.info("ContextManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.propagator = self.spawn_subagent(ContextPropagator, name="ContextPropagator", max_depth=child_depth, resources_mb=32)
        self.storage = self.spawn_subagent(ContextStorage, name="ContextStorage", max_depth=child_depth, resources_mb=32)
        self.retriever = self.spawn_subagent(ContextRetriever, name="ContextRetriever", max_depth=child_depth, resources_mb=32)
        self.cleaner = self.spawn_subagent(ContextCleaner, name="ContextCleaner", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ContextManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        cid = payload.get("context_id", "ctx_1")
        data = payload.get("data", {"intent": "test"})
        self.store_context(cid, data)
        ret = self.retrieve_context(cid)
        return {"status": "COMPLETED", "context": ret}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ContextManager %s cleanup complete.", self.agent_id)

    def propagate_context(self, parent_ctx: Dict[str, Any], child_envelope: Dict[str, Any]) -> Dict[str, Any]:
        """Merge parent and child context scopes."""
        p_env = {"payload": {"parent_context": parent_ctx, "child_envelope": child_envelope}}
        res = self.propagator.process(p_env) if self.propagator else {"propagated_context": {}}
        return res.get("propagated_context", {})

    def store_context(self, context_id: str, data: Dict[str, Any]) -> None:
        """Save context dictionary into in-memory store."""
        p_env = {"payload": {"context_id": context_id, "data": data}}
        if self.storage:
            self.storage.process(p_env)
        self._store[context_id] = data

    def retrieve_context(self, context_id: str) -> Dict[str, Any]:
        """Fetch context dictionary from store."""
        p_env = {"payload": {"context_id": context_id, "store": self._store}}
        res = self.retriever.process(p_env) if self.retriever else {"context": self._store.get(context_id, {})}
        return res.get("context", {})
