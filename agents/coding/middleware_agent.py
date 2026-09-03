"""MiddlewareAgent coordinating auth, logging, and rate limiting middleware generation."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.coding.exceptions import MiddlewareGenerationError
from agents.coding.middleware_handlers import (
    AuthMiddleware,
    LoggingMiddleware,
    RateLimiter,
)
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Coding.MiddlewareAgent")


class MiddlewareAgent(BaseAgent):
    """L4 agent coordinating cross-cutting request/response filters and middleware chains."""

    def __init__(
        self,
        name: str = "MiddlewareAgent",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "middleware_coordination",
            "security_filters",
            "telemetry_interception",
            "traffic_throttling",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C7_MIDDLEWARE_AGENT",
        )

        self.auth_agent: Optional[AuthMiddleware] = None
        self.logging_agent: Optional[LoggingMiddleware] = None
        self.rate_limiter: Optional[RateLimiter] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_middleware_subagents()

        self.register_tool("generate_auth_middleware", self.generate_auth_middleware)
        self.register_tool("generate_logging_middleware", self.generate_logging_middleware)
        self.register_tool("generate_middleware_stack", self.generate_middleware_stack)

    def _spawn_middleware_subagents(self) -> None:
        """Spawn specialized middleware agents (Rule 1 & Rule 5)."""
        logger.info("MiddlewareAgent %s spawning subagents (Auth, Logging, RateLimiter)...", self.agent_id)
        child_depth = self.depth + 2
        self.auth_agent = self.spawn_subagent(
            AuthMiddleware,
            name="AuthMiddleware",
            max_depth=child_depth,
            resources_mb=192,
        )
        self.logging_agent = self.spawn_subagent(
            LoggingMiddleware,
            name="LoggingMiddleware",
            max_depth=child_depth,
            resources_mb=192,
        )
        self.rate_limiter = self.spawn_subagent(
            RateLimiter,
            name="RateLimiter",
            max_depth=child_depth,
            resources_mb=192,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MiddlewareAgent %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        stack = self.generate_middleware_stack(
            include_auth=payload.get("include_auth", True),
            include_logging=payload.get("include_logging", True),
            include_rate_limiting=payload.get("include_rate_limiting", True),
        )
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "middleware_stack": stack,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "middleware_stack" not in result or not result["middleware_stack"].get("full_module_code"):
            raise MiddlewareGenerationError("MiddlewareAgent produced incomplete middleware stack.")
        return result

    def cleanup(self) -> None:
        logger.debug("MiddlewareAgent %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def generate_auth_middleware(self) -> str:
        """Generate JWT authentication middleware."""
        if self.auth_agent:
            res = self.auth_agent.process({})
            return res["code"]
        return "# Auth middleware placeholder"

    def generate_logging_middleware(self) -> str:
        """Generate structured request/response logging middleware."""
        if self.logging_agent:
            res = self.logging_agent.process({})
            return res["code"]
        return "# Logging middleware placeholder"

    def generate_middleware_stack(
        self,
        include_auth: bool = True,
        include_logging: bool = True,
        include_rate_limiting: bool = True,
    ) -> Dict[str, Any]:
        """Assemble all middleware components into a single imports and setup module."""
        parts: List[str] = [
            "import time",
            "import uuid",
            "import logging",
            "from fastapi import Request, Response",
            "from fastapi.responses import JSONResponse",
            "from jose import jwt, JWTError",
            "",
            "logger = logging.getLogger('API.Middleware')",
            "JWT_SECRET_KEY = 'YOUR_SUPER_SECRET_KEY_CHANGE_IN_PRODUCTION'",
            "JWT_ALGORITHM = 'HS256'",
            "",
        ]

        if include_logging:
            parts.append(self.generate_logging_middleware())

        if include_rate_limiting and self.rate_limiter:
            rl_res = self.rate_limiter.process({})
            parts.append(rl_res["code"])

        if include_auth:
            parts.append(self.generate_auth_middleware())

        full_code = "\n".join(parts)
        return {
            "full_module_code": full_code,
            "configured_filters": [
                name for name, enabled in [
                    ("logging", include_logging),
                    ("rate_limiting", include_rate_limiting),
                    ("authentication", include_auth),
                ] if enabled
            ],
        }
