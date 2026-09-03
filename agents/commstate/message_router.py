"""MessageRouter agent handling direct, broadcast, topic-based, and priority-queued message routing."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.commstate.exceptions import RoutingError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.CommState.MessageRouter")


# ==============================================================================
# L5 Atomic Message Router Subagents
# ==============================================================================

class DirectRouter(BaseAgent):
    """L5 agent routing point-to-point messages strictly between parent/child or registered peers."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DirectRouter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        msg = payload.get("message", {})
        recipient = msg.get("recipient_id")

        return {
            "status": "COMPLETED",
            "routing_mode": "DIRECT",
            "delivered_to": [recipient] if recipient else [],
            "message": msg,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DirectRouter %s cleaned up.", self.agent_id)


class BroadcastRouter(BaseAgent):
    """L5 agent broadcasting critical announcements across all registered active agents."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("BroadcastRouter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        msg = payload.get("message", {})
        all_recipients = list(payload.get("active_agent_ids", []))

        return {
            "status": "COMPLETED",
            "routing_mode": "BROADCAST",
            "delivered_to": all_recipients,
            "message": msg,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("BroadcastRouter %s cleaned up.", self.agent_id)


class TopicRouter(BaseAgent):
    """L5 agent fan-out routing messages to agents subscribed to specific topics."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TopicRouter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        msg = payload.get("message", {})
        topic = payload.get("topic", "DEFAULT")
        topic_map = payload.get("topic_subscribers", {})

        recipients = topic_map.get(topic, [])
        return {
            "status": "COMPLETED",
            "routing_mode": "TOPIC",
            "topic": topic,
            "delivered_to": recipients,
            "message": msg,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TopicRouter %s cleaned up.", self.agent_id)


class PriorityRouter(BaseAgent):
    """L5 agent sorting incoming message buffers by priority (CRITICAL > HIGH > NORMAL > LOW)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PriorityRouter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        messages = list(payload.get("messages", []))

        priority_order = {"CRITICAL": 0, "HIGH": 1, "NORMAL": 2, "LOW": 3}
        sorted_msgs = sorted(
            messages,
            key=lambda m: priority_order.get(m.get("priority", "NORMAL").upper(), 2),
        )
        return {"status": "COMPLETED", "sorted_messages": sorted_msgs}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PriorityRouter %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 MessageRouter Agent
# ==============================================================================

class MessageRouter(BaseAgent):
    """L4 coordinator overseeing multi-modal message dispatching, routing topologies, and priority queues."""

    def __init__(
        self,
        name: str = "MessageRouter",
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
            "message_routing",
            "direct_routing",
            "broadcast_routing",
            "topic_routing",
            "priority_dispatch",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C14_MESSAGE_ROUTER",
        )

        self.direct_rtr: Optional[DirectRouter] = None
        self.bcast_rtr: Optional[BroadcastRouter] = None
        self.topic_rtr: Optional[TopicRouter] = None
        self.prio_rtr: Optional[PriorityRouter] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("route_message", self.route_message)
        self.register_tool("prioritize_queue", self.prioritize_queue)

    def _spawn_subagents(self) -> None:
        """Spawn atomic message router subagents (Rule 1 & Rule 5)."""
        logger.info("MessageRouter %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.direct_rtr = self.spawn_subagent(
            DirectRouter,
            name="DirectRouter",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.bcast_rtr = self.spawn_subagent(
            BroadcastRouter,
            name="BroadcastRouter",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.topic_rtr = self.spawn_subagent(
            TopicRouter,
            name="TopicRouter",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.prio_rtr = self.spawn_subagent(
            PriorityRouter,
            name="PriorityRouter",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MessageRouter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        routed = self.route_message(
            message=payload.get("message", {}),
            mode=payload.get("mode", "DIRECT"),
            context=payload,
        )
        return {"status": "COMPLETED", "routing_result": routed}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("MessageRouter %s cleanup complete.", self.agent_id)

    def route_message(self, message: Dict[str, Any], mode: str = "DIRECT", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Dispatch message according to routing mode."""
        ctx = context or {}
        p_env = {"payload": {"message": message, **ctx}}

        mode_upper = mode.upper()
        if mode_upper == "BROADCAST" and self.bcast_rtr:
            return self.bcast_rtr.process(p_env)
        elif mode_upper == "TOPIC" and self.topic_rtr:
            return self.topic_rtr.process(p_env)
        elif self.direct_rtr:
            return self.direct_rtr.process(p_env)
        else:
            return {"delivered_to": [message.get("recipient_id", "BROADCAST")], "message": message}

    def prioritize_queue(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Order messages by descending priority."""
        p_env = {"payload": {"messages": messages}}
        res = self.prio_rtr.process(p_env) if self.prio_rtr else {"sorted_messages": messages}
        return res.get("sorted_messages", messages)
