"""ResourceManager agent controlling host memory allocation, worker thread concurrency, connections, and file handles."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from integration.exceptions import ResourceError


logger = logging.getLogger("FractalCore.Integration.ResourceManager")


# ==============================================================================
# L5 Atomic Resource Manager Subagents
# ==============================================================================

class MemoryManager(BaseAgent):
    """L5 agent checking system memory quotas against the 8192 MB hard threshold."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MemoryManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        requested_mb = payload.get("requested_mb", 128)
        current_mb = payload.get("current_mb", 4096)
        max_mb = payload.get("max_memory_mb", 8192)

        available = current_mb + requested_mb <= max_mb
        return {
            "status": "COMPLETED",
            "resource": "MEMORY",
            "allocated": available,
            "current_mb": current_mb,
            "max_mb": max_mb,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("MemoryManager %s cleaned up.", self.agent_id)


class ThreadManager(BaseAgent):
    """L5 agent managing concurrent worker thread pools against threshold (max 10)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ThreadManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        active_threads = payload.get("active_threads", 4)
        max_threads = payload.get("max_threads", 10)

        can_spawn = active_threads < max_threads
        return {
            "status": "COMPLETED",
            "resource": "THREADS",
            "active_threads": active_threads,
            "max_threads": max_threads,
            "can_spawn": can_spawn,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ThreadManager %s cleaned up.", self.agent_id)


class ConnectionManager(BaseAgent):
    """L5 agent monitoring open HTTP / socket connections against threshold (max 20)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ConnectionManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        active_conns = payload.get("active_conns", 5)
        max_conns = payload.get("max_connections", 20)

        can_connect = active_conns < max_conns
        return {
            "status": "COMPLETED",
            "resource": "CONNECTIONS",
            "active_connections": active_conns,
            "max_connections": max_conns,
            "can_connect": can_connect,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ConnectionManager %s cleaned up.", self.agent_id)


class FileManager(BaseAgent):
    """L5 agent managing open file descriptors and file write locks (max 100)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("FileManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        open_files = payload.get("open_files", 12)
        max_files = payload.get("max_files", 100)

        can_open = open_files < max_files
        return {
            "status": "COMPLETED",
            "resource": "FILES",
            "open_files": open_files,
            "max_files": max_files,
            "can_open": can_open,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("FileManager %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 ResourceManager Agent
# ==============================================================================

class ResourceManager(BaseAgent):
    """L4 coordinator overseeing host memory, thread pools, open connections, and file handles."""

    def __init__(
        self,
        name: str = "ResourceManager",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "resource_management",
            "memory_allocation",
            "thread_management",
            "connection_management",
            "file_management",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "IA13_RESOURCE_MANAGER",
        )

        self.mem_mgr: Optional[MemoryManager] = None
        self.th_mgr: Optional[ThreadManager] = None
        self.conn_mgr: Optional[ConnectionManager] = None
        self.file_mgr: Optional[FileManager] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("check_resource_quotas", self.check_resource_quotas)

    def _spawn_subagents(self) -> None:
        """Spawn atomic resource manager subagents (Rule 1 & Rule 5)."""
        logger.info("ResourceManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.mem_mgr = self.spawn_subagent(MemoryManager, name="MemoryManager", max_depth=child_depth, resources_mb=32)
        self.th_mgr = self.spawn_subagent(ThreadManager, name="ThreadManager", max_depth=child_depth, resources_mb=32)
        self.conn_mgr = self.spawn_subagent(ConnectionManager, name="ConnectionManager", max_depth=child_depth, resources_mb=32)
        self.file_mgr = self.spawn_subagent(FileManager, name="FileManager", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ResourceManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        res = self.check_resource_quotas(context=payload)
        return {"status": "COMPLETED", "resource_status": res}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ResourceManager %s cleanup complete.", self.agent_id)

    def check_resource_quotas(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Verify all four resource dimensions are within configured caps."""
        p_env = {"payload": context or {}}

        m_res = self.mem_mgr.process(p_env) if self.mem_mgr else {"allocated": True}
        t_res = self.th_mgr.process(p_env) if self.th_mgr else {"can_spawn": True}
        c_res = self.conn_mgr.process(p_env) if self.conn_mgr else {"can_connect": True}
        f_res = self.file_mgr.process(p_env) if self.file_mgr else {"can_open": True}

        all_ok = (
            m_res.get("allocated", True)
            and t_res.get("can_spawn", True)
            and c_res.get("can_connect", True)
            and f_res.get("can_open", True)
        )

        return {
            "all_quotas_valid": all_ok,
            "memory": m_res,
            "threads": t_res,
            "connections": c_res,
            "files": f_res,
        }
