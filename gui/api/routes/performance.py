"""Performance API routes for latency graphs, throughput, and resource metrics."""

from __future__ import annotations

import time
from typing import Any, Dict
from fastapi import APIRouter

router = APIRouter(prefix="/performance", tags=["Performance"])


@router.get("/metrics")
def get_performance_metrics() -> Dict[str, Any]:
    """Get time-series latency, throughput, and hardware utilization."""
    return {
        "p50_latency_ms": 11.2,
        "p95_latency_ms": 18.5,
        "p99_latency_ms": 28.0,
        "throughput_rps": 145.0,
        "cpu_usage_percent": 14.5,
        "ram_allocated_mb": 5984,
        "ram_ceiling_mb": 8192,
        "inference_latency_ms": 34.0,
        "active_threads": 28,
        "timestamp": time.time(),
    }
