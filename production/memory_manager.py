"""Memory management utility enforcing 8192 MB limits and allocation quotas."""

from __future__ import annotations

import os
import psutil
from typing import Any, Dict


class MemoryManagerUtil:
    """Utility managing memory quotas and process consumption."""

    def __init__(self, memory_limit_mb: int = 8192) -> None:
        self.memory_limit_mb = memory_limit_mb

    def check_memory_quota(self) -> Dict[str, Any]:
        """Audit current memory consumption against the 8GB limit."""
        process = psutil.Process(os.getpid())
        current_rss_mb = process.memory_info().rss / (1024 * 1024)
        return {
            "memory_limit_mb": self.memory_limit_mb,
            "current_rss_mb": round(current_rss_mb, 2),
            "remaining_mb": round(self.memory_limit_mb - current_rss_mb, 2),
            "quota_respected": current_rss_mb <= self.memory_limit_mb,
        }
