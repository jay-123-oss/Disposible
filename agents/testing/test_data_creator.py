"""TestDataCreator coordinating pytest fixtures, test database seeds, and test environments."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.testing.exceptions import TestDataCreationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Testing.TestDataCreator")


# ==============================================================================
# L5 Specialized Data Generators
# ==============================================================================

class FixtureGenerator(BaseAgent):
    """L5 agent generating reusable pytest fixtures with teardown and scope configuration."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("FixtureGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        code = (
            "@pytest.fixture(scope='function')\n"
            "def test_user_payload():\n"
            "    \"\"\"Yield a fresh deterministic user payload for test isolation.\"\"\"\n"
            "    return {\n"
            "        'email': 'fixture_user@example.com',\n"
            "        'password': 'StrongPassword!2026',\n"
            "        'full_name': 'Fixture Test User',\n"
            "    }\n\n"
            "@pytest.fixture(scope='function')\n"
            "def test_session_token():\n"
            "    \"\"\"Return a mock authenticated bearer token.\"\"\"\n"
            "    return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-IDcSemACt8x4iTMCda8Yhe3iZaWbvV5XKSTbuAn0M'\n"
        )
        return {"status": "COMPLETED", "code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result:
            raise TestDataCreationError("FixtureGenerator produced empty code.")
        return result

    def cleanup(self) -> None:
        logger.debug("FixtureGenerator %s cleaned up.", self.agent_id)


class SeedGenerator(BaseAgent):
    """L5 agent generating deterministic database seed datasets."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SeedGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        count = payload.get("count", 5)
        users = [
            {"id": i, "email": f"seed_user_{i}@example.com", "is_active": True}
            for i in range(1, count + 1)
        ]
        code = (
            f"SEED_USERS = {users}\n\n"
            "async def seed_database(db_session):\n"
            "    \"\"\"Populate test database with predefined test records.\"\"\"\n"
            "    for u in SEED_USERS:\n"
            "        await db_session.execute(User.__table__.insert().values(**u))\n"
            "    await db_session.commit()\n"
        )
        return {"status": "COMPLETED", "code": code, "records_count": count}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result:
            raise TestDataCreationError("SeedGenerator produced empty seed code.")
        return result

    def cleanup(self) -> None:
        logger.debug("SeedGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 TestDataCreator Agent
# ==============================================================================

class TestDataCreator(BaseAgent):
    """L4 coordinator managing fixtures, database seed scripts, and isolated test configurations."""

    def __init__(
        self,
        name: str = "TestDataCreator",
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
            "test_data_creation",
            "fixture_generation",
            "database_seeding",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "T12_TEST_DATA_CREATOR",
        )

        self.fixture_generator: Optional[FixtureGenerator] = None
        self.seed_generator: Optional[SeedGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_fixtures_and_seeds", self.generate_fixtures_and_seeds)

    def _spawn_subagents(self) -> None:
        """Spawn FixtureGenerator and SeedGenerator (Rule 1 & Rule 5)."""
        logger.info("TestDataCreator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.fixture_generator = self.spawn_subagent(
            FixtureGenerator,
            name="FixtureGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.seed_generator = self.spawn_subagent(
            SeedGenerator,
            name="SeedGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TestDataCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        data = self.generate_fixtures_and_seeds()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "test_data_bundle": data,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        bundle = result.get("test_data_bundle")
        if not bundle or not bundle.get("conftest_code"):
            raise TestDataCreationError("TestDataCreator produced incomplete data bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("TestDataCreator %s cleanup complete.", self.agent_id)

    def generate_fixtures_and_seeds(self) -> Dict[str, Any]:
        """Synthesize conftest.py fixtures and seed scripts."""
        blocks: List[str] = [
            "import pytest",
            "",
        ]

        if self.fixture_generator:
            fix_res = self.fixture_generator.process({})
            blocks.append(fix_res["code"])

        if self.seed_generator:
            seed_res = self.seed_generator.process({"payload": {"count": 5}})
            blocks.append(seed_res["code"])

        conftest_code = "\n\n".join(blocks)
        return {
            "conftest_code": conftest_code,
            "fixtures": ["test_user_payload", "test_session_token", "seed_database"],
        }
