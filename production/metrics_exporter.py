"""Prometheus metrics exposition and registry utility."""

from __future__ import annotations

import time
from typing import Any, Dict, List


class MetricsExporterUtil:
    """Utility for collecting and exporting system metrics in Prometheus format."""

    def __init__(self, port: int = 9090) -> None:
        self.port = port
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}

    def inc_counter(self, name: str, value: float = 1.0) -> None:
        """Increment counter metric."""
        self.counters[name] = self.counters.get(name, 0.0) + value

    def set_gauge(self, name: str, value: float) -> None:
        """Set gauge metric."""
        self.gauges[name] = value

    def export_prometheus_text(self) -> str:
        """Render metrics in standard Prometheus exposition format."""
        lines: List[str] = []
        for k, v in self.counters.items():
            lines.append(f"# TYPE {k} counter")
            lines.append(f"{k} {v}")
        for k, v in self.gauges.items():
            lines.append(f"# TYPE {k} gauge")
            lines.append(f"{k} {v}")
        return "\n".join(lines) + "\n"
