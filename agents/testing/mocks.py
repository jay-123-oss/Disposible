"""Specialized mocking agents: DataMocker and DependencyMocker."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.testing.exceptions import MockGenerationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Testing.Mocks")


# ==============================================================================
# L5 Specialized Mocking Agents
# ==============================================================================

class DataMocker(BaseAgent):
    """L5 agent generating synthetic schema data, mock users, and request/response payloads."""

    def __init__(
        self,
        name: str = "DataMocker",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["data_mocking", "fake_data_generation", "entity_mock_synthesis"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "T10_DATA_MOCKER",
        )
        self.register_tool("generate_data_mocks", self.generate_data_mocks)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DataMocker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        schema_name = payload.get("schema_name", "User")
        code = self.generate_data_mocks(schema_name)
        return {"status": "COMPLETED", "agent_id": self.agent_id, "mock_code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "mock_code" not in result or not result["mock_code"]:
            raise MockGenerationError("DataMocker produced empty mock code.")
        return result

    def cleanup(self) -> None:
        logger.debug("DataMocker %s cleaned up.", self.agent_id)

    def generate_data_mocks(self, schema_name: str = "User") -> str:
        """Generate Python mock classes for data models."""
        return (
            f"class Mock{schema_name}:\n"
            f"    \"\"\"Synthetic in-memory mock representing {schema_name} entity.\"\"\"\n"
            f"    def __init__(self, **kwargs):\n"
            f"        self.id = kwargs.get('id', 1)\n"
            f"        self.email = kwargs.get('email', 'mock_user@example.com')\n"
            f"        self.password_hash = kwargs.get('password_hash', '$2b$12$hashedpasswordplaceholder')\n"
            f"        self.is_active = kwargs.get('is_active', True)\n"
            f"        self.created_at = kwargs.get('created_at', datetime.utcnow())\n\n"
            f"    def to_dict(self) -> dict:\n"
            f"        return {{'id': self.id, 'email': self.email, 'is_active': self.is_active}}\n"
        )


class DependencyMocker(BaseAgent):
    """L5 agent generating asynchronous mocks for databases, HTTP clients, and file I/O."""

    def __init__(
        self,
        name: str = "DependencyMocker",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["dependency_mocking", "database_mock_generation", "external_service_mocking"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "T11_DEPENDENCY_MOCKER",
        )
        self.register_tool("generate_dependency_mocks", self.generate_dependency_mocks)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DependencyMocker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        code = self.generate_dependency_mocks()
        return {"status": "COMPLETED", "agent_id": self.agent_id, "mock_code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "mock_code" not in result or not result["mock_code"]:
            raise MockGenerationError("DependencyMocker produced empty dependency mock code.")
        return result

    def cleanup(self) -> None:
        logger.debug("DependencyMocker %s cleaned up.", self.agent_id)

    def generate_dependency_mocks(self) -> str:
        """Generate async mock database and external API client stubs."""
        return (
            "class MockDatabaseSession:\n"
            "    \"\"\"In-memory AsyncSession stub simulating SQLAlchemy database operations.\"\"\"\n"
            "    def __init__(self):\n"
            "        self.records = {}\n"
            "        self.committed = False\n"
            "        self.rolled_back = False\n\n"
            "    async def execute(self, statement, *args, **kwargs):\n"
            "        mock_result = MagicMock()\n"
            "        mock_result.scalars.return_value.first.return_value = list(self.records.values())[0] if self.records else None\n"
            "        mock_result.scalars.return_value.all.return_value = list(self.records.values())\n"
            "        return mock_result\n\n"
            "    def add(self, instance):\n"
            "        if not hasattr(instance, 'id') or instance.id is None:\n"
            "            instance.id = len(self.records) + 1\n"
            "        self.records[instance.id] = instance\n\n"
            "    async def commit(self):\n"
            "        self.committed = True\n\n"
            "    async def refresh(self, instance):\n"
            "        pass\n\n"
            "    async def rollback(self):\n"
            "        self.rolled_back = True\n\n"
            "    async def close(self):\n"
            "        pass\n"
        )
