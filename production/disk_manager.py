"""Disk storage management utility auditing volume quotas and temp directory pruning."""

from __future__ import annotations

import os
import shutil
from typing import Any, Dict


class DiskManagerUtil:
    """Utility managing disk storage limits (100GB limit)."""

    def __init__(self, disk_limit_gb: int = 100, storage_path: str = ".") -> None:
        self.disk_limit_gb = disk_limit_gb
        self.storage_path = storage_path

    def check_disk_space(self) -> Dict[str, Any]:
        """Audit filesystem storage usage."""
        total, used, free = shutil.disk_usage(self.storage_path)
        used_gb = used / (1024 ** 3)
        free_gb = free / (1024 ** 3)
        return {
            "disk_limit_gb": self.disk_limit_gb,
            "used_gb": round(used_gb, 2),
            "free_gb": round(free_gb, 2),
            "healthy": free_gb > 1.0,
        }
