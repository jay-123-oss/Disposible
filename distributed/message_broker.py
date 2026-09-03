"""MessageBroker agent handling inter-node asynchronous publish/subscribe, queuing, and topic routing.

Implements the complete Message Broker hierarchy (D7):
- L4 MessageBroker coordinator
- L5 atomic workers: Publisher, Subscriber, QueueManager, TopicManager
"""

from __future__ import annotations

import collections
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from core.agent_base import BaseAgent
from distributed.exceptions import MessageBrokerError

logger = logging.getLogger("FractalCore.Distributed.MessageBroker")


# ==============================================================================
# L5 Atomic Message Broker Subagents
# ==============================================================================

class Publisher(BaseAgent):
    """L5 agent publishing envelopes into target queues or broadcast topics."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("Publisher %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        topic = task_envelope.get("topic", "default")
        payload = task_envelope.get("payload", {})
        msg = {
            "id": f"msg-{int(time.time()*1000)}",
            "topic": topic,
            "payload": payload,
            "published_at": time.time(),
        }
        return {"status": "COMPLETED", "message": msg, "published": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("Publisher %s cleaned up.", self.agent_id)


class Subscriber(BaseAgent):
    """L5 agent delivering published messages to registered callback listeners."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("Subscriber %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        subscribers = task_envelope.get("subscribers", [])
        message = task_envelope.get("message", {})
        delivered_count = 0
        for sub in subscribers:
            if callable(sub):
                try:
                    sub(message)
                    delivered_count += 1
                except Exception as exc:
                    logger.warning("Subscriber callback failed: %s", exc)
        return {"status": "COMPLETED", "delivered_count": delivered_count}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("Subscriber %s cleaned up.", self.agent_id)


class QueueManager(BaseAgent):
    """L5 agent managing durable FIFO queues and message acknowledgments."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("QueueManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        queues = task_envelope.get("queues", {})
        action = task_envelope.get("action", "length")
        queue_name = task_envelope.get("queue_name", "default")

        if action == "enqueue":
            if queue_name not in queues:
                queues[queue_name] = collections.deque()
            queues[queue_name].append(task_envelope.get("item"))
            return {"status": "COMPLETED", "queue_size": len(queues[queue_name])}
        elif action == "dequeue":
            q = queues.get(queue_name)
            item = q.popleft() if q else None
            return {"status": "COMPLETED", "item": item, "queue_size": len(q) if q else 0}

        return {"status": "COMPLETED", "queue_size": len(queues.get(queue_name, []))}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("QueueManager %s cleaned up.", self.agent_id)


class TopicManager(BaseAgent):
    """L5 agent creating, indexing, and routing topic hierarchies."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TopicManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        topics = task_envelope.get("topics", set())
        topic_name = task_envelope.get("topic_name", "")
        if topic_name:
            topics.add(topic_name)
        return {"status": "COMPLETED", "topics": sorted(list(topics)), "topic_count": len(topics)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TopicManager %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 MessageBroker Agent
# ==============================================================================

class MessageBroker(BaseAgent):
    """L4 coordinator providing in-memory and distributed publish/subscribe messaging."""

    def __init__(
        self,
        name: str = "MessageBroker",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
        broker_type: str = "rabbitmq",
    ) -> None:
        default_caps = capabilities or [
            "message_broker",
            "publisher",
            "subscriber",
            "queue_manager",
            "topic_manager",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "D7_MESSAGE_BROKER",
        )
        self.broker_type = broker_type
        self.topics: set = set()
        self.subscriptions: Dict[str, List[Callable[[Any], None]]] = {}
        self.queues: Dict[str, collections.deque] = {}

        self.publisher: Optional[Publisher] = None
        self.subscriber: Optional[Subscriber] = None
        self.queue_manager: Optional[QueueManager] = None
        self.topic_manager: Optional[TopicManager] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("publish", self.publish)
        self.register_tool("subscribe", self.subscribe)

    def _spawn_subagents(self) -> None:
        """Spawn atomic message broker subagents (Rule 1 & Rule 5)."""
        logger.info("MessageBroker %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.publisher = self.spawn_subagent(Publisher, name="Publisher", max_depth=child_depth, resources_mb=32)
        self.subscriber = self.spawn_subagent(Subscriber, name="Subscriber", max_depth=child_depth, resources_mb=32)
        self.queue_manager = self.spawn_subagent(QueueManager, name="QueueManager", max_depth=child_depth, resources_mb=32)
        self.topic_manager = self.spawn_subagent(TopicManager, name="TopicManager", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MessageBroker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return self.publish(task_envelope.get("topic", "default"), task_envelope.get("payload", {}))

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("MessageBroker %s cleaned up.", self.agent_id)

    def subscribe(self, topic: str, callback: Callable[[Any], None]) -> bool:
        """Register a callback handler for messages published to a topic."""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(callback)
        self.topics.add(topic)
        if self.topic_manager:
            self.topic_manager.process({"topics": self.topics, "topic_name": topic})
        return True

    def publish(self, topic: str, payload: Any) -> Dict[str, Any]:
        """Publish a message to all subscribers of a topic and enqueue."""
        res = self.publisher.process({"topic": topic, "payload": payload}) if self.publisher else {
            "message": {"topic": topic, "payload": payload, "published_at": time.time()}
        }
        msg = res["message"]
        
        # Enqueue for durable consumption
        if topic not in self.queues:
            self.queues[topic] = collections.deque()
        self.queues[topic].append(msg)

        delivered = 0
        subs = self.subscriptions.get(topic, [])
        if self.subscriber and subs:
            sub_res = self.subscriber.process({"subscribers": subs, "message": msg})
            delivered = sub_res.get("delivered_count", 0)

        return {"published": True, "topic": topic, "delivered_to": delivered, "queue_depth": len(self.queues[topic])}

    def poll(self, queue_name: str) -> Optional[Any]:
        """Fetch and remove next item from named queue."""
        q = self.queues.get(queue_name)
        return q.popleft() if q else None
