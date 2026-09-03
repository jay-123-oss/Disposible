"""Coding Domain Agents for the Fractal Multi-Agent Coding System.

Exports all 24 specialized coding agents and subagents across levels L3 to L7,
along with the registration helper `register_all_coding_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from agents.coding.api_route_agent import APIRouteAgent
from agents.coding.backend_agent import BackendAgent
from agents.coding.controller_agent import (
    AuthController,
    ControllerAgent,
    UserController,
)
from agents.coding.database_agent import DatabaseAgent
from agents.coding.exceptions import (
    APIGenerationError,
    CodingError,
    ControllerGenerationError,
    DatabaseGenerationError,
    MiddlewareGenerationError,
    MigrationGenerationError,
    ModelGenerationError,
    QueryGenerationError,
    ServiceGenerationError,
)
from agents.coding.middleware_agent import MiddlewareAgent
from agents.coding.middleware_handlers import (
    AuthMiddleware,
    LoggingMiddleware,
    RateLimiter,
)
from agents.coding.migration_agent import (
    AlterTable,
    CreateTable,
    DropTable,
    MigrationAgent,
)
from agents.coding.model_agent import (
    ModelAgent,
    SessionModel,
    UserModel,
)
from agents.coding.query_agent import (
    InsertQuery,
    QueryAgent,
    SelectQuery,
    UpdateQuery,
)
from agents.coding.route_handlers import (
    DELETERouteAgent,
    GETRouteAgent,
    POSTRouteAgent,
    PUTRouteAgent,
    RouteResponseFormatter,
    RouteServiceCaller,
    RouteValidator,
)
from agents.coding.service_agent import (
    AuthService,
    ServiceAgent,
    UserService,
)
from core.registry import AgentRegistry


logger = logging.getLogger("FractalCore.Coding")

__all__ = [
    # Coordinator
    "BackendAgent",
    # API & Routes
    "APIRouteAgent",
    "GETRouteAgent",
    "POSTRouteAgent",
    "PUTRouteAgent",
    "DELETERouteAgent",
    "RouteValidator",
    "RouteServiceCaller",
    "RouteResponseFormatter",
    # Middleware
    "MiddlewareAgent",
    "AuthMiddleware",
    "LoggingMiddleware",
    "RateLimiter",
    # Controllers
    "ControllerAgent",
    "AuthController",
    "UserController",
    # Services
    "ServiceAgent",
    "AuthService",
    "UserService",
    # Database
    "DatabaseAgent",
    "ModelAgent",
    "UserModel",
    "SessionModel",
    "QueryAgent",
    "SelectQuery",
    "InsertQuery",
    "UpdateQuery",
    "MigrationAgent",
    "CreateTable",
    "AlterTable",
    "DropTable",
    # Exceptions
    "CodingError",
    "APIGenerationError",
    "MiddlewareGenerationError",
    "ControllerGenerationError",
    "ServiceGenerationError",
    "DatabaseGenerationError",
    "ModelGenerationError",
    "QueryGenerationError",
    "MigrationGenerationError",
    # Registration Helper
    "register_all_coding_agents",
]


def register_all_coding_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Register all 24 coding layer agents into the AgentRegistry.

    Args:
        registry: The central AgentRegistry singleton.
        parent_agent: Optional supervising developer agent.
        max_depth: Global depth ceiling for coding hierarchy.

    Returns:
        Dict mapping agent_id to instantiated agent instances.
    """
    logger.info("Registering all 24 coding domain agents into AgentRegistry...")

    # Root Backend Agent (L3)
    backend = BackendAgent(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="C1_BACKEND_AGENT",
        auto_spawn_subagents=True,
    )
    registry.register_agent(backend)

    # Register all spawned children recursively
    registered_count = 1
    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(backend)

    logger.info("Successfully registered %d coding domain agents into registry.", registered_count)
    return {
        "backend": backend,
        "total_registered": registered_count,
    }
