"""MailboxManager agent handling point-to-point agent inboxes, read receipts, and delivery queues."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from agents.commstate.exceptions import MailboxError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.CommState.MailboxManager")


# ==============================================================================
# L5 Atomic Mailbox Subagents
# ==============================================================================

class MessageSender(BaseAgent):
    """L5 agent packaging and timestamping outgoing inter-agent messages."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MessageSender %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        msg_id = f"MSG_{uuid.uuid4().hex[:8]}"
        msg = {
            "message_id": msg_id,
            "sender_id": payload.get("sender_id", "ANONYMOUS"),
            "recipient_id": payload.get("recipient_id", "BROADCAST"),
            "content": payload.get("content", {}),
            "priority": payload.get("priority", "NORMAL"),
            "sent_at": time.time(),
            "read": False,
        }
        return {"status": "COMPLETED", "message": msg}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "message" not in result:
            raise MailboxError("MessageSender produced invalid envelope.")
        return result

    def cleanup(self) -> None:
        logger.debug("MessageSender %s cleaned up.", self.agent_id)


class MessageReceiver(BaseAgent):
    """L5 agent buffering incoming messages into recipient agent inboxes."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MessageReceiver %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        mailbox = dict(payload.get("mailbox", {}))
        msg = payload.get("message", {})
        recipient = msg.get("recipient_id", "DEFAULT")

        if recipient not in mailbox:
            mailbox[recipient] = []
        mailbox[recipient].append(msg)

        return {"status": "COMPLETED", "mailbox": mailbox, "delivered": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("MessageReceiver %s cleaned up.", self.agent_id)


class MessageReader(BaseAgent):
    """L5 agent retrieving unread messages and marking read status."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MessageReader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        inbox = list(payload.get("inbox", []))
        unread_only = payload.get("unread_only", True)

        read_messages = []
        for msg in inbox:
            if unread_only and msg.get("read"):
                continue
            msg["read"] = True
            msg["read_at"] = time.time()
            read_messages.append(msg)

        return {"status": "COMPLETED", "messages": read_messages, "count": len(read_messages)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("MessageReader %s cleaned up.", self.agent_id)


class MessageDeleter(BaseAgent):
    """L5 agent purging acknowledged or expired messages from inboxes."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MessageDeleter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        inbox = list(payload.get("inbox", []))
        msg_id = payload.get("message_id")

        updated_inbox = [m for m in inbox if m.get("message_id") != msg_id]
        return {
            "status": "COMPLETED",
            "inbox": updated_inbox,
            "deleted": len(updated_inbox) < len(inbox),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("MessageDeleter %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 MailboxManager Agent
# ==============================================================================

class MailboxManager(BaseAgent):
    """L4 coordinator managing inter-agent communication mailboxes and buffering."""

    def __init__(
        self,
        name: str = "MailboxManager",
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
            "mailbox_management",
            "message_delivery",
            "inbox_retrieval",
            "message_lifecycle",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C4_MAILBOX_MANAGER",
        )

        self._inboxes: Dict[str, List[Dict[str, Any]]] = {}
        self.sender: Optional[MessageSender] = None
        self.receiver: Optional[MessageReceiver] = None
        self.reader: Optional[MessageReader] = None
        self.deleter: Optional[MessageDeleter] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("send_message", self.send_message)
        self.register_tool("read_messages", self.read_messages)
        self.register_tool("delete_message", self.delete_message)

    def _spawn_subagents(self) -> None:
        """Spawn atomic mailbox subagents (Rule 1 & Rule 5)."""
        logger.info("MailboxManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.sender = self.spawn_subagent(
            MessageSender,
            name="MessageSender",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.receiver = self.spawn_subagent(
            MessageReceiver,
            name="MessageReceiver",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.reader = self.spawn_subagent(
            MessageReader,
            name="MessageReader",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.deleter = self.spawn_subagent(
            MessageDeleter,
            name="MessageDeleter",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MailboxManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        action = payload.get("action", "read")

        if action == "send":
            msg = self.send_message(
                sender_id=payload.get("sender_id", "SYS"),
                recipient_id=payload.get("recipient_id", "ALL"),
                content=payload.get("content", {}),
            )
            return {"status": "COMPLETED", "message": msg}
        else:
            msgs = self.read_messages(recipient_id=payload.get("recipient_id", "ALL"))
            return {"status": "COMPLETED", "messages": msgs}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("MailboxManager %s cleanup complete.", self.agent_id)

    def send_message(self, sender_id: str, recipient_id: str, content: Any, priority: str = "NORMAL") -> Dict[str, Any]:
        """Dispatch message to recipient inbox."""
        p_env = {"payload": {"sender_id": sender_id, "recipient_id": recipient_id, "content": content, "priority": priority}}
        res_send = self.sender.process(p_env) if self.sender else {"message": {"message_id": "MSG_FB", "recipient_id": recipient_id}}
        msg = res_send["message"]

        p_rcv = {"payload": {"mailbox": self._inboxes, "message": msg}}
        if self.receiver:
            r_res = self.receiver.process(p_rcv)
            self._inboxes = r_res.get("mailbox", self._inboxes)
        else:
            if recipient_id not in self._inboxes:
                self._inboxes[recipient_id] = []
            self._inboxes[recipient_id].append(msg)

        return msg

    def read_messages(self, recipient_id: str, unread_only: bool = True) -> List[Dict[str, Any]]:
        """Fetch and acknowledge messages for agent."""
        inbox = self._inboxes.get(recipient_id, [])
        p_env = {"payload": {"inbox": inbox, "unread_only": unread_only}}
        res = self.reader.process(p_env) if self.reader else {"messages": inbox}
        return res.get("messages", [])

    def delete_message(self, recipient_id: str, message_id: str) -> bool:
        """Remove specific message from agent inbox."""
        if recipient_id not in self._inboxes:
            return False
        p_env = {"payload": {"inbox": self._inboxes[recipient_id], "message_id": message_id}}
        res = self.deleter.process(p_env) if self.deleter else {"deleted": False}
        if res.get("deleted"):
            self._inboxes[recipient_id] = res.get("inbox", [])
            return True
        return False
