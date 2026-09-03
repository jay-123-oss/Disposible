"""Runtime profiler providing execution timing, memory consumption deltas, and bottleneck identification."""

from __future__ import annotations

import os
import psutil
import time
from typing import Any, Callable, Dict


class RuntimeProfiler:
    """Utility for measuring function latency and memory overhead."""

    @staticmethod
    def profile_call(fn: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Profile a callable execution."""
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / (1024 * 1024)
        start_time = time.perf_counter()

        result = fn(*args, **kwargs)

        end_time = time.perf_counter()
        mem_after = process.memory_info().rss / (1024 * 1024)
        duration_ms = (end_time - start_time) * 1000.0

        return {
            "result": result,
            "duration_ms": round(duration_ms, 3),
            "memory_before_mb": round(mem_before, 2),
            "memory_after_mb": round(mem_after, 2),
            "memory_delta_mb": round(mem_after - mem_before, 2),
            "within_sla": duration_ms < 200.0,
        }
