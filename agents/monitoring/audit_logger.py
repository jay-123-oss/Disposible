"""AuditLogger agent recording immutable, structured security, action, performance, and error audit events."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from agents.monitoring.exceptions import AuditLogError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Monitoring.AuditLogger")


# ==============================================================================
# L5 Atomic Audit Subagents
# ==============================================================================

class ActionLogger(BaseAgent):
    """L5 agent logging user prompts, task assignments, and agent state mutations."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ActionLogger %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        actor = payload.get("actor", "SYSTEM")
        action = payload.get("action", "TASK_TRANSITION")
        metadata = payload.get("metadata", {})

        record = {
            "log_id": f"ACT_{uuid.uuid4().hex[:8]}",
            "type": "ACTION",
            "actor": actor,
            "action": action,
            "metadata": metadata,
            "timestamp": time.time(),
        }
        return {"status": "COMPLETED", "record": record}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ActionLogger %s cleaned up.", self.agent_id)


class SecurityLogger(BaseAgent):
    """L5 agent tracking authentication audits, token validations, and access policy enforcements."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SecurityLogger %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        event = payload.get("event", "AUTH_VERIFIED")
        severity = payload.get("severity", "LOW")
        details = payload.get("details", {})

        record = {
            "log_id": f"SEC_{uuid.uuid4().hex[:8]}",
            "type": "SECURITY",
            "event": event,
            "severity": severity,
            "details": details,
            "timestamp": time.time(),
        }
        return {"status": "COMPLETED", "record": record}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SecurityLogger %s cleaned up.", self.agent_id)


class PerformanceLogger(BaseAgent):
    """L5 agent logging elapsed latency durations, memory peaks, and task turnaround times."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PerformanceLogger %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        metric_name = payload.get("metric_name", "task_execution_ms")
        duration = payload.get("duration", 124.5)

        record = {
            "log_id": f"PERF_{uuid.uuid4().hex[:8]}",
            "type": "PERFORMANCE",
            "metric": metric_name,
            "value": duration,
            "timestamp": time.time(),
        }
        return {"status": "COMPLETED", "record": record}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PerformanceLogger %s cleaned up.", self.agent_id)


class ErrorLogger(BaseAgent):
    """L5 agent capturing exception events, traceback signatures, and failure contexts."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ErrorLogger %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        error_msg = payload.get("error_msg", "Unknown error")
        error_type = payload.get("error_type", "AgentError")

        record = {
            "log_id": f"ERR_{uuid.uuid4().hex[:8]}",
            "type": "ERROR",
            "error_type": error_type,
            "message": error_msg,
            "timestamp": time.time(),
        }
        return {"status": "COMPLETED", "record": record}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ErrorLogger %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 AuditLogger Agent
# ==============================================================================

class AuditLogger(BaseAgent):
    """L4 coordinator overseeing structured audit trails across actions, security, performance, and errors."""

    def __init__(
        self,
        name: str = "AuditLogger",
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
            "audit_logging",
            "action_logging",
            "security_logging",
            "performance_logging",
            "error_logging",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M6_AUDIT_LOGGER",
        )

        self._audit_log: List[Dict[str, Any]] = []
        self.action_log: Optional[ActionLogger] = None
        self.sec_log: Optional[SecurityLogger] = None
        self.perf_log: Optional[PerformanceLogger] = None
        self.err_log: Optional[ErrorLogger] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("log_event", self.log_event)
        self.register_tool("get_audit_trail", self.get_audit_trail)

    def _spawn_subagents(self) -> None:
        """Spawn atomic audit subagents (Rule 1 & Rule 5)."""
        logger.info("AuditLogger %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.action_log = self.spawn_subagent(
            ActionLogger,
            name="ActionLogger",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.sec_log = self.spawn_subagent(
            SecurityLogger,
            name="SecurityLogger",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.perf_log = self.spawn_subagent(
            PerformanceLogger,
            name="PerformanceLogger",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.err_log = self.spawn_subagent(
            ErrorLogger,
            name="ErrorLogger",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AuditLogger %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        log_type = payload.get("log_type", "ACTION")
        rec = self.log_event(log_type=log_type, data=payload)
        return {"status": "COMPLETED", "logged_record": rec}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AuditLogger %s cleanup complete.", self.agent_id)

    def log_event(self, log_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch audit record to specialized subagent and append to in-memory trail."""
        p_env = {"payload": data}
        rec: Dict[str, Any] = {}

        if log_type == "SECURITY" and self.sec_log:
            res = self.sec_log.process(p_env)
            rec = res.get("record", {})
        elif log_type == "PERFORMANCE" and self.perf_log:
            res = self.perf_log.process(p_env)
            rec = res.get("record", {})
        elif log_type == "ERROR" and self.err_log:
            res = self.err_log.process(p_env)
            rec = res.get("record", {})
        elif self.action_log:
            res = self.action_log.process(p_env)
            rec = res.get("record", {})

        if rec:
            self._audit_log.append(rec)
        return rec

    def get_audit_trail(self, log_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve historical audit events."""
        if log_type:
            filtered = [r for r in self._audit_log if r.get("type") == log_type]
            return filtered[-limit:]
        return self._audit_log[-limit:]
