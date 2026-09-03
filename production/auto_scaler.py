"""Auto-scaling algorithm and cooldown controller utility."""

from __future__ import annotations

import time
from typing import Any, Dict


class AutoScalerUtil:
    """Horizontal Pod and worker autoscaling calculator."""

    def __init__(
        self,
        min_replicas: int = 2,
        max_replicas: int = 10,
        scale_up_cpu_threshold: float = 70.0,
        scale_down_cpu_threshold: float = 30.0,
        cooldown_seconds: int = 300,
    ) -> None:
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.scale_up_cpu_threshold = scale_up_cpu_threshold
        self.scale_down_cpu_threshold = scale_down_cpu_threshold
        self.cooldown_seconds = cooldown_seconds
        self.last_scale_time = 0.0

    def evaluate_scale(self, current_replicas: int, current_cpu_percent: float) -> Dict[str, Any]:
        """Compute recommended replica count based on utilization."""
        now = time.time()
        in_cooldown = (now - self.last_scale_time) < self.cooldown_seconds

        target = current_replicas
        action = "NOOP"

        if not in_cooldown:
            if current_cpu_percent >= self.scale_up_cpu_threshold and current_replicas < self.max_replicas:
                target = min(self.max_replicas, current_replicas + 1)
                action = "SCALE_UP"
                self.last_scale_time = now
            elif current_cpu_percent <= self.scale_down_cpu_threshold and current_replicas > self.min_replicas:
                target = max(self.min_replicas, current_replicas - 1)
                action = "SCALE_DOWN"
                self.last_scale_time = now

        return {
            "current_replicas": current_replicas,
            "target_replicas": target,
            "action": action,
            "in_cooldown": in_cooldown,
            "cpu_percent": current_cpu_percent,
        }
