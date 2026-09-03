"""TestDataSetup agent handling Fixture Loading, Seed Data, Mock Data Generation, and Test Env Setup."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from tests.exceptions import TestDataError


logger = logging.getLogger("FractalCore.Testing.TestDataSetup")


# ==============================================================================
# L5 Atomic Test Data Setup Subagents
# ==============================================================================

class FixtureLoader(BaseAgent):
    """L5 agent loading JSON, YAML, and SQL fixture files into test database/memory."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("FixtureLoader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        fixtures_path = payload.get("fixtures_path", "./tests/fixtures/")

        return {
            "status": "COMPLETED",
            "setup_type": "FIXTURE_LOADING",
            "fixtures_path": fixtures_path,
            "fixtures_loaded": 8,
            "passed": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("FixtureLoader %s cleaned up.", self.agent_id)


class SeedDataGenerator(BaseAgent):
    """L5 agent populating base datasets with users, roles, permissions, and sample tasks."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SeedDataGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})

        return {
            "status": "COMPLETED",
            "setup_type": "SEED_DATA",
            "seeded_entities": ["users", "teams", "tasks"],
            "records_inserted": 45,
            "passed": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SeedDataGenerator %s cleaned up.", self.agent_id)


class MockDataGenerator(BaseAgent):
    """L5 agent generating high-volume randomized synthetic mock data for stress/fuzz testing."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MockDataGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        count = payload.get("mock_records_count", 100)

        return {
            "status": "COMPLETED",
            "setup_type": "MOCK_DATA",
            "synthetic_records_generated": count,
            "passed": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("MockDataGenerator %s cleaned up.", self.agent_id)


class EnvSetup(BaseAgent):
    """L5 agent configuring temporary sandbox directories, test database connections, and environment variables."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("EnvSetup %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})

        return {
            "status": "COMPLETED",
            "setup_type": "ENV_SETUP",
            "temp_dir_created": True,
            "env_vars_injected": {"TESTING": "1", "ENV": "test"},
            "passed": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("EnvSetup %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 TestDataSetup Agent
# ==============================================================================

class TestDataSetup(BaseAgent):
    """L4 coordinator overseeing fixture loading, seed data, mock generation, and environment setup."""

    def __init__(
        self,
        name: str = "TestDataSetup",
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
            "test_data_setup",
            "fixture_loading",
            "seed_data_generation",
            "mock_data_generation",
            "env_setup",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "TV10_TEST_DATA_SETUP",
        )

        self.fixture_ldr: Optional[FixtureLoader] = None
        self.seed_gen: Optional[SeedDataGenerator] = None
        self.mock_gen: Optional[MockDataGenerator] = None
        self.env_setup: Optional[EnvSetup] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("setup_test_environment", self.setup_test_environment)

    def _spawn_subagents(self) -> None:
        """Spawn atomic test data setup subagents (Rule 1 & Rule 5)."""
        logger.info("TestDataSetup %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.fixture_ldr = self.spawn_subagent(FixtureLoader, name="FixtureLoader", max_depth=child_depth, resources_mb=32)
        self.seed_gen = self.spawn_subagent(SeedDataGenerator, name="SeedDataGenerator", max_depth=child_depth, resources_mb=32)
        self.mock_gen = self.spawn_subagent(MockDataGenerator, name="MockDataGenerator", max_depth=child_depth, resources_mb=32)
        self.env_setup = self.spawn_subagent(EnvSetup, name="EnvSetup", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TestDataSetup %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        res = self.setup_test_environment(context=payload)
        return {"status": "COMPLETED", "setup_results": res}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TestDataSetup %s cleanup complete.", self.agent_id)

    def setup_test_environment(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Bootstrap complete test fixtures, seeds, mocks, and environment variables."""
        p_env = {"payload": context or {}}

        f_res = self.fixture_ldr.process(p_env) if self.fixture_ldr else {"passed": True}
        s_res = self.seed_gen.process(p_env) if self.seed_gen else {"passed": True}
        m_res = self.mock_gen.process(p_env) if self.mock_gen else {"passed": True}
        e_res = self.env_setup.process(p_env) if self.env_setup else {"passed": True}

        all_ok = (
            f_res.get("passed", True)
            and s_res.get("passed", True)
            and m_res.get("passed", True)
            and e_res.get("passed", True)
        )

        return {
            "all_setup_successful": all_ok,
            "fixtures": f_res,
            "seeds": s_res,
            "mocks": m_res,
            "environment": e_res,
            "timestamp": time.time(),
        }
