"""UnitTestGenerator coordinating happy path, edge case, and error case test suites."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.testing.exceptions import TestGenerationError
from agents.testing.test_scenarios import (
    EdgeCaseHunter,
    ErrorCaseTester,
    HappyPathTester,
)
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Testing.UnitTestGenerator")


class UnitTestGenerator(BaseAgent):
    """L4 coordinator generating pytest suites by delegating to specialized scenario testers."""

    def __init__(
        self,
        name: str = "UnitTestGenerator",
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
            "unit_test_generation",
            "pytest_suite_synthesis",
            "test_scenario_orchestration",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "T2_UNIT_TEST_GENERATOR",
        )

        self.happy_path_agent: Optional[HappyPathTester] = None
        self.edge_case_agent: Optional[EdgeCaseHunter] = None
        self.error_case_agent: Optional[ErrorCaseTester] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_testing_subagents()

        self.register_tool("generate_tests", self.generate_tests)
        self.register_tool("generate_happy_path", self.generate_happy_path)
        self.register_tool("generate_edge_cases", self.generate_edge_cases)

    def _spawn_testing_subagents(self) -> None:
        """Spawn the 3 scenario test generators (HappyPath, EdgeCase, ErrorCase)."""
        logger.info("UnitTestGenerator %s spawning scenario subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.happy_path_agent = self.spawn_subagent(
            HappyPathTester,
            name="HappyPathTester",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.edge_case_agent = self.spawn_subagent(
            EdgeCaseHunter,
            name="EdgeCaseHunter",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.error_case_agent = self.spawn_subagent(
            ErrorCaseTester,
            name="ErrorCaseTester",
            max_depth=child_depth,
            resources_mb=128,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("UnitTestGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        code = payload.get("code", "")
        functions = payload.get("function_names", ["register_user", "login_user"])

        suite = self.generate_tests(code=code, function_names=functions)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "unit_test_suite": suite,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        suite = result.get("unit_test_suite")
        if not suite or not suite.get("full_test_code"):
            raise TestGenerationError("UnitTestGenerator produced incomplete test suite.")
        return result

    def cleanup(self) -> None:
        logger.debug("UnitTestGenerator %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def generate_happy_path(self, function_name: str) -> str:
        """Generate happy path test."""
        if self.happy_path_agent:
            res = self.happy_path_agent.process({"payload": {"function_name": function_name}})
            return res["test_code"]
        return f"# Happy path test for {function_name}"

    def generate_edge_cases(self, function_name: str) -> str:
        """Generate edge case tests."""
        if self.edge_case_agent:
            res = self.edge_case_agent.process({"payload": {"function_name": function_name}})
            return res["test_code"]
        return f"# Edge cases for {function_name}"

    def generate_error_cases(self, function_name: str) -> str:
        """Generate error case tests."""
        if self.error_case_agent:
            res = self.error_case_agent.process({"payload": {"function_name": function_name}})
            return res["test_code"]
        return f"# Error cases for {function_name}"

    def generate_tests(self, code: str = "", function_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Aggregate unit tests for all target functions into a complete pytest module."""
        targets = function_names or ["register_user", "login_user"]
        test_blocks: List[str] = [
            "import pytest",
            "from unittest.mock import MagicMock, AsyncMock",
            "",
            "@pytest.fixture",
            "def mock_db_session():",
            "    db = MagicMock()",
            "    db.user_exists = False",
            "    db.simulate_disconnect = False",
            "    return db",
            "",
        ]

        for fn in targets:
            test_blocks.append(f"# --- Tests for {fn} ---")
            test_blocks.append(self.generate_happy_path(fn))
            test_blocks.append(self.generate_edge_cases(fn))
            test_blocks.append(self.generate_error_cases(fn))

        full_code = "\n\n".join(test_blocks)
        return {
            "functions_tested": targets,
            "framework": "pytest",
            "full_test_code": full_code,
        }
