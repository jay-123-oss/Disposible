"""Grafana and dashboard model generator utility."""

from __future__ import annotations

import json
from typing import Any, Dict


class DashboardConfigurerUtil:
    """Utility generating Grafana dashboard JSON representations for production observability."""

    @staticmethod
    def generate_dashboard_json(title: str = "Fractal Production Overview") -> Dict[str, Any]:
        """Produce Grafana dashboard model."""
        return {
            "title": title,
            "refresh": "30s",
            "schemaVersion": 16,
            "panels": [
                {
                    "title": "CPU & Memory Utilization",
                    "type": "graph",
                    "targets": [{"expr": "process_cpu_seconds_total"}, {"expr": "process_resident_memory_bytes"}],
                },
                {
                    "title": "Request Latency (p95 / p99)",
                    "type": "heatmap",
                    "targets": [{"expr": "http_request_duration_ms"}],
                },
                {
                    "title": "Active Agents & Task Queue",
                    "type": "stat",
                    "targets": [{"expr": "fractal_active_agents"}, {"expr": "fractal_task_queue_depth"}],
                },
            ],
        }
