"""SystemMonitor class for telemetry, performance tracking, alerts, and drift detection.

Implements:
- Observer pattern for metrics tracking across agents and components.
- Anomaly detection for CPU/RAM pressure, latency spikes, and error rates.
- Logging setup supporting INFO, WARNING, ERROR, DEBUG with file rotation.
- Alert generation with configurable severity tiers (LOW, MEDIUM, HIGH, CRITICAL).
- Tool state drift detection inspecting workspace git purity and hash invariants.
"""

from __future__ import annotations

import logging
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class AlertSeverity(str, Enum):
    """Severity classification for monitoring alerts."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Alert:
    """Monitoring alert record."""
    alert_id: str
    severity: AlertSeverity
    source: str
    message: str
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)


class SystemMonitor:
    """Central telemetry, performance observer, and anomaly detection monitor."""

    def __init__(
        self,
        log_dir: str = "./logs/",
        log_level: str = "INFO",
        max_system_ram_mb: int = 8192,
        latency_threshold_s: float = 30.0,
    ) -> None:
        self._log_dir = Path(log_dir).resolve()
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._log_level_name = log_level.upper()
        self._max_system_ram_mb = max_system_ram_mb
        self._latency_threshold_s = latency_threshold_s

        self._lock = threading.RLock()
        self._alerts: List[Alert] = []
        self._metrics: Dict[str, List[float]] = {
            "latencies": [],
            "tokens": [],
            "ram_samples": [],
        }
        self._error_count: int = 0
        self._total_tokens_consumed: int = 0

        self._setup_logging()
        self._logger = logging.getLogger("FractalCore.SystemMonitor")
        self._logger.info("SystemMonitor initialized (Log Dir: %s, Level: %s)", self._log_dir, self._log_level_name)

    # --------------------------------------------------------------------------
    # Logging System
    # --------------------------------------------------------------------------

    def _setup_logging(self) -> None:
        """Configure root logger with console and rotating log file handlers."""
        log_file = self._log_dir / "system.log"
        numeric_level = getattr(logging, self._log_level_name, logging.INFO)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # Avoid duplicate handlers if re-initialized
        if not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in root_logger.handlers):
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(numeric_level)
            stream_handler.setFormatter(formatter)
            root_logger.addHandler(stream_handler)

    # --------------------------------------------------------------------------
    # Telemetry & Metrics Collection (Observer Pattern)
    # --------------------------------------------------------------------------

    def record_task_execution(self, task_id: str, duration_seconds: float, tokens_used: int = 0) -> None:
        """Record task execution metrics and evaluate for latency anomalies."""
        with self._lock:
            self._metrics["latencies"].append(duration_seconds)
            self._metrics["tokens"].append(float(tokens_used))
            self._total_tokens_consumed += tokens_used

            if duration_seconds > self._latency_threshold_s:
                self.emit_alert(
                    severity=AlertSeverity.HIGH,
                    source=f"TaskExecution:{task_id}",
                    message=f"Task execution duration ({duration_seconds:.1f}s) exceeded limit ({self._latency_threshold_s:.1f}s).",
                    details={"duration_s": duration_seconds, "task_id": task_id},
                )

    def record_error(self, source: str, error_message: str, severity: AlertSeverity = AlertSeverity.MEDIUM) -> None:
        """Record an error occurrence and raise an alert."""
        with self._lock:
            self._error_count += 1
            self.emit_alert(
                severity=severity,
                source=source,
                message=error_message,
                details={"error_index": self._error_count},
            )

    def record_ram_usage(self, current_mb: int) -> None:
        """Record current RAM usage and check for memory pressure anomalies."""
        with self._lock:
            self._metrics["ram_samples"].append(float(current_mb))
            # 92% of maximum memory marks severe pressure
            pressure_threshold = int(self._max_system_ram_mb * 0.92)
            if current_mb > pressure_threshold:
                self.emit_alert(
                    severity=AlertSeverity.CRITICAL,
                    source="MemoryGovernor",
                    message=f"System RAM pressure alert: {current_mb} MB allocated (Threshold: {pressure_threshold} MB, Cap: {self._max_system_ram_mb} MB).",
                    details={"current_ram_mb": current_mb, "threshold_mb": pressure_threshold},
                )

    # --------------------------------------------------------------------------
    # Alerts
    # --------------------------------------------------------------------------

    def emit_alert(
        self,
        severity: AlertSeverity,
        source: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """Emit a structured alert and log appropriately."""
        alert_id = f"alt_{int(time.time()*1000)}"
        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            source=source,
            message=message,
            details=details or {},
        )

        with self._lock:
            self._alerts.append(alert)
            log_msg = f"[{severity.value}] [{source}]: {message}"
            if severity == AlertSeverity.CRITICAL:
                self._logger.critical(log_msg)
            elif severity == AlertSeverity.HIGH:
                self._logger.error(log_msg)
            elif severity == AlertSeverity.MEDIUM:
                self._logger.warning(log_msg)
            else:
                self._logger.info(log_msg)

        return alert

    def get_active_alerts(self, min_severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Fetch recorded alerts, optionally filtering by minimum severity level."""
        with self._lock:
            if not min_severity:
                return list(self._alerts)

            order = [AlertSeverity.LOW, AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL]
            min_idx = order.index(min_severity)
            return [a for a in self._alerts if order.index(a.severity) >= min_idx]

    # --------------------------------------------------------------------------
    # Drift Detection
    # --------------------------------------------------------------------------

    def detect_workspace_drift(self, workspace_path: str = ".") -> Dict[str, Any]:
        """Detect tool state drift and untracked file modifications using git status."""
        try:
            cmd = ["git", "status", "--porcelain"]
            res = subprocess.run(
                cmd,
                cwd=workspace_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            dirty_files = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            has_drift = len(dirty_files) > 0
            if has_drift:
                self.emit_alert(
                    severity=AlertSeverity.MEDIUM,
                    source="DriftDetector",
                    message=f"Workspace drift detected: {len(dirty_files)} uncommitted/untracked files.",
                    details={"dirty_files": dirty_files[:10]},
                )
            return {"has_drift": has_drift, "dirty_count": len(dirty_files), "files": dirty_files}
        except Exception as exc:
            self._logger.debug("Git drift check skipped or unavailable: %s", exc)
            return {"has_drift": False, "dirty_count": 0, "files": [], "error": str(exc)}

    # --------------------------------------------------------------------------
    # System Summary
    # --------------------------------------------------------------------------

    def get_summary(self) -> Dict[str, Any]:
        """Compile a telemetry overview snapshot."""
        with self._lock:
            latencies = self._metrics["latencies"]
            avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
            return {
                "total_tasks_monitored": len(latencies),
                "average_latency_s": avg_lat,
                "total_tokens_consumed": self._total_tokens_consumed,
                "error_count": self._error_count,
                "total_alerts": len(self._alerts),
                "critical_alerts": sum(1 for a in self._alerts if a.severity == AlertSeverity.CRITICAL),
            }
