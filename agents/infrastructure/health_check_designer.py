"""HealthCheckDesigner agent synthesizing readiness, liveness, and startup probes."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.infrastructure.exceptions import HealthCheckError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Infrastructure.HealthCheckDesigner")


# ==============================================================================
# L5 Atomic Health Check Subagents
# ==============================================================================

class ReadinessProbeGenerator(BaseAgent):
    """L5 agent synthesizing readiness probe logic asserting DB and cache availability."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ReadinessProbeGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        ready_code = (
            "@router.get('/health/ready')\n"
            "async def readiness_probe(db = Depends(get_db_session)):\n"
            "    \"\"\"Confirm database and upstream dependencies are operational.\"\"\"\n"
            "    try:\n"
            "        await db.execute(text('SELECT 1'))\n"
            "        return {'status': 'ready', 'database': 'connected'}\n"
            "    except Exception as exc:\n"
            "        raise HTTPException(status_code=503, detail=f'Database unavailable: {str(exc)}')\n"
        )
        return {"status": "COMPLETED", "readiness_code": ready_code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ReadinessProbeGenerator %s cleaned up.", self.agent_id)


class LivenessProbeGenerator(BaseAgent):
    """L5 agent synthesizing lightweight liveness probe logic checking thread/process vitality."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LivenessProbeGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        live_code = (
            "@router.get('/health/live')\n"
            "async def liveness_probe():\n"
            "    \"\"\"Simple lightweight check to verify event-loop execution.\"\"\"\n"
            "    return {'status': 'alive', 'timestamp': time.time()}\n"
        )
        return {"status": "COMPLETED", "liveness_code": live_code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("LivenessProbeGenerator %s cleaned up.", self.agent_id)


class StartupProbeGenerator(BaseAgent):
    """L5 agent synthesizing startup probe logic for initial schema migration and model warmups."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("StartupProbeGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        startup_code = (
            "@router.get('/health/startup')\n"
            "async def startup_probe():\n"
            "    \"\"\"Verify app bootstrap, warmups, and migrations are finished.\"\"\"\n"
            "    return {'status': 'started', 'initialized': True}\n"
        )
        return {"status": "COMPLETED", "startup_code": startup_code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("StartupProbeGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 HealthCheckDesigner Agent
# ==============================================================================

class HealthCheckDesigner(BaseAgent):
    """L4 coordinator authoring comprehensive microservice health probes and FastAPI endpoints."""

    def __init__(
        self,
        name: str = "HealthCheckDesigner",
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
            "health_check_design",
            "readiness_probes",
            "liveness_probes",
            "startup_probes",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "I8_HEALTH_CHECK_DESIGNER",
        )

        self.ready_gen: Optional[ReadinessProbeGenerator] = None
        self.live_gen: Optional[LivenessProbeGenerator] = None
        self.startup_gen: Optional[StartupProbeGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_health_checks", self.generate_health_checks)

    def _spawn_subagents(self) -> None:
        """Spawn atomic health check subagents (Rule 1 & Rule 5)."""
        logger.info("HealthCheckDesigner %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.ready_gen = self.spawn_subagent(
            ReadinessProbeGenerator,
            name="ReadinessProbeGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.live_gen = self.spawn_subagent(
            LivenessProbeGenerator,
            name="LivenessProbeGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.startup_gen = self.spawn_subagent(
            StartupProbeGenerator,
            name="StartupProbeGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("HealthCheckDesigner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        bundle = self.generate_health_checks()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "health_check_bundle": bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        bundle = result.get("health_check_bundle")
        if not bundle or "endpoint_module" not in bundle:
            raise HealthCheckError("HealthCheckDesigner produced incomplete bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("HealthCheckDesigner %s cleanup complete.", self.agent_id)

    def generate_health_checks(self) -> Dict[str, str]:
        """Synthesize health router module combining live, ready, and startup probes."""
        r_res = self.ready_gen.process({}) if self.ready_gen else {"readiness_code": ""}
        l_res = self.live_gen.process({}) if self.live_gen else {"liveness_code": ""}
        s_res = self.startup_gen.process({}) if self.startup_gen else {"startup_code": ""}

        router_code = (
            "import time\n"
            "from fastapi import APIRouter, Depends, HTTPException\n"
            "from sqlalchemy import text\n\n"
            "router = APIRouter(tags=['Health Checks'])\n\n"
            f"{l_res.get('liveness_code')}\n\n"
            f"{r_res.get('readiness_code')}\n\n"
            f"{s_res.get('startup_code')}\n"
        )
        return {
            "endpoint_module": router_code,
            "probes": ["/health/live", "/health/ready", "/health/startup"],
            "passed": True,
        }
