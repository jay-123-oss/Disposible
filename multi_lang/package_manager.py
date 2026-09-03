"""PackageManager agent managing language package ecosystems (pip, npm, go mod, cargo, maven).

Implements the complete Package Manager hierarchy (M10):
- L4 PackageManager coordinator
- L5 atomic workers: PipManager, NpmManager, GoModManager, CargoManager, MavenManager
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from multi_lang.exceptions import PackageManagementError


logger = logging.getLogger("FractalCore.MultiLang.PackageManager")


# ==============================================================================
# L5 Atomic Package Management Subagents
# ==============================================================================

class PipManager(BaseAgent):
    """L5 agent managing Python packages via pip/requirements.txt."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PipManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        packages = task_envelope.get("packages", [])
        return {
            "status": "COMPLETED",
            "manager": "pip",
            "language": "python",
            "installed": [f"{pkg}==*" for pkg in packages],
            "manifest": "requirements.txt",
            "install_command": "pip install -r requirements.txt",
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PipManager %s cleaned up.", self.agent_id)


class NpmManager(BaseAgent):
    """L5 agent managing Node.js packages via npm."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NpmManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        packages = task_envelope.get("packages", [])
        return {
            "status": "COMPLETED",
            "manager": "npm",
            "language": "node",
            "installed": packages,
            "manifest": "package.json",
            "install_command": "npm install",
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NpmManager %s cleaned up.", self.agent_id)


class GoModManager(BaseAgent):
    """L5 agent managing Go modules via `go mod`."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("GoModManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        packages = task_envelope.get("packages", [])
        return {
            "status": "COMPLETED",
            "manager": "go mod",
            "language": "go",
            "installed": packages,
            "manifest": "go.mod",
            "install_command": "go mod tidy",
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("GoModManager %s cleaned up.", self.agent_id)


class CargoManager(BaseAgent):
    """L5 agent managing Rust crates via cargo."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CargoManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        packages = task_envelope.get("packages", [])
        return {
            "status": "COMPLETED",
            "manager": "cargo",
            "language": "rust",
            "installed": packages,
            "manifest": "Cargo.toml",
            "install_command": "cargo add <crate>",
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CargoManager %s cleaned up.", self.agent_id)


class MavenManager(BaseAgent):
    """L5 agent managing Java dependencies via Maven."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MavenManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        packages = task_envelope.get("packages", [])
        return {
            "status": "COMPLETED",
            "manager": "maven",
            "language": "java",
            "installed": packages,
            "manifest": "pom.xml",
            "install_command": "mvn dependency:resolve",
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("MavenManager %s cleaned up.", self.agent_id)

    # ==============================================================================
# L4 PackageManager Agent
# ==============================================================================

class PackageManager(BaseAgent):
    """L4 coordinator managing packages across pip, npm, go mod, cargo, and maven."""

    def __init__(
        self,
        name: str = "PackageManager",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
        auto_update: bool = True,
        security_scan: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "package_manager",
            "pip_manager",
            "npm_manager",
            "go_mod_manager",
            "cargo_manager",
            "maven_manager",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M10_PACKAGE_MANAGER",
        )
        self.auto_update = auto_update
        self.security_scan = security_scan
        self.pip: Optional[PipManager] = None
        self.npm: Optional[NpmManager] = None
        self.go_mod: Optional[GoModManager] = None
        self.cargo: Optional[CargoManager] = None
        self.maven: Optional[MavenManager] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("manage_packages", self.manage_packages)

    def _spawn_subagents(self) -> None:
        """Spawn atomic package manager subagents (Rule 1 & Rule 5)."""
        logger.info("PackageManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.pip = self.spawn_subagent(PipManager, name="PipManager", max_depth=child_depth, resources_mb=32)
        self.npm = self.spawn_subagent(NpmManager, name="NpmManager", max_depth=child_depth, resources_mb=32)
        self.go_mod = self.spawn_subagent(GoModManager, name="GoModManager", max_depth=child_depth, resources_mb=32)
        self.cargo = self.spawn_subagent(CargoManager, name="CargoManager", max_depth=child_depth, resources_mb=32)
        self.maven = self.spawn_subagent(MavenManager, name="MavenManager", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PackageManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.manage_packages(payload.get("language", "python"), payload.get("packages", []))
        return {"status": "COMPLETED", "package_management": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PackageManager %s cleanup complete.", self.agent_id)

    def manage_packages(self, language: str, packages: List[str]) -> Dict[str, Any]:
        """Route package requests to the appropriate L5 manager."""
        logger.info("Managing packages for %s...", language)
        manager_map = {
            "python": self.pip,
            "node": self.npm,
            "go": self.go_mod,
            "rust": self.cargo,
            "java": self.maven,
        }
        manager = manager_map.get(language.lower())
        if manager is None:
            raise PackageManagementError(f"Unsupported package language: {language}")
        result = manager.process({"packages": packages})
        result["auto_update"] = self.auto_update
        result["security_scan"] = self.security_scan
        return result