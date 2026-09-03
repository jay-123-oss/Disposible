"""Circuit Breaker utility implementing Closed, Open, and Half-Open failure threshold transitions."""

from __future__ import annotations

import time
from enum import Enum
from typing import Any, Callable, Dict, Optional


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerUtil:
    """Production circuit breaker protecting downstream dependencies."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout_seconds: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def record_success(self) -> None:
        """Record successful call, resetting breaker state."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record failure, potentially tripping breaker open."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def allow_execution(self) -> bool:
        """Check if request execution is permitted."""
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        # HALF_OPEN allows single probe
        return True

    def get_state(self) -> Dict[str, Any]:
        """Inspect breaker status."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "allowed": self.allow_execution(),
        }
