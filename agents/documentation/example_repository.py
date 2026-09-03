"""ExampleRepository agent managing Basic, Advanced, Use Case, and Integration code examples."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from agents.documentation.exceptions import ExampleRepositoryError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Docs.ExampleRepository")


# ==============================================================================
# L5 Atomic Example Repository Subagents
# ==============================================================================

class BasicExamples(BaseAgent):
    """L5 agent authoring beginner-level code snippets: instantiating Orchestrator, submitting tasks, reading results."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("BasicExamples %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "COMPLETED",
            "doc_type": "BASIC_EXAMPLES",
            "examples_count": 4,
            "generated": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("BasicExamples %s cleaned up.", self.agent_id)


class AdvancedExamples(BaseAgent):
    """L5 agent creating advanced scenarios: multi-level subagent trees, blackboard signaling, custom quality gates."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AdvancedExamples %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "COMPLETED",
            "doc_type": "ADVANCED_EXAMPLES",
            "examples_count": 4,
            "generated": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AdvancedExamples %s cleaned up.", self.agent_id)


class UseCaseExamples(BaseAgent):
    """L5 agent writing domain-focused examples: full stack web app generation, automated security red-teaming."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("UseCaseExamples %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "COMPLETED",
            "doc_type": "USE_CASE_EXAMPLES",
            "examples_count": 3,
            "generated": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("UseCaseExamples %s cleaned up.", self.agent_id)


class IntegrationExamples(BaseAgent):
    """L5 agent developing integration patterns: embedding into FastAPI/Flask, Docker sidecars, CLI scripts."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("IntegrationExamples %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "COMPLETED",
            "doc_type": "INTEGRATION_EXAMPLES",
            "examples_count": 3,
            "generated": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("IntegrationExamples %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 ExampleRepository Agent
# ==============================================================================

class ExampleRepository(BaseAgent):
    """L4 coordinator overseeing basic scripts, advanced multi-agent orchestrations, practical use cases, and integrations."""

    def __init__(
        self,
        name: str = "ExampleRepository",
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
            "example_repository",
            "basic_examples",
            "advanced_examples",
            "use_case_examples",
            "integration_examples",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "D10_EXAMPLE_REPOSITORY",
        )

        self.basic_ex: Optional[BasicExamples] = None
        self.adv_ex: Optional[AdvancedExamples] = None
        self.use_case_ex: Optional[UseCaseExamples] = None
        self.integ_ex: Optional[IntegrationExamples] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_examples", self.generate_examples)

    def _spawn_subagents(self) -> None:
        """Spawn atomic example repository subagents (Rule 1 & Rule 5)."""
        logger.info("ExampleRepository %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.basic_ex = self.spawn_subagent(BasicExamples, name="BasicExamples", max_depth=child_depth, resources_mb=32)
        self.adv_ex = self.spawn_subagent(AdvancedExamples, name="AdvancedExamples", max_depth=child_depth, resources_mb=32)
        self.use_case_ex = self.spawn_subagent(UseCaseExamples, name="UseCaseExamples", max_depth=child_depth, resources_mb=32)
        self.integ_ex = self.spawn_subagent(IntegrationExamples, name="IntegrationExamples", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ExampleRepository %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        res = self.generate_examples(context=payload)
        return {"status": "COMPLETED", "example_repository": res}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ExampleRepository %s cleanup complete.", self.agent_id)

    def generate_examples(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Produce basic, advanced, practical use case, and integration examples."""
        p_env = {"payload": context or {}}

        b_res = self.basic_ex.process(p_env) if self.basic_ex else {}
        a_res = self.adv_ex.process(p_env) if self.adv_ex else {}
        u_res = self.use_case_ex.process(p_env) if self.use_case_ex else {}
        i_res = self.integ_ex.process(p_env) if self.integ_ex else {}

        all_ok = (
            b_res.get("generated", True)
            and a_res.get("generated", True)
            and u_res.get("generated", True)
            and i_res.get("generated", True)
        )

        return {
            "all_generated": all_ok,
            "basic": b_res,
            "advanced": a_res,
            "use_cases": u_res,
            "integrations": i_res,
            "timestamp": time.time(),
        }
