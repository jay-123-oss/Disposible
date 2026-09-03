"""MetricsCollector agent aggregating system, application, agent, and token consumption metrics."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from agents.monitoring.exceptions import MetricsCollectionError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Monitoring.MetricsCollector")


# ==============================================================================
# L5 Atomic Metrics Subagents
# ==============================================================================

class SystemMetricsCollector(BaseAgent):
    """L5 agent sampling host CPU, memory, disk, and socket statistics."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SystemMetricsCollector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        # Simulated lightweight metrics extraction without external psutil dependencies
        metrics = {
            "cpu_percent": 18.5,
            "system_ram_allocated_mb": 512,
            "system_ram_limit_mb": 8192,
            "disk_usage_percent": 42.0,
            "timestamp": time.time(),
        }
        return {"status": "COMPLETED", "system_metrics": metrics}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SystemMetricsCollector %s cleaned up.", self.agent_id)


class ApplicationMetricsCollector(BaseAgent):
    """L5 agent capturing application throughput, error rates, and latency distributions."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ApplicationMetricsCollector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        metrics = {
            "throughput_rps": payload.get("rps", 120.0),
            "avg_response_time_ms": payload.get("response_time_ms", 45.2),
            "p95_response_time_ms": payload.get("p95_ms", 92.4),
            "error_rate_percent": payload.get("error_rate", 0.05),
        }
        return {"status": "COMPLETED", "application_metrics": metrics}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ApplicationMetricsCollector %s cleaned up.", self.agent_id)


class AgentMetricsCollector(BaseAgent):
    """L5 agent monitoring active agent counts, task queue lengths, and task completion rates."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AgentMetricsCollector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        active_count = payload.get("active_agents", 14)
        completed_tasks = payload.get("completed_tasks", 10)

        metrics = {
            "active_agent_count": active_count,
            "completed_task_count": completed_tasks,
            "avg_depth": 3.2,
            "task_success_rate": 0.98,
        }
        return {"status": "COMPLETED", "agent_metrics": metrics}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AgentMetricsCollector %s cleaned up.", self.agent_id)


class TokenMetricsCollector(BaseAgent):
    """L5 agent tracking prompt tokens, completion tokens, and token budget thresholds."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TokenMetricsCollector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        prompt_tokens = payload.get("prompt_tokens", 850)
        completion_tokens = payload.get("completion_tokens", 420)
        max_limit = 4096

        total = prompt_tokens + completion_tokens
        metrics = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total,
            "max_token_limit": max_limit,
            "utilization_percent": round((total / max_limit) * 100, 2),
        }
        return {"status": "COMPLETED", "token_metrics": metrics}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TokenMetricsCollector %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 MetricsCollector Agent
# ==============================================================================

class MetricsCollector(BaseAgent):
    """L4 coordinator overseeing system, application, agent, and token metrics collection."""

    def __init__(
        self,
        name: str = "MetricsCollector",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "metrics_collection",
            "system_metrics",
            "application_metrics",
            "agent_metrics",
            "token_metrics",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M3_METRICS_COLLECTOR",
        )

        self.sys_collector: Optional[SystemMetricsCollector] = None
        self.app_collector: Optional[ApplicationMetricsCollector] = None
        self.agent_collector: Optional[AgentMetricsCollector] = None
        self.token_collector: Optional[TokenMetricsCollector] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("collect_all_metrics", self.collect_all_metrics)

    def _spawn_subagents(self) -> None:
        """Spawn atomic metrics subagents (Rule 1 & Rule 5)."""
        logger.info("MetricsCollector %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.sys_collector = self.spawn_subagent(
            SystemMetricsCollector,
            name="SystemMetricsCollector",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.app_collector = self.spawn_subagent(
            ApplicationMetricsCollector,
            name="ApplicationMetricsCollector",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.agent_collector = self.spawn_subagent(
            AgentMetricsCollector,
            name="AgentMetricsCollector",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.token_collector = self.spawn_subagent(
            TokenMetricsCollector,
            name="TokenMetricsCollector",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MetricsCollector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        snapshot = self.collect_all_metrics(context=payload)
        return {"status": "COMPLETED", "metrics_snapshot": snapshot}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "metrics_snapshot" not in result:
            raise MetricsCollectionError("MetricsCollector missing snapshot.")
        return result

    def cleanup(self) -> None:
        logger.debug("MetricsCollector %s cleanup complete.", self.agent_id)

    def collect_all_metrics(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Collect combined metrics across all four domains."""
        ctx = context or {}
        p_env = {"payload": ctx}

        sys_res = self.sys_collector.process(p_env) if self.sys_collector else {"system_metrics": {}}
        app_res = self.app_collector.process(p_env) if self.app_collector else {"application_metrics": {}}
        agent_res = self.agent_collector.process(p_env) if self.agent_collector else {"agent_metrics": {}}
        tok_res = self.token_collector.process(p_env) if self.token_collector else {"token_metrics": {}}

        return {
            "timestamp": time.time(),
            "system": sys_res.get("system_metrics"),
            "application": app_res.get("application_metrics"),
            "agent": agent_res.get("agent_metrics"),
            "token": tok_res.get("token_metrics"),
        }
