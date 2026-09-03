"""IntegrationTestCreator coordinating API endpoint tests and stateful E2E user flows."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.testing.exceptions import TestGenerationError
from agents.testing.integration_tests import (
    APITester,
    FlowTester,
)
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Testing.IntegrationTestCreator")


class IntegrationTestCreator(BaseAgent):
    """L4 coordinator generating end-to-end integration tests using FastAPI TestClient."""

    def __init__(
        self,
        name: str = "IntegrationTestCreator",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 192,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "integration_test_generation",
            "api_flow_orchestration",
            "e2e_test_synthesis",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "T6_INTEGRATION_TEST_CREATOR",
        )

        self.api_tester: Optional[APITester] = None
        self.flow_tester: Optional[FlowTester] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_integration_subagents()

        self.register_tool("generate_integration_tests", self.generate_integration_tests)
        self.register_tool("generate_flow_tests", self.generate_flow_tests)

    def _spawn_integration_subagents(self) -> None:
        """Spawn specialized integration testing subagents (APITester, FlowTester)."""
        logger.info("IntegrationTestCreator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.api_tester = self.spawn_subagent(
            APITester,
            name="APITester",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.flow_tester = self.spawn_subagent(
            FlowTester,
            name="FlowTester",
            max_depth=child_depth,
            resources_mb=128,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("IntegrationTestCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        entity = payload.get("entity", "user")

        suite = self.generate_integration_tests(api_spec={"entity": entity})
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "integration_test_suite": suite,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        suite = result.get("integration_test_suite")
        if not suite or not suite.get("full_test_code"):
            raise TestGenerationError("IntegrationTestCreator produced incomplete test suite.")
        return result

    def cleanup(self) -> None:
        logger.debug("IntegrationTestCreator %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def generate_flow_tests(self, flows: Optional[List[str]] = None) -> str:
        """Generate multi-turn stateful journey tests."""
        if self.flow_tester:
            res = self.flow_tester.process({})
            return res["test_code"]
        return "# Flow tests placeholder"

    def generate_integration_tests(self, api_spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synthesize complete integration test module."""
        entity = (api_spec or {}).get("entity", "user")

        blocks: List[str] = [
            "import time",
            "import pytest",
            "from fastapi.testclient import TestClient",
            "from app.main import app",
            "",
            "@pytest.fixture",
            "def test_client():",
            "    return TestClient(app)",
            "",
            "@pytest.fixture",
            "def auth_headers():",
            "    return {'Authorization': 'Bearer TEST_SYNTHETIC_JWT_TOKEN'}",
            "",
        ]

        if self.api_tester:
            api_res = self.api_tester.process({"payload": {"entity": entity}})
            blocks.append(api_res["test_code"])

        if self.flow_tester:
            flow_res = self.flow_tester.process({})
            blocks.append(flow_res["test_code"])

        full_code = "\n\n".join(blocks)
        return {
            "entity": entity,
            "framework": "pytest-testclient",
            "full_test_code": full_code,
        }
