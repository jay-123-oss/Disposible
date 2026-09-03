"""ArchitectureDesigner agent for defining architectural layers, components, and data flows."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.planning.exceptions import ArchitectureDesignError
from agents.planning.knowledge_base import KnowledgeBase
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Planning.ArchitectureDesigner")


class ArchitectureDesigner(BaseAgent):
    """Synthesizes clean, modular architectural blueprints, layers, components, and interface boundaries."""

    def __init__(
        self,
        name: str = "ArchitectureDesigner",
        capabilities: Optional[List[str]] = None,
        model: str = "llama3.2:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or [
            "architecture_design",
            "layer_definition",
            "interface_specification",
            "data_flow_mapping",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P7_ARCHITECTURE_DESIGNER",
        )
        self._knowledge_base = KnowledgeBase()
        self.register_tool("design_architecture", self.design_architecture)
        self.register_tool("define_layers", self.define_layers)
        self.register_tool("specify_interfaces", self.specify_interfaces)

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ArchitectureDesigner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        arch_design = self.design_architecture(payload)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "architecture": arch_design,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        arch = result.get("architecture")
        if not arch or "layers" not in arch or "components" not in arch:
            raise ArchitectureDesignError(
                "ArchitectureDesigner produced incomplete architecture.",
                details={"result": result, "agent_id": self.agent_id},
            )
        return result

    def cleanup(self) -> None:
        logger.debug("ArchitectureDesigner %s cleaned up.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def design_architecture(self, reqs: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize a complete architectural blueprint from requirements."""
        entities = reqs.get("entities", {})
        proj_type = (entities.get("project_type") or reqs.get("project_type", "API")).lower()

        # Select pattern
        if proj_type == "microservice":
            pattern_name = "microservices"
        elif proj_type in ("cli", "script"):
            pattern_name = "monolithic"
        else:
            pattern_name = "hexagonal"

        pat_info = self._knowledge_base.get_architecture_pattern(pattern_name)
        layers = self.define_layers(reqs)

        # Identify core components
        components = [
            {"id": "CMP_ROUTER", "name": "ApiRouter", "layer": "Presentation", "role": "HTTP dispatch and DTO validation"},
            {"id": "CMP_SERVICE", "name": "BusinessService", "layer": "Service", "role": "Transactional domain logic"},
            {"id": "CMP_DATA", "name": "DataRepository", "layer": "DataAccess", "role": "Database persistence and ORM queries"},
            {"id": "CMP_SECURITY", "name": "SecurityMiddleware", "layer": "CrossCutting", "role": "JWT auth & permission gates"},
        ]

        interfaces = self.specify_interfaces(components)

        data_flow = [
            "Client HTTP Request -> SecurityMiddleware (Token Check)",
            "SecurityMiddleware -> ApiRouter (Path Parameter & DTO Validation)",
            "ApiRouter -> BusinessService (Execute Intent)",
            "BusinessService -> DataRepository (Execute SQL Query / ORM Commit)",
            "DataRepository -> BusinessService (Return Entity Model)",
            "BusinessService -> ApiRouter (Return Serialized DTO)",
            "ApiRouter -> Client HTTP 200/201 JSON Response",
        ]

        return {
            "pattern": pattern_name,
            "pattern_description": pat_info.get("description", "") if pat_info else "",
            "layers": layers,
            "components": components,
            "interfaces": interfaces,
            "data_flow": data_flow,
            "patterns_applied": ["Repository Pattern", "Dependency Injection", "DTO Pattern"],
        }

    def define_layers(self, tech_stack: Dict[str, Any]) -> List[Dict[str, str]]:
        """Define the architectural tiers and their responsibilities."""
        return [
            {
                "name": "Presentation Layer",
                "folder": "app/api/",
                "responsibility": "Route handlers, request parsing, response formatting, status codes",
            },
            {
                "name": "Service / Domain Layer",
                "folder": "app/services/",
                "responsibility": "Business rules, domain validation, orchestration between repositories",
            },
            {
                "name": "Data Access Layer",
                "folder": "app/models/ and app/repositories/",
                "responsibility": "ORM schema definitions, raw SQL queries, transaction boundaries",
            },
            {
                "name": "Cross-Cutting Layer",
                "folder": "app/core/ and app/middleware/",
                "responsibility": "Logging, security checks, exception handlers, config management",
            },
        ]

    def specify_interfaces(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Define interface contracts connecting adjacent architectural components."""
        return [
            {
                "interface": "IServiceHandler",
                "caller": "CMP_ROUTER",
                "implementer": "CMP_SERVICE",
                "methods": [
                    "execute(context: RequestContext) -> ServiceResult",
                    "validate_constraints(dto: BaseModel) -> bool",
                ],
            },
            {
                "interface": "IRepository",
                "caller": "CMP_SERVICE",
                "implementer": "CMP_DATA",
                "methods": [
                    "get_by_id(id: UUID) -> Optional[Model]",
                    "create(model: Model) -> Model",
                    "update(id: UUID, patch: dict) -> Model",
                    "delete(id: UUID) -> bool",
                ],
            },
        ]
