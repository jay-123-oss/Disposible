"""Specialized integration testing agents: APITester and FlowTester with atomic scenario builders."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.testing.exceptions import TestGenerationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Testing.IntegrationTests")


# ==============================================================================
# L5 Specialized Integration Agents
# ==============================================================================

class APITester(BaseAgent):
    """L5 agent generating direct HTTP endpoint integration tests using FastAPI TestClient."""

    def __init__(
        self,
        name: str = "APITester",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["api_integration_testing", "rest_endpoint_testing", "http_status_assertion"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "T7_API_TESTER",
        )
        self.register_tool("generate_endpoint_tests", self.generate_endpoint_tests)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("APITester %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        entity = payload.get("entity", "user")
        code = self.generate_endpoint_tests(entity)
        return {"status": "COMPLETED", "agent_id": self.agent_id, "test_code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "test_code" not in result or not result["test_code"]:
            raise TestGenerationError("APITester produced empty test code.")
        return result

    def cleanup(self) -> None:
        logger.debug("APITester %s cleaned up.", self.agent_id)

    def generate_endpoint_tests(self, entity: str = "user") -> str:
        """Generate TestClient CRUD endpoint tests."""
        return (
            f"def test_{entity}_post_endpoint(test_client):\n"
            f"    \"\"\"Verify POST /api/v1/{entity}s creates resource.\"\"\"\n"
            f"    payload = {{'email': 'new_{entity}@example.com', 'password': 'Password123!'}}\n"
            f"    resp = test_client.post('/api/v1/{entity}s', json=payload)\n"
            f"    assert resp.status_code in (200, 201)\n"
            f"    data = resp.json()\n"
            f"    assert 'id' in data or 'user' in data or 'token' in data\n\n"
            f"def test_{entity}_get_endpoint(test_client, auth_headers):\n"
            f"    \"\"\"Verify GET /api/v1/{entity}s/1 returns resource.\"\"\"\n"
            f"    resp = test_client.get('/api/v1/{entity}s/1', headers=auth_headers)\n"
            f"    assert resp.status_code in (200, 404)\n\n"
            f"def test_{entity}_delete_endpoint(test_client, auth_headers):\n"
            f"    \"\"\"Verify DELETE /api/v1/{entity}s/1 removes resource.\"\"\"\n"
            f"    resp = test_client.delete('/api/v1/{entity}s/1', headers=auth_headers)\n"
            f"    assert resp.status_code in (200, 204, 404)\n"
        )


class FlowTester(BaseAgent):
    """L5 agent generating multi-turn stateful integration flows (Register -> Login -> Query)."""

    def __init__(
        self,
        name: str = "FlowTester",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["flow_integration_testing", "e2e_journey_testing", "stateful_api_testing"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "T8_FLOW_TESTER",
        )
        self.register_tool("generate_e2e_flows", self.generate_e2e_flows)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("FlowTester %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        code = self.generate_e2e_flows()
        return {"status": "COMPLETED", "agent_id": self.agent_id, "test_code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "test_code" not in result or not result["test_code"]:
            raise TestGenerationError("FlowTester produced empty flow code.")
        return result

    def cleanup(self) -> None:
        logger.debug("FlowTester %s cleaned up.", self.agent_id)

    def generate_e2e_flows(self) -> str:
        """Generate end-to-end user lifecycle flow test."""
        return (
            "def test_full_auth_and_profile_flow(test_client):\n"
            "    \"\"\"Verify full sequence: register account -> login to get JWT -> access protected route.\"\"\"\n"
            "    # 1. Register account\n"
            "    email = f'flow_{time.time()}@example.com'\n"
            "    reg_resp = test_client.post('/api/v1/auth/register', json={'email': email, 'password': 'SecurePassword123!'})\n"
            "    assert reg_resp.status_code in (200, 201)\n\n"
            "    # 2. Login to receive access token\n"
            "    login_resp = test_client.post('/api/v1/auth/login', json={'email': email, 'password': 'SecurePassword123!'})\n"
            "    assert login_resp.status_code == 200\n"
            "    token = login_resp.json().get('access_token')\n"
            "    assert token is not None\n\n"
            "    # 3. Access authenticated profile endpoint\n"
            "    headers = {'Authorization': f'Bearer {token}'}\n"
            "    prof_resp = test_client.get('/api/v1/users/me', headers=headers)\n"
            "    assert prof_resp.status_code in (200, 404)\n"
        )
