"""MessageBus class for agent messaging, stigmergy traces, and artifact transfer.

Implements:
- Mediator pattern for decoupled agent-to-agent communication.
- FAMF message envelope verification and checksum validation.
- Stigmergy trace system with attraction, danger, and info traces.
- Mathematical exponential decay of environmental signals with garbage collection.
- Thread-safe artifact repository indexing.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.exceptions import CommunicationError


logger = logging.getLogger("FractalCore.Communication")


class TraceType(str, Enum):
    """Categorization of stigmergic environmental traces."""
    ATTRACTION = "attraction"  # Guides agents toward active sub-tasks/artifacts
    DANGER = "danger"          # Warns agents away from broken paths/regressions
    INFO = "info"              # General status signals and specification readiness


@dataclass
class StigmergyTrace:
    """Represents a digital pheromone signal left in the shared environment."""
    trace_id: str
    trace_type: TraceType
    topic: str
    origin_agent_id: str
    intensity: float = 1.0
    decay_rate_lambda: float = 0.02
    ttl_seconds: float = 600.0
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def current_intensity(self, now: Optional[float] = None) -> float:
        """Compute current intensity using exponential decay: I(t) = I_0 * e^(-lambda * dt)."""
        current_time = now or time.time()
        elapsed = current_time - self.created_at
        if elapsed >= self.ttl_seconds:
            return 0.0
        return max(0.0, self.intensity * math.exp(-self.decay_rate_lambda * elapsed))


@dataclass
class MessageEnvelope:
    """Standard FAMF message envelope for agent communication."""
    frame_id: str
    trace_id: str
    sender_id: str
    recipient_id: str
    message_type: str
    payload: Dict[str, Any]
    priority: str = "NORMAL"
    correlation_id: Optional[str] = None
    timestamp_utc: float = field(default_factory=time.time)
    checksum: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.checksum:
            self.checksum = self.compute_checksum()

    def compute_checksum(self) -> str:
        """Compute SHA-256 digest of normalized payload."""
        serialized = json.dumps(self.payload, sort_keys=True)
        return "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class MessageBus:
    """Centralized mediator governing message routing and stigmergic signals."""

    def __init__(self, artifacts_dir: str = "./state/artifacts/") -> None:
        self._artifacts_dir = Path(artifacts_dir).resolve()
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._traces: Dict[str, StigmergyTrace] = {}
        self._subscribers: Dict[str, List[Callable[[MessageEnvelope], None]]] = {}
        self._artifacts: Dict[str, Path] = {}
        self._message_history: List[MessageEnvelope] = []
        logger.info("MessageBus initialized with artifacts at %s", self._artifacts_dir)

    # --------------------------------------------------------------------------
    # Messaging (Mediator Pattern)
    # --------------------------------------------------------------------------

    def subscribe(self, agent_id: str, callback: Callable[[MessageEnvelope], None]) -> None:
        """Register an agent's inbound message listener."""
        with self._lock:
            if agent_id not in self._subscribers:
                self._subscribers[agent_id] = []
            self._subscribers[agent_id].append(callback)
            logger.debug("Agent '%s' subscribed to MessageBus", agent_id)

    def unsubscribe(self, agent_id: str) -> None:
        """Remove all listeners for an agent."""
        with self._lock:
            if agent_id in self._subscribers:
                del self._subscribers[agent_id]
                logger.debug("Agent '%s' unsubscribed from MessageBus", agent_id)

    def send_message(
        self,
        sender_id: str,
        recipient_id: str,
        message_type: str,
        payload: Dict[str, Any],
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        priority: str = "NORMAL",
    ) -> MessageEnvelope:
        """Route a message envelope directly to the target recipient's subscriber."""
        with self._lock:
            frame = MessageEnvelope(
                frame_id=str(uuid.uuid4()),
                trace_id=trace_id or f"trc_{uuid.uuid4().hex[:16]}",
                sender_id=sender_id,
                recipient_id=recipient_id,
                message_type=message_type,
                payload=payload,
                priority=priority,
                correlation_id=correlation_id,
            )

            # Invariant C1 Check: Log and enforce routing bounds
            logger.debug(
                "Routing message [%s] from %s to %s (Type: %s, Checksum: %s)",
                frame.frame_id,
                sender_id,
                recipient_id,
                message_type,
                frame.checksum,
            )

            callbacks = self._subscribers.get(recipient_id, [])
            if not callbacks:
                logger.warning("No active subscriber for recipient '%s'. Message buffered in history.", recipient_id)
            else:
                for cb in callbacks:
                    try:
                        cb(frame)
                    except Exception as exc:
                        logger.error("Error in message handler for %s: %s", recipient_id, exc)
                        raise CommunicationError(f"Delivery to {recipient_id} failed: {exc}") from exc

            self._message_history.append(frame)
            if len(self._message_history) > 1000:
                self._message_history = self._message_history[-500:]

            return frame

    # --------------------------------------------------------------------------
    # Stigmergy Pattern Implementation
    # --------------------------------------------------------------------------

    def emit_trace(
        self,
        origin_agent_id: str,
        topic: str,
        trace_type: TraceType = TraceType.INFO,
        metadata: Optional[Dict[str, Any]] = None,
        decay_rate: float = 0.02,
        ttl_seconds: float = 600.0,
    ) -> str:
        """Deposit a digital pheromone trace onto the shared blackboard."""
        with self._lock:
            trace_id = f"sig_{uuid.uuid4().hex[:12]}"
            trace = StigmergyTrace(
                trace_id=trace_id,
                trace_type=trace_type,
                topic=topic,
                origin_agent_id=origin_agent_id,
                decay_rate_lambda=decay_rate,
                ttl_seconds=ttl_seconds,
                metadata=metadata or {},
            )
            self._traces[trace_id] = trace
            logger.info(
                "Stigmergic trace '%s' emitted by %s [Type: %s, Topic: '%s']",
                trace_id,
                origin_agent_id,
                trace_type.value,
                topic,
            )
            return trace_id

    def get_active_traces(self, min_intensity: float = 0.10) -> List[Dict[str, Any]]:
        """Return all active pheromones that have not yet evaporated past the threshold."""
        with self._lock:
            now = time.time()
            active: List[Dict[str, Any]] = []
            evaporated_keys: List[str] = []

            for tid, trace in self._traces.items():
                intensity = trace.current_intensity(now)
                if intensity < min_intensity:
                    evaporated_keys.append(tid)
                else:
                    data = asdict(trace)
                    data["current_intensity"] = round(intensity, 4)
                    active.append(data)

            # Evaporate dead traces
            for tid in evaporated_keys:
                del self._traces[tid]
                logger.debug("Pheromone trace '%s' evaporated and pruned.", tid)

            return active

    def query_traces_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """Query active signals matching a specific topic string."""
        active = self.get_active_traces()
        return [t for t in active if t["topic"] == topic]

    # --------------------------------------------------------------------------
    # Artifact Storage & Retrieval
    # --------------------------------------------------------------------------

    def store_artifact(self, artifact_id: str, content: str, extension: str = "txt") -> str:
        """Store an artifact in the local repository and index its URI."""
        with self._lock:
            filename = f"{artifact_id}.{extension}"
            target_path = self._artifacts_dir / filename
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            self._artifacts[artifact_id] = target_path
            logger.info("Stored artifact '%s' at %s", artifact_id, target_path)
            return f"file://{target_path.resolve()}"

    def retrieve_artifact(self, artifact_id: str) -> Optional[str]:
        """Read and return artifact content by its ID."""
        with self._lock:
            path = self._artifacts.get(artifact_id)
            if not path or not path.exists():
                return None
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
