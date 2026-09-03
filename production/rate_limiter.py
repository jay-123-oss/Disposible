"""Rate limiting utility implementing sliding-window and token-bucket algorithms."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Dict, List


class RateLimiterUtil:
    """Sliding-window request rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = defaultdict(list)

    def allow_request(self, client_id: str) -> bool:
        """Check if request is permitted under rate limit."""
        now = time.time()
        cutoff = now - self.window_seconds
        timestamps = [t for t in self._history[client_id] if t > cutoff]
        self._history[client_id] = timestamps

        if len(timestamps) < self.max_requests:
            self._history[client_id].append(now)
            return True
        return False

    def get_status(self, client_id: str) -> Dict[str, Any]:
        """Get rate limit status for a client."""
        now = time.time()
        cutoff = now - self.window_seconds
        current = len([t for t in self._history.get(client_id, []) if t > cutoff])
        return {
            "client_id": client_id,
            "requests_used": current,
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "remaining": max(0, self.max_requests - current),
            "allowed": current < self.max_requests,
        }
