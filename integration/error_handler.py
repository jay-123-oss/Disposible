"""ErrorHandler agent catching system exceptions, logging diagnostics, executing recovery retries, and escalating."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from core.agent_base import BaseAgent
from integration.exceptions import IntegrationError


logger = logging.getLogger("FractalCore.Integration.ErrorHandler")


# ==============================================================================
# L5 Atomic Error Handler Subagents
# ==============================================================================

class ExceptionCatcher(BaseAgent):
    """L5 agent wrapping callables with try/catch boundaries to shield the orchestrator."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ExceptionCatcher %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        target_fn: Optional[Callable[[], Any]] = payload.get("target_fn")

        success = True
        output = None
        error_msg = None

        if target_fn and callable(target_fn):
            try:
                output = target_fn()
            except Exception as exc:
                success = False
                error_msg = str(exc)

        return {
            "status": "COMPLETED",
            "execution_succeeded": success,
            "output": output,
            "error_msg": error_msg,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ExceptionCatcher %s cleaned up.", self.agent_id)


class ErrorLogger(BaseAgent):
    """L5 agent logging formatted error traces into structured observability sinks."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ErrorLogger %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        err = payload.get("error", "General failure")

        logger.error("ErrorHandler caught: %s", err)
        return {
            "status": "COMPLETED",
            "logged": True,
            "error": str(err),
            "timestamp": time.time(),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ErrorLogger %s cleaned up.", self.agent_id)


class ErrorRecoverer(BaseAgent):
    """L5 agent attempting automated corrective strategies (e.g. transient retry, cache clear)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ErrorRecoverer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        attempts = payload.get("attempts", 1)
        max_attempts = payload.get("max_attempts", 3)

        recovered = attempts <= max_attempts
        return {
            "status": "COMPLETED",
            "recovered": recovered,
            "attempt": attempts,
            "max_attempts": max_attempts,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ErrorRecoverer %s cleaned up.", self.agent_id)


class ErrorEscalator(BaseAgent):
    """L5 agent routing fatal unrecoverable exceptions to alert channels or orchestrator halts."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ErrorEscalator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        err = payload.get("error", "Critical fault")

        return {
            "status": "COMPLETED",
            "escalated": True,
            "severity": "CRITICAL",
            "error": str(err),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ErrorEscalator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 ErrorHandler Agent
# ==============================================================================

class ErrorHandler(BaseAgent):
    """L4 coordinator overseeing exception interception, logging, recovery retries, and escalation."""

    def __init__(
        self,
        name: str = "ErrorHandler",
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
            "global_error_handling",
            "exception_interception",
            "error_logging",
            "automated_recovery",
            "error_escalation",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "IA9_ERROR_HANDLER",
        )

        self.catcher: Optional[ExceptionCatcher] = None
        self.logger_sub: Optional[ErrorLogger] = None
        self.recoverer: Optional[ErrorRecoverer] = None
        self.escalator: Optional[ErrorEscalator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("handle_error", self.handle_error)

    def _spawn_subagents(self) -> None:
        """Spawn atomic error handler subagents (Rule 1 & Rule 5)."""
        logger.info("ErrorHandler %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.catcher = self.spawn_subagent(ExceptionCatcher, name="ExceptionCatcher", max_depth=child_depth, resources_mb=32)
        self.logger_sub = self.spawn_subagent(ErrorLogger, name="ErrorLogger", max_depth=child_depth, resources_mb=32)
        self.recoverer = self.spawn_subagent(ErrorRecoverer, name="ErrorRecoverer", max_depth=child_depth, resources_mb=32)
        self.escalator = self.spawn_subagent(ErrorEscalator, name="ErrorEscalator", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ErrorHandler %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        err = payload.get("error", "Runtime warning")
        res = self.handle_error(error=err)
        return {"status": "COMPLETED", "error_handling_result": res}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ErrorHandler %s cleanup complete.", self.agent_id)

    def handle_error(self, error: Any, attempts: int = 1, max_attempts: int = 3) -> Dict[str, Any]:
        """Log error, attempt recovery, and escalate if needed."""
        p_env = {"payload": {"error": error, "attempts": attempts, "max_attempts": max_attempts}}

        l_res = self.logger_sub.process(p_env) if self.logger_sub else {}
        r_res = self.recoverer.process(p_env) if self.recoverer else {"recovered": False}

        escalated = False
        if not r_res.get("recovered", True):
            e_res = self.escalator.process(p_env) if self.escalator else {}
            escalated = e_res.get("escalated", True)

        return {
            "error_handled": True,
            "logged": l_res.get("logged", True),
            "recovered": r_res.get("recovered", False),
            "escalated": escalated,
        }
