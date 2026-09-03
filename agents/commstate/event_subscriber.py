"""EventSubscriber agent filtering event streams and dispatching to registered agent handlers."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from agents.commstate.exceptions import EventError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.CommState.EventSubscriber")


# ==============================================================================
# L5 Atomic Event Subscriber Subagents
# ==============================================================================

class TaskEventSubscriber(BaseAgent):
    """L5 agent handling subscriptions and filters for task lifecycle events."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TaskEventSubscriber %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        events = payload.get("events", [])
        action_filter = payload.get("action_filter")

        matched = [
            e for e in events
            if e.get("category") == "TASK" and (not action_filter or e.get("action") == action_filter)
        ]
        return {"status": "COMPLETED", "filtered_events": matched}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TaskEventSubscriber %s cleaned up.", self.agent_id)


class AgentEventSubscriber(BaseAgent):
    """L5 agent handling subscriptions for agent registration and lifecycle events."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AgentEventSubscriber %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        events = payload.get("events", [])
        agent_filter = payload.get("agent_id")

        matched = [
            e for e in events
            if e.get("category") == "AGENT" and (not agent_filter or e.get("agent_id") == agent_filter)
        ]
        return {"status": "COMPLETED", "filtered_events": matched}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AgentEventSubscriber %s cleaned up.", self.agent_id)


class StateEventSubscriber(BaseAgent):
    """L5 agent handling subscriptions for state mutations and checkpoints."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("StateEventSubscriber %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        events = payload.get("events", [])
        key_filter = payload.get("key")

        matched = [
            e for e in events
            if e.get("category") == "STATE" and (not key_filter or e.get("key") == key_filter)
        ]
        return {"status": "COMPLETED", "filtered_events": matched}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("StateEventSubscriber %s cleaned up.", self.agent_id)


class ErrorEventSubscriber(BaseAgent):
    """L5 agent filtering critical and high-severity error events for immediate alerting."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ErrorEventSubscriber %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        events = payload.get("events", [])
        severity = payload.get("severity")

        matched = [
            e for e in events
            if e.get("category") == "ERROR" and (not severity or e.get("severity") == severity)
        ]
        return {"status": "COMPLETED", "filtered_events": matched}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ErrorEventSubscriber %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 EventSubscriber Agent
# ==============================================================================

class EventSubscriber(BaseAgent):
    """L4 coordinator routing incoming event streams to registered listener callbacks."""

    def __init__(
        self,
        name: str = "EventSubscriber",
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
            "event_subscription",
            "event_filtering",
            "callback_dispatch",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C13_EVENT_SUBSCRIBER",
        )

        self._subscriptions: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self.task_sub: Optional[TaskEventSubscriber] = None
        self.agent_sub: Optional[AgentEventSubscriber] = None
        self.state_sub: Optional[StateEventSubscriber] = None
        self.error_sub: Optional[ErrorEventSubscriber] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("subscribe", self.subscribe)
        self.register_tool("filter_events", self.filter_events)

    def _spawn_subagents(self) -> None:
        """Spawn atomic event subscriber subagents (Rule 1 & Rule 5)."""
        logger.info("EventSubscriber %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.task_sub = self.spawn_subagent(
            TaskEventSubscriber,
            name="TaskEventSubscriber",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.agent_sub = self.spawn_subagent(
            AgentEventSubscriber,
            name="AgentEventSubscriber",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.state_sub = self.spawn_subagent(
            StateEventSubscriber,
            name="StateEventSubscriber",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.error_sub = self.spawn_subagent(
            ErrorEventSubscriber,
            name="ErrorEventSubscriber",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("EventSubscriber %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        matched = self.filter_events(
            events=payload.get("events", []),
            category=payload.get("category", "TASK"),
        )
        return {"status": "COMPLETED", "matched_events": matched}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("EventSubscriber %s cleanup complete.", self.agent_id)

    def subscribe(self, category: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register listener callback for event category."""
        cat_upper = category.upper()
        if cat_upper not in self._subscriptions:
            self._subscriptions[cat_upper] = []
        self._subscriptions[cat_upper].append(callback)

    def filter_events(self, events: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
        """Filter list of events by targeted category."""
        cat_upper = category.upper()
        p_env = {"payload": {"events": events}}

        if cat_upper == "TASK" and self.task_sub:
            res = self.task_sub.process(p_env)
        elif cat_upper == "AGENT" and self.agent_sub:
            res = self.agent_sub.process(p_env)
        elif cat_upper == "ERROR" and self.error_sub:
            res = self.error_sub.process(p_env)
        elif self.state_sub:
            res = self.state_sub.process(p_env)
        else:
            res = {"filtered_events": [e for e in events if e.get("category") == cat_upper]}

        return res.get("filtered_events", [])
