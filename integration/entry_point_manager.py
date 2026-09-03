"""EntryPointManager agent dispatching execution between CLI, interactive, batch, and API entry points."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from integration.exceptions import InterfaceError


logger = logging.getLogger("FractalCore.Integration.EntryPointManager")


# ==============================================================================
# L5 Atomic Entry Point Subagents
# ==============================================================================

class CliEntryPoint(BaseAgent):
    """L5 agent handling single-shot command-line task executions."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CliEntryPoint %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        task = payload.get("task", "default task")

        return {"status": "COMPLETED", "mode": "CLI", "task": task, "handled": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CliEntryPoint %s cleaned up.", self.agent_id)


class InteractiveEntryPoint(BaseAgent):
    """L5 agent driving interactive REPL sessions."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("InteractiveEntryPoint %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})

        return {"status": "COMPLETED", "mode": "INTERACTIVE", "ready": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("InteractiveEntryPoint %s cleaned up.", self.agent_id)


class BatchEntryPoint(BaseAgent):
    """L5 agent processing batches of declarative task envelopes from JSON or YAML manifests."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("BatchEntryPoint %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        tasks = payload.get("tasks", [])

        return {"status": "COMPLETED", "mode": "BATCH", "batch_size": len(tasks), "queued": len(tasks)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("BatchEntryPoint %s cleaned up.", self.agent_id)


class ApiEntryPoint(BaseAgent):
    """L5 agent managing HTTP / FastAPI server harnesses for remote task submissions."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ApiEntryPoint %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        port = payload.get("port", 8000)

        return {"status": "COMPLETED", "mode": "API", "port": port, "server_ready": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ApiEntryPoint %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 EntryPointManager Agent
# ==============================================================================

class EntryPointManager(BaseAgent):
    """L4 coordinator overseeing execution entry points (CLI, Interactive REPL, Batch, and API)."""

    def __init__(
        self,
        name: str = "EntryPointManager",
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
            "entry_point_management",
            "cli_entry",
            "interactive_entry",
            "batch_entry",
            "api_entry",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "IA6_ENTRY_POINT_MANAGER",
        )

        self.cli_ep: Optional[CliEntryPoint] = None
        self.interactive_ep: Optional[InteractiveEntryPoint] = None
        self.batch_ep: Optional[BatchEntryPoint] = None
        self.api_ep: Optional[ApiEntryPoint] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("dispatch_entry_point", self.dispatch_entry_point)

    def _spawn_subagents(self) -> None:
        """Spawn atomic entry point subagents (Rule 1 & Rule 5)."""
        logger.info("EntryPointManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.cli_ep = self.spawn_subagent(CliEntryPoint, name="CliEntryPoint", max_depth=child_depth, resources_mb=32)
        self.interactive_ep = self.spawn_subagent(InteractiveEntryPoint, name="InteractiveEntryPoint", max_depth=child_depth, resources_mb=32)
        self.batch_ep = self.spawn_subagent(BatchEntryPoint, name="BatchEntryPoint", max_depth=child_depth, resources_mb=32)
        self.api_ep = self.spawn_subagent(ApiEntryPoint, name="ApiEntryPoint", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("EntryPointManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        mode = payload.get("mode", "CLI")
        res = self.dispatch_entry_point(mode=mode, data=payload)
        return {"status": "COMPLETED", "entry_point_result": res}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("EntryPointManager %s cleanup complete.", self.agent_id)

    def dispatch_entry_point(self, mode: str = "CLI", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Route to requested entry point worker."""
        p_env = {"payload": data or {}}

        if mode.upper() == "INTERACTIVE" and self.interactive_ep:
            res = self.interactive_ep.process(p_env)
        elif mode.upper() == "BATCH" and self.batch_ep:
            res = self.batch_ep.process(p_env)
        elif mode.upper() == "API" and self.api_ep:
            res = self.api_ep.process(p_env)
        elif self.cli_ep:
            res = self.cli_ep.process(p_env)
        else:
            res = {"handled": False, "mode": mode}

        return res
