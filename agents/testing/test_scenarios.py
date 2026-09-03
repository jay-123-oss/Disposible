"""Specialized test scenario agents: HappyPathTester, EdgeCaseHunter, and ErrorCaseTester."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.testing.exceptions import TestGenerationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Testing.Scenarios")


# ==============================================================================
# Atomic Subagents for Scenario Testing (L6)
# ==============================================================================

class InputGenerator(BaseAgent):
    """Atomic worker generating valid, representative test inputs."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("InputGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        target = payload.get("target", "user")
        data = {
            "email": f"test_{target}@example.com",
            "password": "SecurePassword123!",
            "is_active": True,
            "roles": ["user"],
        }
        return {"status": "COMPLETED", "inputs": data}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "inputs" not in result:
            raise TestGenerationError("InputGenerator produced empty inputs.")
        return result

    def cleanup(self) -> None:
        logger.debug("InputGenerator %s cleaned up.", self.agent_id)


class OutputVerifier(BaseAgent):
    """Atomic worker generating output inspection and contract verification code."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("OutputVerifier %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        code = (
            "assert result is not None\n"
            "assert 'id' in result or hasattr(result, 'id')\n"
            "assert getattr(result, 'is_active', True) is True\n"
        )
        return {"status": "COMPLETED", "code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result:
            raise TestGenerationError("OutputVerifier produced empty verification code.")
        return result

    def cleanup(self) -> None:
        logger.debug("OutputVerifier %s cleaned up.", self.agent_id)


class AssertionBuilder(BaseAgent):
    """Atomic worker generating assert statements."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AssertionBuilder %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        expected_status = payload.get("expected_status", 200)
        code = f"assert response.status_code == {expected_status}\n"
        return {"status": "COMPLETED", "code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result:
            raise TestGenerationError("AssertionBuilder produced empty assertion code.")
        return result

    def cleanup(self) -> None:
        logger.debug("AssertionBuilder %s cleaned up.", self.agent_id)


# ==============================================================================
# L5 Scenario Tester Agents
# ==============================================================================

class HappyPathTester(BaseAgent):
    """L5 agent generating test cases validating standard business workflows and sunny-day paths."""

    def __init__(
        self,
        name: str = "HappyPathTester",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["happy_path_testing", "positive_assertion_generation"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "T3_HAPPY_PATH_TESTER",
        )
        self.input_gen: Optional[InputGenerator] = None
        self.output_ver: Optional[OutputVerifier] = None
        self.assertion_bld: Optional[AssertionBuilder] = None
        self._spawn_subagents()
        self.register_tool("generate_happy_path_test", self.generate_happy_path_test)

    def _spawn_subagents(self) -> None:
        """Spawn atomic helper agents."""
        child_depth = self.depth + 2
        self.input_gen = self.spawn_subagent(
            InputGenerator,
            name="InputGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.output_ver = self.spawn_subagent(
            OutputVerifier,
            name="OutputVerifier",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.assertion_bld = self.spawn_subagent(
            AssertionBuilder,
            name="AssertionBuilder",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("HappyPathTester %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        func_name = payload.get("function_name", "register_user")
        code = self.generate_happy_path_test(func_name)
        return {"status": "COMPLETED", "agent_id": self.agent_id, "test_code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "test_code" not in result or not result["test_code"]:
            raise TestGenerationError("HappyPathTester produced empty test code.")
        return result

    def cleanup(self) -> None:
        logger.debug("HappyPathTester %s cleaned up.", self.agent_id)

    def generate_happy_path_test(self, function_name: str = "register_user") -> str:
        """Synthesize a complete happy-path unit test function."""
        return (
            f"def test_{function_name}_success(mock_db_session):\n"
            f"    \"\"\"Verify successful execution of {function_name} with valid inputs.\"\"\"\n"
            f"    # Arrange\n"
            f"    test_email = 'happy_path@example.com'\n"
            f"    test_password = 'ValidPassword123!'\n\n"
            f"    # Act\n"
            f"    result = {function_name}(email=test_email, password=test_password, db=mock_db_session)\n\n"
            f"    # Assert\n"
            f"    assert result is not None\n"
            f"    assert result.get('status') == 'success' or hasattr(result, 'id')\n"
        )


class EdgeCaseHunter(BaseAgent):
    """L5 agent identifying nulls, boundary values, empty payloads, and unusual unicode inputs."""

    def __init__(
        self,
        name: str = "EdgeCaseHunter",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["edge_case_testing", "boundary_value_analysis", "null_safety_testing"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "T4_EDGE_CASE_HUNTER",
        )
        self.register_tool("generate_edge_case_tests", self.generate_edge_case_tests)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("EdgeCaseHunter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        func_name = payload.get("function_name", "register_user")
        code = self.generate_edge_case_tests(func_name)
        return {"status": "COMPLETED", "agent_id": self.agent_id, "test_code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "test_code" not in result or not result["test_code"]:
            raise TestGenerationError("EdgeCaseHunter produced empty test code.")
        return result

    def cleanup(self) -> None:
        logger.debug("EdgeCaseHunter %s cleaned up.", self.agent_id)

    def generate_edge_case_tests(self, function_name: str = "register_user") -> str:
        """Synthesize edge case tests covering boundary conditions."""
        return (
            f"@pytest.mark.parametrize('edge_input', ['', '   ', 'a' * 256, 'user+tag@sub.domain.co'])\n"
            f"def test_{function_name}_boundary_inputs(mock_db_session, edge_input):\n"
            f"    \"\"\"Verify {function_name} behaves gracefully on boundary inputs.\"\"\"\n"
            f"    if not edge_input.strip() or len(edge_input) > 255:\n"
            f"        with pytest.raises((ValueError, Exception)):\n"
            f"            {function_name}(email=edge_input, password='Pass', db=mock_db_session)\n"
            f"    else:\n"
            f"        res = {function_name}(email=edge_input, password='ValidPassword123!', db=mock_db_session)\n"
            f"        assert res is not None\n\n"
            f"def test_{function_name}_none_handling(mock_db_session):\n"
            f"    \"\"\"Ensure None/null parameters raise appropriate validation exceptions.\"\"\"\n"
            f"    with pytest.raises((ValueError, TypeError, Exception)):\n"
            f"        {function_name}(email=None, password=None, db=mock_db_session)\n"
        )


class ErrorCaseTester(BaseAgent):
    """L5 agent validating exceptional paths, invalid state transitions, and expected errors."""

    def __init__(
        self,
        name: str = "ErrorCaseTester",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["error_case_testing", "exception_assertion", "failure_mode_testing"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "T5_ERROR_CASE_TESTER",
        )
        self.register_tool("generate_error_case_tests", self.generate_error_case_tests)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ErrorCaseTester %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        func_name = payload.get("function_name", "register_user")
        code = self.generate_error_case_tests(func_name)
        return {"status": "COMPLETED", "agent_id": self.agent_id, "test_code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "test_code" not in result or not result["test_code"]:
            raise TestGenerationError("ErrorCaseTester produced empty test code.")
        return result

    def cleanup(self) -> None:
        logger.debug("ErrorCaseTester %s cleaned up.", self.agent_id)

    def generate_error_case_tests(self, function_name: str = "register_user") -> str:
        """Synthesize error-case tests asserting specific exceptions and HTTP statuses."""
        return (
            f"def test_{function_name}_duplicate_entry(mock_db_session):\n"
            f"    \"\"\"Verify duplicate registration attempts raise expected conflict errors.\"\"\"\n"
            f"    # Mock pre-existing user condition\n"
            f"    mock_db_session.user_exists = True\n"
            f"    with pytest.raises(ValueError, match=r'.*(already registered|exists|duplicate).*'):\n"
            f"        {function_name}(email='existing@example.com', password='ValidPassword123!', db=mock_db_session)\n\n"
            f"def test_{function_name}_db_connection_failure(mock_db_session):\n"
            f"    \"\"\"Verify graceful failure when database raises connection error.\"\"\"\n"
            f"    mock_db_session.simulate_disconnect = True\n"
            f"    with pytest.raises(Exception):\n"
            f"        {function_name}(email='normal@example.com', password='ValidPassword123!', db=mock_db_session)\n"
        )
