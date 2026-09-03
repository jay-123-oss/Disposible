"""EventPublisher agent broadcasting task, agent, state, and error events across the system bus."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from agents.commstate.exceptions import EventError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.CommState.EventPublisher")


# ==============================================================================
# L5 Atomic Event Publisher Subagents
# ==============================================================================

class TaskEventPublisher(BaseAgent):
    """L5 agent constructing and publishing task lifecycle events (created, started, finished)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TaskEventPublisher %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        evt = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "category": "TASK",
            "action": payload.get("action", "TASK_UPDATED"),
            "task_id": payload.get("task_id"),
            "payload": payload.get("data", {}),
            "timestamp": time.time(),
        }
        return {"status": "COMPLETED", "event": evt}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "event" not in result:
            raise EventError("TaskEventPublisher produced invalid event.")
        return result

    def cleanup(self) -> None:
        logger.debug("TaskEventPublisher %s cleaned up.", self.agent_id)


class AgentEventPublisher(BaseAgent):
    """L5 agent publishing agent registration, spawn, and heartbeat events."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AgentEventPublisher %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        evt = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "category": "AGENT",
            "action": payload.get("action", "AGENT_STATE_CHANGED"),
            "agent_id": payload.get("agent_id"),
            "payload": payload.get("data", {}),
            "timestamp": time.time(),
        }
        return {"status": "COMPLETED", "event": evt}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AgentEventPublisher %s cleaned up.", self.agent_id)


class StateEventPublisher(BaseAgent):
    """L5 agent publishing state mutation, checkpoint, and sync notifications."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("StateEventPublisher %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        evt = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "category": "STATE",
            "action": payload.get("action", "STATE_MUTATED"),
            "key": payload.get("key"),
            "payload": payload.get("data", {}),
            "timestamp": time.time(),
        }
        return {"status": "COMPLETED", "event": evt}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("StateEventPublisher %s cleaned up.", self.agent_id)


class ErrorEventPublisher(BaseAgent):
    """L5 agent publishing high-priority security, quality gate, or system exceptions."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ErrorEventPublisher %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        evt = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "category": "ERROR",
            "action": payload.get("action", "SYSTEM_ERROR"),
            "severity": payload.get("severity", "HIGH"),
            "error_msg": payload.get("error_msg", "unspecified error"),
            "timestamp": time.time(),
        }
        return {"status": "COMPLETED", "event": evt}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ErrorEventPublisher %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 EventPublisher Agent
# ==============================================================================

class EventPublisher(BaseAgent):
    """L4 coordinator managing event broadcast and fan-out to subscribers."""

    def __init__(
        self,
        name: str = "EventPublisher",
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
            "event_publishing",
            "event_broadcasting",
            "task_event_dispatch",
            "error_alerting",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C12_EVENT_PUBLISHER",
        )

        self._published_events: List[Dict[str, Any]] = []
        self.task_pub: Optional[TaskEventPublisher] = None
        self.agent_pub: Optional[AgentEventPublisher] = None
        self.state_pub: Optional[StateEventPublisher] = None
        self.error_pub: Optional[ErrorEventPublisher] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("publish_event", self.publish_event)

    def _spawn_subagents(self) -> None:
        """Spawn atomic event publisher subagents (Rule 1 & Rule 5)."""
        logger.info("EventPublisher %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.task_pub = self.spawn_subagent(
            TaskEventPublisher,
            name="TaskEventPublisher",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.agent_pub = self.spawn_subagent(
            AgentEventPublisher,
            name="AgentEventPublisher",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.state_pub = self.spawn_subagent(
            StateEventPublisher,
            name="StateEventPublisher",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.error_pub = self.spawn_subagent(
            ErrorEventPublisher,
            name="ErrorEventPublisher",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("EventPublisher %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        evt = self.publish_event(
            category=payload.get("category", "TASK"),
            action=payload.get("action", "NOTIFY"),
            data=payload.get("data", {}),
        )
        return {"status": "COMPLETED", "published_event": evt}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("EventPublisher %s cleanup complete.", self.agent_id)

    def publish_event(self, category: str, action: str, data: Any = None, agent_id: Optional[str] = None, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Publish an event to the event stream."""
        cat_upper = category.upper()
        p_env = {"payload": {"action": action, "data": data, "agent_id": agent_id, "task_id": task_id}}

        if cat_upper == "TASK" and self.task_pub:
            res = self.task_pub.process(p_env)
        elif cat_upper == "AGENT" and self.agent_pub:
            res = self.agent_pub.process(p_env)
        elif cat_upper == "ERROR" and self.error_pub:
            res = self.error_pub.process(p_env)
        elif self.state_pub:
            res = self.state_pub.process(p_env)
        else:
            res = {"event": {"event_id": "evt_fb", "category": category, "action": action, "timestamp": time.time()}}

        evt = res["event"]
        self._published_events.append(evt)
        return evt
