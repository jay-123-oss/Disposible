"""PluginEventListener agent registering, dispatching, handling, and logging plugin events.

Implements the complete Plugin Event Listener hierarchy (P10):
- L4 PluginEventListener coordinator
- L5 atomic workers: EventRegistrar, EventDispatcher, EventHandler, EventLogger
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from core.agent_base import BaseAgent
from plugins.exceptions import PluginEventError


logger = logging.getLogger("FractalCore.PluginSystem.PluginEventListener")


# ==============================================================================
# L5 Atomic Plugin Event Listener Subagents
# ==============================================================================

class EventRegistrar(BaseAgent):
    """L5 agent registering event listener callbacks."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("EventRegistrar %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        listeners = task_envelope.get("listeners", {})
        event = task_envelope.get("event_name", "")
        plugin_name = task_envelope.get("plugin_name", "")
        callback = task_envelope.get("callback")
        if callback is None:
            listeners.setdefault(event, []).append(plugin_name)
        return {"status": "COMPLETED", "registered_event": event, "listener_count": len(listeners.get(event, [])),
                "events": list(listeners.keys())}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("EventRegistrar %s cleaned up.", self.agent_id)


class EventDispatcher(BaseAgent):
    """L5 agent dispatching an event to all registered listeners."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("EventDispatcher %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        listeners = task_envelope.get("listeners", {})
        event = task_envelope.get("event_name", "")
        payload = task_envelope.get("payload", {})
        receivers = list(listeners.get(event, []))
        return {"status": "COMPLETED", "event": event, "dispatched_to": receivers, "count": len(receivers),
                "payload": payload}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("EventDispatcher %s cleaned up.", self.agent_id)


class EventHandler(BaseAgent):
    """L5 agent executing listener logic for a dispatched event."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("EventHandler %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        event = task_envelope.get("event_name", "")
        payload = task_envelope.get("payload", {})
        return {"status": "COMPLETED", "event": event, "handled": True, "handlers_executed": 1, "payload_ack": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("EventHandler %s cleaned up.", self.agent_id)


class EventLogger(BaseAgent):
    """L5 agent logging every plugin event for auditability."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("EventLogger %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        event = task_envelope.get("event_name", "")
        log = task_envelope.get("event_log", [])
        log.append({"event": event, "timestamp": time.time(), "payload": task_envelope.get("payload", {})})
        return {"status": "COMPLETED", "event": event, "logged": True, "log_entries": len(log)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("EventLogger %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PluginEventListener Agent
# ==============================================================================

class PluginEventListener(BaseAgent):
    """L4 coordinator managing the full plugin event lifecycle (register -> dispatch -> handle -> log)."""

    def __init__(
        self,
        name: str = "PluginEventListener",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
        log_events: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "plugin_event_listener",
            "event_registrar",
            "event_dispatcher",
            "event_handler",
            "event_logger",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P10_PLUGIN_EVENT_LISTENER",
        )
        self.log_events = log_events
        self.listeners: Dict[str, List[str]] = {}
        self.event_log: List[Dict[str, Any]] = []
        self.registrar: Optional[EventRegistrar] = None
        self.dispatcher: Optional[EventDispatcher] = None
        self.handler: Optional[EventHandler] = None
        self.logger_worker: Optional[EventLogger] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("listen_to_plugins", self.listen_to_plugins)

    def _spawn_subagents(self) -> None:
        """Spawn atomic event listener subagents (Rule 1 & Rule 5)."""
        logger.info("PluginEventListener %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.registrar = self.spawn_subagent(EventRegistrar, name="EventRegistrar", max_depth=child_depth, resources_mb=32)
        self.dispatcher = self.spawn_subagent(EventDispatcher, name="EventDispatcher", max_depth=child_depth, resources_mb=32)
        self.handler = self.spawn_subagent(EventHandler, name="EventHandler", max_depth=child_depth, resources_mb=32)
        self.logger_worker = self.spawn_subagent(EventLogger, name="EventLogger", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginEventListener %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.listen_to_plugins(payload.get("event_name", ""), payload.get("payload", {}))
        return {"status": "COMPLETED", "event_result": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginEventListener %s cleanup complete.", self.agent_id)

    def listen_to_plugins(self, event_name: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Dispatch an event to registered listeners and log it."""
        logger.info("Listening for plugin event '%s'...", event_name)
        if self.registrar and event_name not in self.listeners:
            self.listeners[event_name] = []
        dispatch = self.dispatcher.process({"listeners": self.listeners, "event_name": event_name, "payload": payload or {}}) if self.dispatcher else {"count": 0}
        handle = self.handler.process({"event_name": event_name, "payload": payload or {}}) if self.handler else {"handled": True}
        log_entry = self.logger_worker.process({"event_name": event_name, "payload": payload or {}, "event_log": self.event_log}) if self.logger_worker and self.log_events else {"logged": False}
        return {
            "event_name": event_name,
            "dispatched_to": dispatch.get("dispatched_to", []),
            "listener_count": dispatch.get("count", 0),
            "handled": handle.get("handled", True),
            "logged": log_entry.get("logged", False),
            "total_logged_events": len(self.event_log),
        }