"""Cache optimizer utility providing cache memory management, TTL tuning, and eviction algorithms."""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any, Dict, Optional


class CacheOptimizerUtil:
    """In-memory LRU cache with hit-ratio tracking and memory boundaries."""

    def __init__(self, max_items: int = 1000, ttl_seconds: int = 300) -> None:
        self.max_items = max_items
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache with TTL validation."""
        if key not in self._cache:
            self.misses += 1
            return None

        val, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            self.misses += 1
            return None

        self._cache.move_to_end(key)
        self.hits += 1
        return val

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value with eviction if max_items reached."""
        expiry = time.time() + (ttl if ttl is not None else self.ttl_seconds)
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, expiry)
        if len(self._cache) > self.max_items:
            self._cache.popitem(last=False)

    def get_hit_ratio(self) -> float:
        """Calculate cache hit percentage."""
        total = self.hits + self.misses
        if total == 0:
            return 100.0
        return round((self.hits / total) * 100.0, 2)

    def clear(self) -> None:
        """Purge all entries."""
        self._cache.clear()
