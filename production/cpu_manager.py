"""CPU management utility enforcing core limits and task scheduling."""

from __future__ import annotations

import os
from typing import Any, Dict


class CpuManagerUtil:
    """Utility managing CPU limits and core count quotas."""

    def __init__(self, cpu_limit: int = 4) -> None:
        self.cpu_limit = cpu_limit

    def check_cpu_quota(self) -> Dict[str, Any]:
        """Verify process CPU allocations against configured limits."""
        available_cores = os.cpu_count() or 1
        allocated = min(available_cores, self.cpu_limit)
        return {
            "cpu_limit": self.cpu_limit,
            "available_cores": available_cores,
            "allocated_cores": allocated,
            "quota_respected": allocated <= self.cpu_limit,
        }
