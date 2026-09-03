"""APIRouteAgent coordinating HTTP verb generation, route assembly, and router registration."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.coding.exceptions import APIGenerationError
from agents.coding.route_handlers import (
    DELETERouteAgent,
    GETRouteAgent,
    POSTRouteAgent,
    PUTRouteAgent,
)
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Coding.APIRouteAgent")


class APIRouteAgent(BaseAgent):
    """L4 agent coordinating REST endpoint generation across GET, POST, PUT, and DELETE handlers."""

    def __init__(
        self,
        name: str = "APIRouteAgent",
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
            "api_route_generation",
            "endpoint_coordination",
            "rest_routing",
            "router_registration",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C2_API_ROUTE_AGENT",
        )

        self.get_agent: Optional[GETRouteAgent] = None
        self.post_agent: Optional[POSTRouteAgent] = None
        self.put_agent: Optional[PUTRouteAgent] = None
        self.delete_agent: Optional[DELETERouteAgent] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_route_subagents()

        self.register_tool("generate_routes", self.generate_routes)
        self.register_tool("generate_get_route", self.generate_get_route)
        self.register_tool("generate_post_route", self.generate_post_route)

    def _spawn_route_subagents(self) -> None:
        """Spawn the 4 specialized HTTP verb agents (Rule 1 & Rule 5)."""
        logger.info("APIRouteAgent %s spawning route verb subagents (GET, POST, PUT, DELETE)...", self.agent_id)
        child_depth = self.depth + 2
        self.get_agent = self.spawn_subagent(
            GETRouteAgent,
            name="GETRouteAgent",
            max_depth=child_depth,
            resources_mb=192,
        )
        self.post_agent = self.spawn_subagent(
            POSTRouteAgent,
            name="POSTRouteAgent",
            max_depth=child_depth,
            resources_mb=192,
        )
        self.put_agent = self.spawn_subagent(
            PUTRouteAgent,
            name="PUTRouteAgent",
            max_depth=child_depth,
            resources_mb=192,
        )
        self.delete_agent = self.spawn_subagent(
            DELETERouteAgent,
            name="DELETERouteAgent",
            max_depth=child_depth,
            resources_mb=192,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("APIRouteAgent %s initialized for task %s", self.agent_id, task_envelope.get("task_id"))

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        entity = payload.get("entity", "user")
        prefix = payload.get("prefix", f"/api/v1/{entity}s")

        routes_bundle = self.generate_routes(controllers=[entity], models=[entity], prefix=prefix)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "entity": entity,
            "prefix": prefix,
            "routes_bundle": routes_bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "routes_bundle" not in result or not result["routes_bundle"].get("full_router_code"):
            raise APIGenerationError("APIRouteAgent produced incomplete route bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("APIRouteAgent %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def generate_routes(
        self,
        controllers: List[str],
        models: List[str],
        prefix: str = "/api/v1/users",
    ) -> Dict[str, Any]:
        """Generate full router module comprising GET, POST, PUT, and DELETE operations."""
        entity = models[0] if models else "user"
        routes: List[str] = []

        # Coordinate execution across sub-agents
        if self.get_agent:
            get_res = self.get_agent.process({"payload": {"endpoint": f"{prefix}/{{id}}", "entity": entity}})
            routes.append(get_res["route_code"])

        if self.post_agent:
            post_res = self.post_agent.process({"payload": {"endpoint": f"{prefix}", "entity": entity}})
            routes.append(post_res["route_code"])

        if self.put_agent:
            put_res = self.put_agent.process({"payload": {"endpoint": f"{prefix}/{{id}}", "entity": entity}})
            routes.append(put_res["route_code"])

        if self.delete_agent:
            del_res = self.delete_agent.process({"payload": {"endpoint": f"{prefix}/{{id}}", "entity": entity}})
            routes.append(del_res["route_code"])

        header = (
            "from typing import Optional\n"
            "from fastapi import APIRouter, Depends, HTTPException, status, Response\n"
            "from sqlalchemy.ext.asyncio import AsyncSession\n"
            "from pydantic import BaseModel, Field\n\n"
            "router = APIRouter(tags=['" + entity.capitalize() + "s'])\n\n"
        )
        full_code = header + "\n".join(routes)

        return {
            "prefix": prefix,
            "entity": entity,
            "operations": ["GET", "POST", "PUT", "DELETE"],
            "full_router_code": full_code,
        }

    def generate_get_route(self, endpoint: str, handler: str, validators: Optional[List[str]] = None) -> str:
        """Helper to invoke GET route generation."""
        if self.get_agent:
            res = self.get_agent.process({"payload": {"endpoint": endpoint, "entity": handler}})
            return res["route_code"]
        return f"# GET {endpoint} -> {handler}"

    def generate_post_route(self, endpoint: str, handler: str, validators: Optional[List[str]] = None) -> str:
        """Helper to invoke POST route generation."""
        if self.post_agent:
            res = self.post_agent.process({"payload": {"endpoint": endpoint, "entity": handler}})
            return res["route_code"]
        return f"# POST {endpoint} -> {handler}"
