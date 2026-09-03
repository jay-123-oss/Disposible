"""ComposeGenerator agent assembling multi-container docker-compose specifications."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.infrastructure.exceptions import ComposeError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Infrastructure.ComposeGenerator")


# ==============================================================================
# L5 Atomic Compose Subagents
# ==============================================================================

class ServiceDefiner(BaseAgent):
    """L5 agent defining containerized microservices: API, PostgreSQL, and Redis."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ServiceDefiner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        services_yaml = (
            "services:\n"
            "  api:\n"
            "    build:\n"
            "      context: .\n"
            "      dockerfile: Dockerfile\n"
            "    ports:\n"
            "      - \"8000:8000\"\n"
            "    environment:\n"
            "      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/appdb\n"
            "      - REDIS_URL=redis://cache:6379/0\n"
            "    depends_on:\n"
            "      db:\n"
            "        condition: service_healthy\n"
            "      cache:\n"
            "        condition: service_started\n"
            "    networks:\n"
            "      - frontend\n"
            "      - backend\n"
            "    restart: unless-stopped\n\n"
            "  db:\n"
            "    image: postgres:15-alpine\n"
            "    environment:\n"
            "      - POSTGRES_USER=postgres\n"
            "      - POSTGRES_PASSWORD=postgres\n"
            "      - POSTGRES_DB=appdb\n"
            "    volumes:\n"
            "      - postgres_data:/var/lib/postgresql/data\n"
            "    healthcheck:\n"
            "      test: [\"CMD-SHELL\", \"pg_isready -U postgres\"]\n"
            "      interval: 10s\n"
            "      timeout: 5s\n"
            "      retries: 5\n"
            "    networks:\n"
            "      - backend\n\n"
            "  cache:\n"
            "    image: redis:7-alpine\n"
            "    command: redis-server --appendonly yes\n"
            "    volumes:\n"
            "      - redis_data:/data\n"
            "    networks:\n"
            "      - backend\n"
        )
        return {"status": "COMPLETED", "services_yaml": services_yaml}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ServiceDefiner %s cleaned up.", self.agent_id)


class NetworkDefiner(BaseAgent):
    """L5 agent configuring isolated bridge networks for frontend routing and backend storage."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NetworkDefiner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        networks_yaml = (
            "networks:\n"
            "  frontend:\n"
            "    driver: bridge\n"
            "  backend:\n"
            "    driver: bridge\n"
            "    internal: true\n"
        )
        return {"status": "COMPLETED", "networks_yaml": networks_yaml}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NetworkDefiner %s cleaned up.", self.agent_id)


class VolumeDefiner(BaseAgent):
    """L5 agent defining persistent local and cloud storage volumes."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("VolumeDefiner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        volumes_yaml = (
            "volumes:\n"
            "  postgres_data:\n"
            "  redis_data:\n"
        )
        return {"status": "COMPLETED", "volumes_yaml": volumes_yaml}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("VolumeDefiner %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 ComposeGenerator Agent
# ==============================================================================

class ComposeGenerator(BaseAgent):
    """L4 coordinator generating docker-compose orchestration files."""

    def __init__(
        self,
        name: str = "ComposeGenerator",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "compose_generation",
            "service_definition",
            "network_isolation",
            "volume_management",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "I3_COMPOSE_GENERATOR",
        )

        self.service_def: Optional[ServiceDefiner] = None
        self.network_def: Optional[NetworkDefiner] = None
        self.volume_def: Optional[VolumeDefiner] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_compose", self.generate_compose)

    def _spawn_subagents(self) -> None:
        """Spawn atomic compose subagents (Rule 1 & Rule 5)."""
        logger.info("ComposeGenerator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.service_def = self.spawn_subagent(
            ServiceDefiner,
            name="ServiceDefiner",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.network_def = self.spawn_subagent(
            NetworkDefiner,
            name="NetworkDefiner",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.volume_def = self.spawn_subagent(
            VolumeDefiner,
            name="VolumeDefiner",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ComposeGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        compose_text = self.generate_compose()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "docker_compose_yaml": compose_text,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "docker_compose_yaml" not in result:
            raise ComposeError("ComposeGenerator produced empty docker-compose file.")
        return result

    def cleanup(self) -> None:
        logger.debug("ComposeGenerator %s cleanup complete.", self.agent_id)

    def generate_compose(self) -> str:
        """Synthesize docker-compose.yml combining services, networks, and volumes."""
        s_res = self.service_def.process({}) if self.service_def else {"services_yaml": "services: {}"}
        n_res = self.network_def.process({}) if self.network_def else {"networks_yaml": "networks: {}"}
        v_res = self.volume_def.process({}) if self.volume_def else {"volumes_yaml": "volumes: {}"}

        full_compose = (
            "version: '3.8'\n\n"
            f"{s_res.get('services_yaml')}\n"
            f"{n_res.get('networks_yaml')}\n"
            f"{v_res.get('volumes_yaml')}\n"
        )
        return full_compose
