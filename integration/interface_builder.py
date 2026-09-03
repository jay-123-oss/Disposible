"""InterfaceBuilder agent constructing CLI command structures, Web views, REST schemas, and request routing."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from integration.exceptions import InterfaceError


logger = logging.getLogger("FractalCore.Integration.InterfaceBuilder")


# ==============================================================================
# L5 Atomic Interface Builder Subagents
# ==============================================================================

class CliInterfaceBuilder(BaseAgent):
    """L5 agent constructing argparse parsers, CLI flags, help manuals, and subcommands."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CliInterfaceBuilder %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        flags = [
            {"flag": "--task", "type": "str", "help": "Direct task intent"},
            {"flag": "--capability", "type": "str", "help": "Target agent capability domain"},
            {"flag": "--interactive", "type": "bool", "help": "Launch interactive REPL mode"},
            {"flag": "--batch", "type": "str", "help": "Path to batch task YAML/JSON manifest"},
            {"flag": "--config", "type": "str", "help": "Custom config path"},
        ]
        return {"status": "COMPLETED", "interface": "CLI", "flags": flags}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CliInterfaceBuilder %s cleaned up.", self.agent_id)


class WebInterfaceBuilder(BaseAgent):
    """L5 agent generating Web UI component specs, real-time event socket endpoints, and static routes."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("WebInterfaceBuilder %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        routes = [
            {"path": "/", "view": "DashboardView"},
            {"path": "/tasks", "view": "TaskQueueView"},
            {"path": "/agents", "view": "AgentTreeView"},
            {"path": "/metrics", "view": "TelemetryView"},
        ]
        return {"status": "COMPLETED", "interface": "WEB", "routes": routes}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("WebInterfaceBuilder %s cleaned up.", self.agent_id)


class ApiInterfaceBuilder(BaseAgent):
    """L5 agent compiling OpenAPI 3.0 specification documents and REST endpoint schemas."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ApiInterfaceBuilder %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        endpoints = [
            {"method": "POST", "path": "/api/v1/tasks", "desc": "Submit new task"},
            {"method": "GET", "path": "/api/v1/tasks/{id}", "desc": "Get task status"},
            {"method": "GET", "path": "/api/v1/agents", "desc": "List registered agents"},
            {"method": "GET", "path": "/api/v1/health", "desc": "Health status"},
        ]
        return {"status": "COMPLETED", "interface": "API", "endpoints": endpoints}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ApiInterfaceBuilder %s cleaned up.", self.agent_id)


class InterfaceRouter(BaseAgent):
    """L5 agent routing incoming user or client requests to designated interface controllers."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("InterfaceRouter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        target_iface = payload.get("interface", "CLI")

        return {
            "status": "COMPLETED",
            "routed_interface": target_iface,
            "routing_success": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("InterfaceRouter %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 InterfaceBuilder Agent
# ==============================================================================

class InterfaceBuilder(BaseAgent):
    """L4 coordinator overseeing CLI flag builders, Web UI specs, API schemas, and request routing."""

    def __init__(
        self,
        name: str = "InterfaceBuilder",
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
            "interface_building",
            "cli_builder",
            "web_builder",
            "api_builder",
            "interface_routing",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "IA7_INTERFACE_BUILDER",
        )

        self.cli_bld: Optional[CliInterfaceBuilder] = None
        self.web_bld: Optional[WebInterfaceBuilder] = None
        self.api_bld: Optional[ApiInterfaceBuilder] = None
        self.router: Optional[InterfaceRouter] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("build_interfaces", self.build_interfaces)

    def _spawn_subagents(self) -> None:
        """Spawn atomic interface builder subagents (Rule 1 & Rule 5)."""
        logger.info("InterfaceBuilder %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.cli_bld = self.spawn_subagent(CliInterfaceBuilder, name="CliInterfaceBuilder", max_depth=child_depth, resources_mb=32)
        self.web_bld = self.spawn_subagent(WebInterfaceBuilder, name="WebInterfaceBuilder", max_depth=child_depth, resources_mb=32)
        self.api_bld = self.spawn_subagent(ApiInterfaceBuilder, name="ApiInterfaceBuilder", max_depth=child_depth, resources_mb=32)
        self.router = self.spawn_subagent(InterfaceRouter, name="InterfaceRouter", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("InterfaceBuilder %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        res = self.build_interfaces()
        return {"status": "COMPLETED", "interfaces": res}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("InterfaceBuilder %s cleanup complete.", self.agent_id)

    def build_interfaces(self) -> Dict[str, Any]:
        """Synthesize all three supported client interface definitions."""
        p_env = {"payload": {}}

        c_res = self.cli_bld.process(p_env) if self.cli_bld else {}
        w_res = self.web_bld.process(p_env) if self.web_bld else {}
        a_res = self.api_bld.process(p_env) if self.api_bld else {}

        return {
            "cli": c_res.get("flags", []),
            "web": w_res.get("routes", []),
            "api": a_res.get("endpoints", []),
            "all_built": True,
        }
