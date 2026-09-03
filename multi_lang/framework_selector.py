"""FrameworkSelector agent selecting the optimal web framework per language.

Implements the complete Framework Selector hierarchy (M11):
- L4 FrameworkSelector coordinator
- L5 atomic workers: FastapiSelector, ExpressSelector, GinSelector, ActixSelector, SpringSelector
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from multi_lang.exceptions import FrameworkSelectionError


logger = logging.getLogger("FractalCore.MultiLang.FrameworkSelector")


# ==============================================================================
# L5 Atomic Framework Selector Subagents
# ==============================================================================

class FastapiSelector(BaseAgent):
    """L5 agent selecting FastAPI/Flask/Django for Python projects."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("FastapiSelector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        workload = task_envelope.get("workload", "api")
        framework = "fastapi" if workload == "api" else ("django" if workload == "fullstack" else "flask")
        return {"status": "COMPLETED", "language": "python", "framework": framework, "score": 9.5}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("FastapiSelector %s cleaned up.", self.agent_id)


class ExpressSelector(BaseAgent):
    """L5 agent selecting Express/NestJS/Fastify for Node.js projects."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ExpressSelector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        workload = task_envelope.get("workload", "api")
        framework = "nestjs" if workload == "enterprise" else ("fastify" if workload == "low_latency" else "express")
        return {"status": "COMPLETED", "language": "node", "framework": framework, "score": 9.2}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ExpressSelector %s cleaned up.", self.agent_id)


class GinSelector(BaseAgent):
    """L5 agent selecting Gin/Echo/Fiber for Go projects."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("GinSelector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        workload = task_envelope.get("workload", "api")
        framework = "gin" if workload == "api" else ("echo" if workload == "middleware_heavy" else "fiber")
        return {"status": "COMPLETED", "language": "go", "framework": framework, "score": 9.0}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("GinSelector %s cleaned up.", self.agent_id)


class ActixSelector(BaseAgent):
    """L5 agent selecting Actix/Rocket/Axum for Rust projects."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ActixSelector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        workload = task_envelope.get("workload", "high_performance")
        framework = "actix" if workload == "high_performance" else ("rocket" if workload == "developer_friendly" else "axum")
        return {"status": "COMPLETED", "language": "rust", "framework": framework, "score": 9.1}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ActixSelector %s cleaned up.", self.agent_id)


class SpringSelector(BaseAgent):
    """L5 agent selecting Spring Boot/Quarkus/Micronaut for Java projects."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SpringSelector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        workload = task_envelope.get("workload", "enterprise")
        framework = "spring-boot" if workload == "enterprise" else ("quarkus" if workload == "cloud_native" else "micronaut")
        return {"status": "COMPLETED", "language": "java", "framework": framework, "score": 9.3}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SpringSelector %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 FrameworkSelector Agent
# ==============================================================================

class FrameworkSelector(BaseAgent):
    """L4 coordinator selecting the optimal framework for any supported language."""

    def __init__(
        self,
        name: str = "FrameworkSelector",
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
            "framework_selector",
            "fastapi_selector",
            "express_selector",
            "gin_selector",
            "actix_selector",
            "spring_selector",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M11_FRAMEWORK_SELECTOR",
        )
        self.fastapi: Optional[FastapiSelector] = None
        self.express: Optional[ExpressSelector] = None
        self.gin: Optional[GinSelector] = None
        self.actix: Optional[ActixSelector] = None
        self.spring: Optional[SpringSelector] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("select_framework", self.select_framework)

    def _spawn_subagents(self) -> None:
        """Spawn atomic framework selector subagents (Rule 1 & Rule 5)."""
        logger.info("FrameworkSelector %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.fastapi = self.spawn_subagent(FastapiSelector, name="FastapiSelector", max_depth=child_depth, resources_mb=32)
        self.express = self.spawn_subagent(ExpressSelector, name="ExpressSelector", max_depth=child_depth, resources_mb=32)
        self.gin = self.spawn_subagent(GinSelector, name="GinSelector", max_depth=child_depth, resources_mb=32)
        self.actix = self.spawn_subagent(ActixSelector, name="ActixSelector", max_depth=child_depth, resources_mb=32)
        self.spring = self.spawn_subagent(SpringSelector, name="SpringSelector", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("FrameworkSelector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.select_framework(payload.get("language", "python"), payload.get("workload", "api"))
        return {"status": "COMPLETED", "selection": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("FrameworkSelector %s cleanup complete.", self.agent_id)

    def select_framework(self, language: str, workload: str = "api") -> Dict[str, Any]:
        """Select the best framework for the language + workload profile."""
        logger.info("Selecting framework for %s (%s)...", language, workload)
        selector_map = {
            "python": self.fastapi,
            "node": self.express,
            "go": self.gin,
            "rust": self.actix,
            "java": self.spring,
        }
        selector = selector_map.get(language.lower())
        if selector is None:
            raise FrameworkSelectionError(f"Unsupported language for framework selection: {language}")
        result = selector.process({"workload": workload})
        return {
            "language": result.get("language"),
            "framework": result.get("framework"),
            "score": result.get("score"),
            "optimal": True,
            "alternatives": ["default"],
        }