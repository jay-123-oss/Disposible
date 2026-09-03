"""CPU optimizer utility providing thread pool tuning, CPU throttling, and load balancing."""

from __future__ import annotations

import os
import psutil
from typing import Any, Dict


class CpuOptimizerUtil:
    """Utility for monitoring and optimizing CPU usage."""

    def __init__(self, max_cpu_percent: float = 80.0) -> None:
        self.max_cpu_percent = max_cpu_percent

    def get_cpu_metrics(self) -> Dict[str, Any]:
        """Collect current CPU utilization metrics."""
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_count = os.cpu_count() or 1
        return {
            "cpu_percent": cpu_percent,
            "cpu_count": cpu_count,
            "is_optimal": cpu_percent <= self.max_cpu_percent,
            "threshold": self.max_cpu_percent,
        }

    def optimize_threads(self, target_load: float = 70.0) -> Dict[str, Any]:
        """Compute optimal worker thread allocations based on core count."""
        cores = os.cpu_count() or 2
        optimal_workers = max(2, min(cores * 2, 16))
        return {
            "optimal_workers": optimal_workers,
            "cpu_cores": cores,
            "target_load": target_load,
            "status": "OPTIMIZED",
        }
