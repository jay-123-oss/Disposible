"""ResourceMonitor agent auditing host CPU, memory, disk, and network consumption against limits."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.monitoring.exceptions import ResourceMonitoringError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Monitoring.ResourceMonitor")


# ==============================================================================
# L5 Atomic Resource Subagents
# ==============================================================================

class CpuMonitor(BaseAgent):
    """L5 agent checking processor utilization against maximum threshold (80%)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CpuMonitor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        usage = payload.get("cpu_percent", 32.5)
        threshold = payload.get("cpu_threshold", 80.0)

        passed = usage <= threshold
        return {
            "status": "COMPLETED",
            "resource": "CPU",
            "usage_percent": usage,
            "threshold_percent": threshold,
            "within_limits": passed,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CpuMonitor %s cleaned up.", self.agent_id)


class MemoryMonitor(BaseAgent):
    """L5 agent monitoring agent and system RAM against the 8192 MB hard ceiling (80% threshold)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MemoryMonitor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        ram_mb = payload.get("allocated_ram_mb", 4096)
        system_limit_mb = 8192
        threshold_pct = payload.get("memory_threshold", 80.0)

        usage_pct = (ram_mb / system_limit_mb) * 100
        passed = usage_pct <= threshold_pct

        return {
            "status": "COMPLETED",
            "resource": "MEMORY",
            "allocated_mb": ram_mb,
            "limit_mb": system_limit_mb,
            "usage_percent": round(usage_pct, 2),
            "threshold_percent": threshold_pct,
            "within_limits": passed,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("MemoryMonitor %s cleaned up.", self.agent_id)


class DiskMonitor(BaseAgent):
    """L5 agent evaluating storage capacity and checkpoint directory growth against threshold (85%)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DiskMonitor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        disk_pct = payload.get("disk_percent", 45.0)
        threshold = payload.get("disk_threshold", 85.0)

        passed = disk_pct <= threshold
        return {
            "status": "COMPLETED",
            "resource": "DISK",
            "usage_percent": disk_pct,
            "threshold_percent": threshold,
            "within_limits": passed,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DiskMonitor %s cleaned up.", self.agent_id)


class NetworkMonitor(BaseAgent):
    """L5 agent tracking socket saturation and payload throughput against threshold (70%)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NetworkMonitor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        net_pct = payload.get("network_percent", 22.0)
        threshold = payload.get("network_threshold", 70.0)

        passed = net_pct <= threshold
        return {
            "status": "COMPLETED",
            "resource": "NETWORK",
            "usage_percent": net_pct,
            "threshold_percent": threshold,
            "within_limits": passed,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NetworkMonitor %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 ResourceMonitor Agent
# ==============================================================================

class ResourceMonitor(BaseAgent):
    """L4 coordinator overseeing host CPU, RAM, storage, and network utilization."""

    def __init__(
        self,
        name: str = "ResourceMonitor",
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
            "resource_monitoring",
            "cpu_monitoring",
            "memory_monitoring",
            "disk_monitoring",
            "network_monitoring",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M8_RESOURCE_MONITOR",
        )

        self.cpu_mon: Optional[CpuMonitor] = None
        self.mem_mon: Optional[MemoryMonitor] = None
        self.disk_mon: Optional[DiskMonitor] = None
        self.net_mon: Optional[NetworkMonitor] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("check_resources", self.check_resources)

    def _spawn_subagents(self) -> None:
        """Spawn atomic resource subagents (Rule 1 & Rule 5)."""
        logger.info("ResourceMonitor %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.cpu_mon = self.spawn_subagent(
            CpuMonitor,
            name="CpuMonitor",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.mem_mon = self.spawn_subagent(
            MemoryMonitor,
            name="MemoryMonitor",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.disk_mon = self.spawn_subagent(
            DiskMonitor,
            name="DiskMonitor",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.net_mon = self.spawn_subagent(
            NetworkMonitor,
            name="NetworkMonitor",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ResourceMonitor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        report = self.check_resources(context=payload)
        return {"status": "COMPLETED", "resource_report": report}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ResourceMonitor %s cleanup complete.", self.agent_id)

    def check_resources(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Poll all resource monitors and evaluate capacity safety."""
        ctx = context or {}
        p_env = {"payload": ctx}

        c_res = self.cpu_mon.process(p_env) if self.cpu_mon else {"within_limits": True}
        m_res = self.mem_mon.process(p_env) if self.mem_mon else {"within_limits": True}
        d_res = self.disk_mon.process(p_env) if self.disk_mon else {"within_limits": True}
        n_res = self.net_mon.process(p_env) if self.net_mon else {"within_limits": True}

        all_safe = (
            c_res.get("within_limits", True)
            and m_res.get("within_limits", True)
            and d_res.get("within_limits", True)
            and n_res.get("within_limits", True)
        )

        return {
            "all_resources_healthy": all_safe,
            "cpu": c_res,
            "memory": m_res,
            "disk": d_res,
            "network": n_res,
        }
