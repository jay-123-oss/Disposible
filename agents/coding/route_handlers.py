"""Route handler agents for HTTP verbs: GET, POST, PUT, DELETE with atomic sub-handlers."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.coding.exceptions import APIGenerationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Coding.RouteHandlers")


# ==============================================================================
# Atomic Subagents for Route Assembly (L6 / Atomic Workers)
# ==============================================================================

class RouteValidator(BaseAgent):
    """Atomic worker generating parameter and DTO validation logic."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RouteValidator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        param_name = payload.get("param_name", "id")
        param_type = payload.get("param_type", "int")
        method = payload.get("method", "GET").upper()

        if method in ("POST", "PUT"):
            dto_name = payload.get("dto_name", "ItemPayload")
            code = (
                f"class {dto_name}(BaseModel):\n"
                f"    title: str = Field(..., min_length=1, max_length=255)\n"
                f"    description: Optional[str] = None\n"
            )
        else:
            code = (
                f"def validate_{param_name}(val: {param_type}) -> {param_type}:\n"
                f"    if val is None or (isinstance(val, int) and val <= 0):\n"
                f"        raise HTTPException(status_code=400, detail='Invalid {param_name} provided')\n"
                f"    return val\n"
            )
        return {"status": "COMPLETED", "code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result:
            raise APIGenerationError("RouteValidator produced empty code output.")
        return result

    def cleanup(self) -> None:
        logger.debug("RouteValidator %s cleaned up.", self.agent_id)


class RouteServiceCaller(BaseAgent):
    """Atomic worker generating business logic service call invocations."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RouteServiceCaller %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        entity = payload.get("entity", "item").lower()
        method = payload.get("method", "GET").upper()

        if method == "GET":
            call = f"record = await {entity}_service.get_by_id(validated_id, db=db)"
        elif method == "POST":
            call = f"record = await {entity}_service.create(payload.model_dump(), db=db)"
        elif method == "PUT":
            call = f"record = await {entity}_service.update(validated_id, payload.model_dump(), db=db)"
        elif method == "DELETE":
            call = f"success = await {entity}_service.delete(validated_id, db=db)"
        else:
            call = f"record = await {entity}_service.execute(db=db)"

        return {"status": "COMPLETED", "code": call}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result:
            raise APIGenerationError("RouteServiceCaller produced empty code output.")
        return result

    def cleanup(self) -> None:
        logger.debug("RouteServiceCaller %s cleaned up.", self.agent_id)


class RouteResponseFormatter(BaseAgent):
    """Atomic worker generating HTTP response serialization and status codes."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RouteResponseFormatter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        method = payload.get("method", "GET").upper()
        entity = payload.get("entity", "item").capitalize()

        if method == "POST":
            code = f"return {entity}Response.model_validate(record)"
            status_code = 201
        elif method == "DELETE":
            code = "return Response(status_code=status.HTTP_204_NO_CONTENT)"
            status_code = 204
        else:
            code = (
                f"if not record:\n"
                f"    raise HTTPException(status_code=404, detail='{entity} not found')\n"
                f"return {entity}Response.model_validate(record)"
            )
            status_code = 200

        return {"status": "COMPLETED", "code": code, "status_code": status_code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result:
            raise APIGenerationError("RouteResponseFormatter produced empty code output.")
        return result

    def cleanup(self) -> None:
        logger.debug("RouteResponseFormatter %s cleaned up.", self.agent_id)


# ==============================================================================
# Concrete HTTP Method Route Agents (L5)
# ==============================================================================

class BaseHttpRouteAgent(BaseAgent):
    """Base class for HTTP Verb Route Agents coordinating atomic sub-handlers."""

    def __init__(
        self,
        name: str,
        method: str,
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        self.method = method.upper()
        default_caps = capabilities or [f"{self.method.lower()}_route_generation", "endpoint_assembly"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id,
        )
        self.validator: Optional[RouteValidator] = None
        self.service_caller: Optional[RouteServiceCaller] = None
        self.response_formatter: Optional[RouteResponseFormatter] = None
        self._spawn_subagents()

    def _spawn_subagents(self) -> None:
        """Spawn the 3 atomic sub-agents (Validator, ServiceCaller, Formatter)."""
        child_depth = self.depth + 2
        self.validator = self.spawn_subagent(
            RouteValidator,
            name=f"{self.method}_Validator",
            agent_id=f"{self.method}_VAL_{self.agent_id[:6]}",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.service_caller = self.spawn_subagent(
            RouteServiceCaller,
            name=f"{self.method}_ServiceCaller",
            agent_id=f"{self.method}_SVC_{self.agent_id[:6]}",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.response_formatter = self.spawn_subagent(
            RouteResponseFormatter,
            name=f"{self.method}_ResponseFormatter",
            agent_id=f"{self.method}_FMT_{self.agent_id[:6]}",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("%s initialized for %s endpoint.", self.name, self.method)

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "route_code" not in result:
            raise APIGenerationError(f"{self.name} failed to assemble valid route code.")
        return result

    def cleanup(self) -> None:
        logger.debug("%s cleanup complete.", self.name)


class GETRouteAgent(BaseHttpRouteAgent):
    """L5 agent for assembling HTTP GET routes."""

    def __init__(self, name: str = "GETRouteAgent", agent_id: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(name=name, method="GET", agent_id=agent_id or "C3_GET_ROUTE_AGENT", **kwargs)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        endpoint = payload.get("endpoint", "/users/{id}")
        entity = payload.get("entity", "user").lower()
        param_name = payload.get("param_name", "id")

        val_res = self.validator.process({"payload": {"param_name": param_name, "param_type": "int", "method": "GET"}})
        svc_res = self.service_caller.process({"payload": {"entity": entity, "method": "GET"}})
        fmt_res = self.response_formatter.process({"payload": {"entity": entity, "method": "GET"}})

        route_code = (
            f"@router.get('{endpoint}', response_model={entity.capitalize()}Response, status_code=200)\n"
            f"async def get_{entity}(\n"
            f"    {param_name}: int,\n"
            f"    db: AsyncSession = Depends(get_db_session),\n"
            f"    current_user: User = Depends(get_current_active_user)\n"
            f") -> {entity.capitalize()}Response:\n"
            f"    \"\"\"Fetch a single {entity} by primary key.\"\"\"\n"
            f"    validated_id = validate_{param_name}({param_name})\n"
            f"    {svc_res['code']}\n"
            f"    {fmt_res['code'].replace(chr(10), chr(10) + '    ')}\n"
        )
        return {
            "status": "COMPLETED",
            "method": "GET",
            "endpoint": endpoint,
            "route_code": route_code,
            "validator_code": val_res["code"],
        }


class POSTRouteAgent(BaseHttpRouteAgent):
    """L5 agent for assembling HTTP POST creation routes."""

    def __init__(self, name: str = "POSTRouteAgent", agent_id: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(name=name, method="POST", agent_id=agent_id or "C4_POST_ROUTE_AGENT", **kwargs)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        endpoint = payload.get("endpoint", "/users")
        entity = payload.get("entity", "user").lower()
        dto_name = f"{entity.capitalize()}CreateRequest"

        val_res = self.validator.process({"payload": {"dto_name": dto_name, "method": "POST"}})
        svc_res = self.service_caller.process({"payload": {"entity": entity, "method": "POST"}})
        fmt_res = self.response_formatter.process({"payload": {"entity": entity, "method": "POST"}})

        route_code = (
            f"@router.post('{endpoint}', response_model={entity.capitalize()}Response, status_code=201)\n"
            f"async def create_{entity}(\n"
            f"    payload: {dto_name},\n"
            f"    db: AsyncSession = Depends(get_db_session),\n"
            f"    current_user: User = Depends(get_current_active_user)\n"
            f") -> {entity.capitalize()}Response:\n"
            f"    \"\"\"Create a new {entity} record.\"\"\"\n"
            f"    {svc_res['code']}\n"
            f"    {fmt_res['code']}\n"
        )
        return {
            "status": "COMPLETED",
            "method": "POST",
            "endpoint": endpoint,
            "route_code": route_code,
            "dto_code": val_res["code"],
        }


class PUTRouteAgent(BaseHttpRouteAgent):
    """L5 agent for assembling HTTP PUT update routes."""

    def __init__(self, name: str = "PUTRouteAgent", agent_id: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(name=name, method="PUT", agent_id=agent_id or "C5_PUT_ROUTE_AGENT", **kwargs)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        endpoint = payload.get("endpoint", "/users/{id}")
        entity = payload.get("entity", "user").lower()
        dto_name = f"{entity.capitalize()}UpdateRequest"
        param_name = payload.get("param_name", "id")

        val_res = self.validator.process({"payload": {"dto_name": dto_name, "method": "PUT"}})
        svc_res = self.service_caller.process({"payload": {"entity": entity, "method": "PUT"}})
        fmt_res = self.response_formatter.process({"payload": {"entity": entity, "method": "PUT"}})

        route_code = (
            f"@router.put('{endpoint}', response_model={entity.capitalize()}Response, status_code=200)\n"
            f"async def update_{entity}(\n"
            f"    {param_name}: int,\n"
            f"    payload: {dto_name},\n"
            f"    db: AsyncSession = Depends(get_db_session),\n"
            f"    current_user: User = Depends(get_current_active_user)\n"
            f") -> {entity.capitalize()}Response:\n"
            f"    \"\"\"Update an existing {entity} by ID.\"\"\"\n"
            f"    validated_id = validate_{param_name}({param_name})\n"
            f"    {svc_res['code']}\n"
            f"    {fmt_res['code'].replace(chr(10), chr(10) + '    ')}\n"
        )
        return {
            "status": "COMPLETED",
            "method": "PUT",
            "endpoint": endpoint,
            "route_code": route_code,
            "dto_code": val_res["code"],
        }


class DELETERouteAgent(BaseHttpRouteAgent):
    """L5 agent for assembling HTTP DELETE routes."""

    def __init__(self, name: str = "DELETERouteAgent", agent_id: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(name=name, method="DELETE", agent_id=agent_id or "C6_DELETE_ROUTE_AGENT", **kwargs)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        endpoint = payload.get("endpoint", "/users/{id}")
        entity = payload.get("entity", "user").lower()
        param_name = payload.get("param_name", "id")

        val_res = self.validator.process({"payload": {"param_name": param_name, "param_type": "int", "method": "DELETE"}})
        svc_res = self.service_caller.process({"payload": {"entity": entity, "method": "DELETE"}})
        fmt_res = self.response_formatter.process({"payload": {"entity": entity, "method": "DELETE"}})

        route_code = (
            f"@router.delete('{endpoint}', status_code=status.HTTP_204_NO_CONTENT)\n"
            f"async def delete_{entity}(\n"
            f"    {param_name}: int,\n"
            f"    db: AsyncSession = Depends(get_db_session),\n"
            f"    current_user: User = Depends(get_current_active_user)\n"
            f"):\n"
            f"    \"\"\"Delete an existing {entity} by ID.\"\"\"\n"
            f"    validated_id = validate_{param_name}({param_name})\n"
            f"    {svc_res['code']}\n"
            f"    {fmt_res['code']}\n"
        )
        return {
            "status": "COMPLETED",
            "method": "DELETE",
            "endpoint": endpoint,
            "route_code": route_code,
        }
