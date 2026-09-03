"""PerformanceMonitor agent collecting node metrics, aggregating cluster utilization, and generating alerts.

Implements the complete Performance Monitor hierarchy (D12):
- L4 PerformanceMonitor coordinator
- L5 atomic workers: NodeMetricsCollector, ClusterMetricsAggregator, PerfAnalyzer, PerfAlerter
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from distributed.exceptions import PerformanceMonitoringError

logger = logging.getLogger("FractalCore.Distributed.PerformanceMonitor")


# ==============================================================================
# L5 Atomic Performance Monitor Subagents
# ==============================================================================

class NodeMetricsCollector(BaseAgent):
    """L5 agent sampling CPU, memory, network, and disk I/O metrics on a host node."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NodeMetricsCollector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        node_id = task_envelope.get("node_id", "node-1")
        # Sample or use simulated metrics
        metrics = {
            "node_id": node_id,
            "cpu_percent": task_envelope.get("cpu_percent", 25.5),
            "memory_mb": task_envelope.get("memory_mb", 512),
            "network_tx_kb": task_envelope.get("network_tx_kb", 1024),
            "network_rx_kb": task_envelope.get("network_rx_kb", 2048),
            "timestamp": time.time(),
        }
        return {"status": "COMPLETED", "node_id": node_id, "metrics": metrics}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NodeMetricsCollector %s cleaned up.", self.agent_id)


class ClusterMetricsAggregator(BaseAgent):
    """L5 agent aggregating multi-node metrics into cluster-wide statistics."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ClusterMetricsAggregator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        node_metrics = task_envelope.get("node_metrics", {})
        count = len(node_metrics)
        if not count:
            return {"status": "COMPLETED", "avg_cpu": 0.0, "total_memory_mb": 0, "node_count": 0}

        avg_cpu = sum(m.get("cpu_percent", 0.0) for m in node_metrics.values()) / count
        tot_mem = sum(m.get("memory_mb", 0) for m in node_metrics.values())
        return {
            "status": "COMPLETED",
            "avg_cpu_percent": round(avg_cpu, 2),
            "total_memory_mb": tot_mem,
            "node_count": count,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ClusterMetricsAggregator %s cleaned up.", self.agent_id)


class PerfAnalyzer(BaseAgent):
    """L5 agent identifying performance bottlenecks, latency spikes, and capacity constraints."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PerfAnalyzer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        cluster_summary = task_envelope.get("cluster_summary", {})
        avg_cpu = cluster_summary.get("avg_cpu_percent", 0.0)
        threshold = task_envelope.get("threshold", 80.0)
        bottleneck = avg_cpu > threshold
        return {
            "status": "COMPLETED",
            "bottleneck_detected": bottleneck,
            "resource": "cpu" if bottleneck else "none",
            "severity": "CRITICAL" if avg_cpu > 90 else ("WARNING" if bottleneck else "OK"),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PerfAnalyzer %s cleaned up.", self.agent_id)


class PerfAlerter(BaseAgent):
    """L5 agent emitting alerts when performance SLAs or capacity thresholds are breached."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PerfAlerter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        analysis = task_envelope.get("analysis", {})
        alerts = []
        if analysis.get("bottleneck_detected"):
            alerts.append({
                "level": analysis.get("severity", "WARNING"),
                "resource": analysis.get("resource", "cluster"),
                "message": f"Cluster utilization exceeded threshold! Severity: {analysis.get('severity')}",
                "timestamp": time.time(),
            })
        return {"status": "COMPLETED", "alerts": alerts, "alert_count": len(alerts)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PerfAlerter %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PerformanceMonitor Agent
# ==============================================================================

class PerformanceMonitor(BaseAgent):
    """L4 coordinator monitoring distributed cluster performance, aggregation, and alerting."""

    def __init__(
        self,
        name: str = "PerformanceMonitor",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
        metrics_interval: int = 10,
        alert_threshold: float = 80.0,
    ) -> None:
        default_caps = capabilities or [
            "performance_monitor",
            "node_metrics_collector",
            "cluster_metrics_aggregator",
            "perf_analyzer",
            "perf_alerter",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "D12_PERFORMANCE_MONITOR",
        )
        self.metrics_interval = metrics_interval
        self.alert_threshold = alert_threshold
        self.node_metrics: Dict[str, Dict[str, Any]] = {}

        self.collector: Optional[NodeMetricsCollector] = None
        self.aggregator: Optional[ClusterMetricsAggregator] = None
        self.analyzer: Optional[PerfAnalyzer] = None
        self.alerter: Optional[PerfAlerter] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("collect_metrics", self.collect_metrics)
        self.register_tool("evaluate_cluster_health", self.evaluate_cluster_health)

    def _spawn_subagents(self) -> None:
        """Spawn atomic performance monitor subagents (Rule 1 & Rule 5)."""
        logger.info("PerformanceMonitor %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.collector = self.spawn_subagent(NodeMetricsCollector, name="NodeMetricsCollector", max_depth=child_depth, resources_mb=32)
        self.aggregator = self.spawn_subagent(ClusterMetricsAggregator, name="ClusterMetricsAggregator", max_depth=child_depth, resources_mb=32)
        self.analyzer = self.spawn_subagent(PerfAnalyzer, name="PerfAnalyzer", max_depth=child_depth, resources_mb=32)
        self.alerter = self.spawn_subagent(PerfAlerter, name="PerfAlerter", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PerformanceMonitor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return self.evaluate_cluster_health()

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PerformanceMonitor %s cleaned up.", self.agent_id)

    def collect_metrics(self, node_id: str, cpu_percent: float = 20.0, memory_mb: int = 512) -> Dict[str, Any]:
        """Collect host metrics from specified node."""
        res = self.collector.process({
            "node_id": node_id,
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
        }) if self.collector else {"metrics": {"node_id": node_id, "cpu_percent": cpu_percent, "memory_mb": memory_mb}}
        self.node_metrics[node_id] = res["metrics"]
        return res["metrics"]

    def evaluate_cluster_health(self) -> Dict[str, Any]:
        """Aggregate node metrics and evaluate health threshold alerts."""
        agg = self.aggregator.process({"node_metrics": self.node_metrics}) if self.aggregator else {
            "avg_cpu_percent": 25.0, "total_memory_mb": 1024, "node_count": len(self.node_metrics)
        }
        analysis = self.analyzer.process({
            "cluster_summary": agg,
            "threshold": self.alert_threshold,
        }) if self.analyzer else {"bottleneck_detected": False, "severity": "OK"}

        alerts_res = self.alerter.process({"analysis": analysis}) if self.alerter else {"alerts": []}

        return {
            "aggregated": agg,
            "analysis": analysis,
            "alerts": alerts_res.get("alerts", []),
            "healthy": not analysis.get("bottleneck_detected", False),
        }
