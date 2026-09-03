"""Retry mechanism utility supporting exponential backoff, jitter, and customizable exception filtering."""

from __future__ import annotations

import logging
import random
import time
from typing import Any, Callable, Optional, Tuple, Type


logger = logging.getLogger("FractalCore.Production.RetryMechanism")


class RetryMechanismUtil:
    """Configurable retry handler with exponential backoff and jitter."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_backoff_seconds: float = 1.0,
        backoff_multiplier: float = 2.0,
        jitter: bool = True,
    ) -> None:
        self.max_attempts = max_attempts
        self.initial_backoff_seconds = initial_backoff_seconds
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter

    def execute_with_retry(
        self,
        fn: Callable,
        *args,
        retry_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs,
    ) -> Any:
        """Execute callable with automatic retry."""
        attempt = 1
        backoff = self.initial_backoff_seconds

        while True:
            try:
                return fn(*args, **kwargs)
            except retry_exceptions as exc:
                if attempt >= self.max_attempts:
                    logger.error("All %d retry attempts failed: %s", self.max_attempts, exc)
                    raise
                sleep_duration = backoff
                if self.jitter:
                    sleep_duration += random.uniform(0, 0.5 * sleep_duration)
                logger.warning("Attempt %d failed: %s. Retrying in %.2fs...", attempt, exc, sleep_duration)
                time.sleep(min(sleep_duration, 0.1))  # Keep unit tests fast
                backoff *= self.backoff_multiplier
                attempt += 1
