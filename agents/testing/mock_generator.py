"""MockGenerator coordinating data and dependency mock synthesis."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.testing.exceptions import MockGenerationError
from agents.testing.mocks import (
    DataMocker,
    DependencyMocker,
)
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Testing.MockGenerator")


class MockGenerator(BaseAgent):
    """L4 coordinator generating mock datasets, fixtures, and external service stubs."""

    def __init__(
        self,
        name: str = "MockGenerator",
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
            "mock_generation",
            "fixture_synthesis",
            "dependency_isolation",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "T9_MOCK_GENERATOR",
        )

        self.data_mocker: Optional[DataMocker] = None
        self.dependency_mocker: Optional[DependencyMocker] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_mock_subagents()

        self.register_tool("generate_mocks", self.generate_mocks)
        self.register_tool("generate_data_mocks", self.generate_data_mocks)

    def _spawn_mock_subagents(self) -> None:
        """Spawn DataMocker and DependencyMocker (Rule 1 & Rule 5)."""
        logger.info("MockGenerator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.data_mocker = self.spawn_subagent(
            DataMocker,
            name="DataMocker",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.dependency_mocker = self.spawn_subagent(
            DependencyMocker,
            name="DependencyMocker",
            max_depth=child_depth,
            resources_mb=128,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MockGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        schema_name = payload.get("schema_name", "User")
        bundle = self.generate_mocks(dependencies=["database", "http_client"], schema_name=schema_name)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "mock_bundle": bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        bundle = result.get("mock_bundle")
        if not bundle or not bundle.get("full_code"):
            raise MockGenerationError("MockGenerator produced incomplete mock bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("MockGenerator %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def generate_data_mocks(self, schema: str = "User") -> str:
        """Generate mock entity classes."""
        if self.data_mocker:
            res = self.data_mocker.process({"payload": {"schema_name": schema}})
            return res["mock_code"]
        return f"# Mock for {schema}"

    def generate_mocks(
        self,
        dependencies: Optional[List[str]] = None,
        schema_name: str = "User",
    ) -> Dict[str, Any]:
        """Synthesize all mock stubs into a cohesive mocks module."""
        blocks: List[str] = [
            "from datetime import datetime",
            "from unittest.mock import MagicMock, AsyncMock",
            "",
        ]

        if self.data_mocker:
            blocks.append(self.generate_data_mocks(schema_name))

        if self.dependency_mocker:
            dep_res = self.dependency_mocker.process({})
            blocks.append(dep_res["mock_code"])

        full_code = "\n\n".join(blocks)
        return {
            "schema": schema_name,
            "dependencies": dependencies or ["database"],
            "full_code": full_code,
        }
