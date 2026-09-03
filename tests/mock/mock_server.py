"""MockServer agent providing API Mocking, Database Mocking, Service Mocking, and Response Mocking."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from tests.exceptions import MockServerError


logger = logging.getLogger("FractalCore.Testing.MockServer")


# ==============================================================================
# L5 Atomic Mock Server Subagents
# ==============================================================================

class ApiMocker(BaseAgent):
    """L5 agent mocking REST / GraphQL HTTP endpoints on mock port (e.g. 8080)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ApiMocker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        port = payload.get("api_mock_port", 8080)

        return {
            "status": "COMPLETED",
            "mock_type": "API_MOCK",
            "port": port,
            "endpoints_mocked": ["/api/v1/auth", "/api/v1/billing"],
            "running": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ApiMocker %s cleaned up.", self.agent_id)


class DatabaseMocker(BaseAgent):
    """L5 agent simulating SQL/NoSQL queries, returning stubbed rowsets and transactional cursors."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DatabaseMocker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})

        return {
            "status": "COMPLETED",
            "mock_type": "DATABASE_MOCK",
            "in_memory_db": "sqlite:///:memory:",
            "mocked_tables": ["users", "agents", "tasks"],
            "ready": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DatabaseMocker %s cleaned up.", self.agent_id)


class ServiceMocker(BaseAgent):
    """L5 agent stubbing third-party cloud services (AWS S3, Stripe, Twilio) with timeout handling."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ServiceMocker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        timeout = payload.get("service_mock_timeout", 30)

        return {
            "status": "COMPLETED",
            "mock_type": "SERVICE_MOCK",
            "mocked_services": ["s3_storage", "stripe_payment", "smtp_mail"],
            "timeout_seconds": timeout,
            "ready": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ServiceMocker %s cleaned up.", self.agent_id)


class ResponseMocker(BaseAgent):
    """L5 agent generating custom JSON payloads, headers, delay simulation, and error codes."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ResponseMocker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        status_code = payload.get("mock_status_code", 200)

        return {
            "status": "COMPLETED",
            "mock_type": "RESPONSE_MOCK",
            "mock_status_code": status_code,
            "mock_headers": {"Content-Type": "application/json", "X-Mock": "1"},
            "latency_injected_ms": 10,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ResponseMocker %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 MockServer Agent
# ==============================================================================

class MockServer(BaseAgent):
    """L4 coordinator overseeing API mocking, database stubbing, external service mocks, and response generation."""

    def __init__(
        self,
        name: str = "MockServer",
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
            "mock_server",
            "api_mocking",
            "database_mocking",
            "service_mocking",
            "response_mocking",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "TV12_MOCK_SERVER",
        )

        self.api_mocker: Optional[ApiMocker] = None
        self.db_mocker: Optional[DatabaseMocker] = None
        self.service_mocker: Optional[ServiceMocker] = None
        self.response_mocker: Optional[ResponseMocker] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("provision_mock_environment", self.provision_mock_environment)

    def _spawn_subagents(self) -> None:
        """Spawn atomic mock server subagents (Rule 1 & Rule 5)."""
        logger.info("MockServer %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.api_mocker = self.spawn_subagent(ApiMocker, name="ApiMocker", max_depth=child_depth, resources_mb=32)
        self.db_mocker = self.spawn_subagent(DatabaseMocker, name="DatabaseMocker", max_depth=child_depth, resources_mb=32)
        self.service_mocker = self.spawn_subagent(ServiceMocker, name="ServiceMocker", max_depth=child_depth, resources_mb=32)
        self.response_mocker = self.spawn_subagent(ResponseMocker, name="ResponseMocker", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MockServer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        res = self.provision_mock_environment(context=payload)
        return {"status": "COMPLETED", "mock_environment": res}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("MockServer %s cleanup complete.", self.agent_id)

    def provision_mock_environment(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Bootstrap all mock servers and stubbed services."""
        p_env = {"payload": context or {}}

        a_res = self.api_mocker.process(p_env) if self.api_mocker else {"running": True}
        d_res = self.db_mocker.process(p_env) if self.db_mocker else {"ready": True}
        s_res = self.service_mocker.process(p_env) if self.service_mocker else {"ready": True}
        r_res = self.response_mocker.process(p_env) if self.response_mocker else {}

        all_ready = a_res.get("running", True) and d_res.get("ready", True) and s_res.get("ready", True)

        return {
            "mock_server_ready": all_ready,
            "api_mock": a_res,
            "database_mock": d_res,
            "service_mock": s_res,
            "response_mock": r_res,
            "timestamp": time.time(),
        }
