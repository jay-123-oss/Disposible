"""
Cache and Execution Optimizer Utilities.

Provides high-performance caching mechanisms, debounce/throttling helpers,
and execution benchmarking to optimize compute-heavy and I/O-bound operations.
"""

from __future__ import annotations

import functools
import time
from collections import OrderedDict
from typing import Any, Callable, Dict, Generic, Optional, Tuple, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class TTLCache(Generic[T]):
    """
    In-memory LRU cache with Time-To-Live (TTL) expiration support.
    Optimizes repeated queries and prevents stale data accumulation.
    """

    def __init__(self, maxsize: int = 128, default_ttl_seconds: float = 60.0):
        self.maxsize: int = maxsize
        self.default_ttl: float = default_ttl_seconds
        self._cache: OrderedDict[str, Tuple[T, float]] = OrderedDict()
        self._hits: int = 0
        self._misses: int = 0

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Fetch an item from cache if not expired."""
        if key not in self._cache:
            self._misses += 1
            return default

        value, expire_at = self._cache[key]
        if time.time() > expire_at:
            # Expired item removal
            del self._cache[key]
            self._misses += 1
            return default

        # Move accessed key to end (LRU behavior)
        self._cache.move_to_end(key)
        self._hits += 1
        return value

    def set(self, key: str, value: T, ttl_seconds: Optional[float] = None) -> None:
        """Add or update an item with custom or default TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expire_at = time.time() + ttl

        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, expire_at)

        # Evict oldest if capacity exceeded
        if len(self._cache) > self.maxsize:
            self._cache.popitem(last=False)

    def invalidate(self, key: str) -> bool:
        """Manually invalidate a cache key."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    @property
    def stats(self) -> Dict[str, Any]:
        """Return cache performance statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100.0) if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "maxsize": self.maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_pct": round(hit_rate, 2),
        }


def optimize_cached(ttl_seconds: float = 60.0, maxsize: int = 128):
    """
    Decorator for memoizing expensive function calls with TTL cache.
    """
    cache = TTLCache[Any](maxsize=maxsize, default_ttl_seconds=ttl_seconds)

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            key = f"{func.__name__}:{repr(args)}:{repr(sorted(kwargs.items()))}"
            cached_val = cache.get(key)
            if cached_val is not None:
                return cached_val

            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        wrapper.cache = cache  # type: ignore[attr-defined]
        return wrapper

    return decorator


def benchmark(func: Callable[..., R]) -> Callable[..., R]:
    """
    Simple profiling decorator to measure runtime latency of critical code sections.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start_time) * 1000.0
        print(f"[BENCHMARK] {func.__name__} executed in {elapsed:.3f} ms")
        return result

    return wrapper
