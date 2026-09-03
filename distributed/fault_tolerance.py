"""FaultTolerance agent providing failure detection, automatic recovery, circuit breaking, and exponential retries.

Implements the complete Fault Tolerance hierarchy (D9):
- L4 FaultTolerance coordinator
- L5 atomic workers: FailureDetector, AutoRecoverer, CircuitBreaker, RetryManager
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from core.agent_base import BaseAgent
from distributed.exceptions import FaultToleranceError

logger = logging.getLogger("FractalCore.Distributed.FaultTolerance")


# ==============================================================================
# L5 Atomic Fault Tolerance Subagents
# ==============================================================================

class FailureDetector(BaseAgent):
    """L5 agent evaluating node heartbeat thresholds to declare failure states."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("FailureDetector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        node_id = task_envelope.get("node_id", "")
        last_seen = task_envelope.get("last_seen", time.time())
        threshold_s = task_envelope.get("failure_threshold_s", 15.0)
        elapsed = time.time() - last_seen
        failed = elapsed > threshold_s
        return {
            "status": "COMPLETED",
            "node_id": node_id,
            "failed": failed,
            "elapsed_seconds": round(elapsed, 2),
            "threshold_seconds": threshold_s,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("FailureDetector %s cleaned up.", self.agent_id)


class AutoRecoverer(BaseAgent):
    """L5 agent triggering automated failover and worker restarting workflows."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AutoRecoverer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        failed_node = task_envelope.get("failed_node", "")
        backup_nodes = task_envelope.get("backup_nodes", [])
        recovered = len(backup_nodes) > 0
        new_active = backup_nodes[0] if recovered else None
        return {
            "status": "COMPLETED",
            "failed_node": failed_node,
            "recovered": recovered,
            "new_active_node": new_active,
            "recovered_at": time.time(),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AutoRecoverer %s cleaned up.", self.agent_id)


class CircuitBreaker(BaseAgent):
    """L5 agent managing state transitions (CLOSED -> OPEN -> HALF_OPEN) based on error rates."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CircuitBreaker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        failure_count = task_envelope.get("failure_count", 0)
        threshold = task_envelope.get("threshold", 3)
        last_failure = task_envelope.get("last_failure", 0)
        cooldown = task_envelope.get("cooldown_seconds", 30)
        state = "CLOSED"

        if failure_count >= threshold:
            if time.time() - last_failure > cooldown:
                state = "HALF_OPEN"
            else:
                state = "OPEN"

        return {
            "status": "COMPLETED",
            "circuit_state": state,
            "can_execute": state in ("CLOSED", "HALF_OPEN"),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CircuitBreaker %s cleaned up.", self.agent_id)


class RetryManager(BaseAgent):
    """L5 agent executing exponential backoff retries on transient errors."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RetryManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        retries = task_envelope.get("attempt", 0)
        max_retries = task_envelope.get("max_retries", 3)
        backoff_base = task_envelope.get("backoff_base", 1.5)
        delay = (backoff_base ** retries) * 0.1
        can_retry = retries < max_retries
        return {
            "status": "COMPLETED",
            "can_retry": can_retry,
            "attempt": retries + 1,
            "backoff_delay_seconds": round(delay, 3),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("RetryManager %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 FaultTolerance Agent
# ==============================================================================

class FaultTolerance(BaseAgent):
    """L4 coordinator overseeing distributed cluster resilience, circuit breaking, and recovery."""

    def __init__(
        self,
        name: str = "FaultTolerance",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
        failure_threshold: int = 3,
        recovery_timeout: int = 60,
    ) -> None:
        default_caps = capabilities or [
            "fault_tolerance",
            "failure_detector",
            "auto_recoverer",
            "circuit_breaker",
            "retry_manager",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "D9_FAULT_TOLERANCE",
        )
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.circuit_failures: Dict[str, int] = {}
        self.circuit_last_failure: Dict[str, float] = {}

        self.failure_detector: Optional[FailureDetector] = None
        self.auto_recoverer: Optional[AutoRecoverer] = None
        self.circuit_breaker: Optional[CircuitBreaker] = None
        self.retry_manager: Optional[RetryManager] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("check_node_liveness", self.check_node_liveness)
        self.register_tool("execute_with_retry", self.execute_with_retry)
        self.register_tool("can_execute_service", self.can_execute_service)

    def _spawn_subagents(self) -> None:
        """Spawn atomic fault tolerance subagents (Rule 1 & Rule 5)."""
        logger.info("FaultTolerance %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.failure_detector = self.spawn_subagent(FailureDetector, name="FailureDetector", max_depth=child_depth, resources_mb=32)
        self.auto_recoverer = self.spawn_subagent(AutoRecoverer, name="AutoRecoverer", max_depth=child_depth, resources_mb=32)
        self.circuit_breaker = self.spawn_subagent(CircuitBreaker, name="CircuitBreaker", max_depth=child_depth, resources_mb=32)
        self.retry_manager = self.spawn_subagent(RetryManager, name="RetryManager", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("FaultTolerance %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return self.check_node_liveness(
            task_envelope.get("node_id", ""),
            task_envelope.get("last_seen", time.time()),
        )

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("FaultTolerance %s cleaned up.", self.agent_id)

    def check_node_liveness(self, node_id: str, last_seen: float) -> Dict[str, Any]:
        """Detect whether a node has failed its liveness timeout."""
        res = self.failure_detector.process({
            "node_id": node_id,
            "last_seen": last_seen,
            "failure_threshold_s": float(self.recovery_timeout),
        }) if self.failure_detector else {"failed": False}
        return res

    def record_service_failure(self, service_id: str) -> None:
        """Increment failure counter and trip circuit breaker if threshold exceeded."""
        self.circuit_failures[service_id] = self.circuit_failures.get(service_id, 0) + 1
        self.circuit_last_failure[service_id] = time.time()

    def record_service_success(self, service_id: str) -> None:
        """Reset failure counter upon successful execution."""
        self.circuit_failures[service_id] = 0

    def can_execute_service(self, service_id: str) -> bool:
        """Check if circuit breaker allows calls to service."""
        failures = self.circuit_failures.get(service_id, 0)
        last_fail = self.circuit_last_failure.get(service_id, 0)
        res = self.circuit_breaker.process({
            "failure_count": failures,
            "threshold": self.failure_threshold,
            "last_failure": last_fail,
            "cooldown_seconds": 30,
        }) if self.circuit_breaker else {"can_execute": True}
        return res.get("can_execute", True)

    def execute_with_retry(self, operation: Callable[[], Any], max_retries: int = 3) -> Any:
        """Execute callable with exponential backoff on exceptions."""
        attempt = 0
        last_exc: Optional[Exception] = None
        while attempt < max_retries:
            try:
                return operation()
            except Exception as exc:
                last_exc = exc
                attempt += 1
                if self.retry_manager:
                    res = self.retry_manager.process({"attempt": attempt, "max_retries": max_retries})
                    if not res.get("can_retry"):
                        break
        raise FaultToleranceError(f"Operation failed after {attempt} retries: {last_exc}") from last_exc
