"""BackendAgent orchestrating API, Middleware, Controller, Service, and Database layers."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.coding.api_route_agent import APIRouteAgent
from agents.coding.controller_agent import ControllerAgent
from agents.coding.database_agent import DatabaseAgent
from agents.coding.exceptions import CodingError
from agents.coding.middleware_agent import MiddlewareAgent
from agents.coding.service_agent import ServiceAgent
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Coding.BackendAgent")


class BackendAgent(BaseAgent):
    """L3 Master Backend Agent orchestrating the entire backend generation pipeline."""

    def __init__(
        self,
        name: str = "BackendAgent",
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
            "backend_development",
            "api_design",
            "database_coordination",
            "full_stack_backend_synthesis",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C1_BACKEND_AGENT",
        )

        self.api_agent: Optional[APIRouteAgent] = None
        self.middleware_agent: Optional[MiddlewareAgent] = None
        self.controller_agent: Optional[ControllerAgent] = None
        self.service_agent: Optional[ServiceAgent] = None
        self.database_agent: Optional[DatabaseAgent] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_backend_subagents()

        self.register_tool("synthesize_backend", self.synthesize_backend)

    def _spawn_backend_subagents(self) -> None:
        """Spawn the 5 major subsystem coordinators (API, Middleware, Controller, Service, Database)."""
        logger.info("BackendAgent %s spawning 5 subsystem coordinators (L4)...", self.agent_id)
        child_depth = self.depth + 2
        self.api_agent = self.spawn_subagent(
            APIRouteAgent,
            name="APIRouteAgent",
            max_depth=child_depth,
            resources_mb=256,
        )
        self.middleware_agent = self.spawn_subagent(
            MiddlewareAgent,
            name="MiddlewareAgent",
            max_depth=child_depth,
            resources_mb=256,
        )
        self.controller_agent = self.spawn_subagent(
            ControllerAgent,
            name="ControllerAgent",
            max_depth=child_depth,
            resources_mb=256,
        )
        self.service_agent = self.spawn_subagent(
            ServiceAgent,
            name="ServiceAgent",
            max_depth=child_depth,
            resources_mb=256,
        )
        self.database_agent = self.spawn_subagent(
            DatabaseAgent,
            name="DatabaseAgent",
            max_depth=child_depth,
            resources_mb=256,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("BackendAgent %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        entity = payload.get("entity", "user")
        backend_artifacts = self.synthesize_backend(entity=entity)

        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "entity": entity,
            "backend_artifacts": backend_artifacts,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        artifacts = result.get("backend_artifacts")
        if not artifacts or "main_app_code" not in artifacts:
            raise CodingError("BackendAgent produced incomplete backend artifacts.")
        return result

    def cleanup(self) -> None:
        logger.debug("BackendAgent %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def synthesize_backend(self, entity: str = "user") -> Dict[str, Any]:
        """Execute full hierarchical generation across all 5 subsystems."""
        logger.info("Synthesizing full backend for entity: '%s'...", entity)

        # 1. Database
        db_res = self.database_agent.process({"payload": {"model_name": entity.capitalize()}}) if self.database_agent else {}
        db_bundle = db_res.get("database_bundle", {})

        # 2. Services
        svc_res = self.service_agent.process({}) if self.service_agent else {}
        svc_bundle = svc_res.get("services_bundle", {})

        # 3. Controllers
        ctrl_res = self.controller_agent.process({}) if self.controller_agent else {}
        ctrl_bundle = ctrl_res.get("controllers_bundle", {})

        # 4. Middleware
        mid_res = self.middleware_agent.process({}) if self.middleware_agent else {}
        mid_stack = mid_res.get("middleware_stack", {})

        # 5. API Routes
        api_res = self.api_agent.process({"payload": {"entity": entity}}) if self.api_agent else {}
        api_bundle = api_res.get("routes_bundle", {})

        # Generate main.py entrypoint connecting all components
        main_app_code = (
            "from fastapi import FastAPI\n"
            "from app.api.routes import router as api_router\n"
            "from app.middleware.stack import logging_middleware, auth_middleware, rate_limit_middleware\n"
            "from app.database.session import engine\n\n"
            "app = FastAPI(title='Autonomous Backend Service', version='1.0.0')\n\n"
            "# Attach middleware stack\n"
            "app.middleware('http')(logging_middleware)\n"
            "app.middleware('http')(rate_limit_middleware)\n"
            "app.middleware('http')(auth_middleware)\n\n"
            "# Mount routers\n"
            f"app.include_router(api_router, prefix='/api/v1')\n\n"
            "@app.get('/health')\n"
            "async def health_check():\n"
            "    return {'status': 'healthy', 'timestamp': time.time()}\n"
        )

        return {
            "main_app_code": main_app_code,
            "database": db_bundle,
            "services": svc_bundle,
            "controllers": ctrl_bundle,
            "middleware": mid_stack,
            "api_routes": api_bundle,
        }
