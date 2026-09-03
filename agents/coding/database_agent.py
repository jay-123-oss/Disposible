"""DatabaseAgent coordinating models, queries, migrations, and database session engines."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.coding.exceptions import DatabaseGenerationError
from agents.coding.migration_agent import MigrationAgent
from agents.coding.model_agent import ModelAgent
from agents.coding.query_agent import QueryAgent
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Coding.DatabaseAgent")


class DatabaseAgent(BaseAgent):
    """L4 agent coordinating data persistence, ORM models, CRUD repositories, and DDL migrations."""

    def __init__(
        self,
        name: str = "DatabaseAgent",
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
            "database_coordination",
            "orm_management",
            "query_assembly",
            "migration_control",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C17_DATABASE_AGENT",
        )

        self.model_agent: Optional[ModelAgent] = None
        self.query_agent: Optional[QueryAgent] = None
        self.migration_agent: Optional[MigrationAgent] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_database_subagents()

        self.register_tool("generate_models", self.generate_models)
        self.register_tool("generate_queries", self.generate_queries)
        self.register_tool("generate_database_bundle", self.generate_database_bundle)

    def _spawn_database_subagents(self) -> None:
        """Spawn ModelAgent, QueryAgent, and MigrationAgent (Rule 1 & Rule 5)."""
        logger.info("DatabaseAgent %s spawning subagents (ModelAgent, QueryAgent, MigrationAgent)...", self.agent_id)
        child_depth = self.depth + 2
        self.model_agent = self.spawn_subagent(
            ModelAgent,
            name="ModelAgent",
            max_depth=child_depth,
            resources_mb=192,
        )
        self.query_agent = self.spawn_subagent(
            QueryAgent,
            name="QueryAgent",
            max_depth=child_depth,
            resources_mb=192,
        )
        self.migration_agent = self.spawn_subagent(
            MigrationAgent,
            name="MigrationAgent",
            max_depth=child_depth,
            resources_mb=192,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DatabaseAgent %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        bundle = self.generate_database_bundle(
            model_name=payload.get("model_name", "User"),
            engine_url=payload.get("engine_url", "sqlite+aiosqlite:///./app.db"),
        )
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "database_bundle": bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "database_bundle" not in result or not result["database_bundle"].get("session_code"):
            raise DatabaseGenerationError("DatabaseAgent produced incomplete database bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("DatabaseAgent %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def generate_models(self, schema: Optional[Dict[str, Any]] = None) -> str:
        """Generate declarative models code."""
        if self.model_agent:
            res = self.model_agent.process({"payload": {"schema": schema}})
            return res["models_bundle"]["full_code"]
        return "# Models placeholder"

    def generate_queries(self, model: str = "User", operations: Optional[List[str]] = None) -> str:
        """Generate repository queries for a model."""
        if self.query_agent:
            res = self.query_agent.process({"payload": {"model_name": model}})
            return res["queries_bundle"]["full_code"]
        return f"# Queries for {model}"

    def generate_database_bundle(
        self,
        model_name: str = "User",
        engine_url: str = "sqlite+aiosqlite:///./app.db",
    ) -> Dict[str, Any]:
        """Generate async engine setup, models, and queries into a complete database layer."""
        session_code = (
            "from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession\n\n"
            f"DATABASE_URL = '{engine_url}'\n"
            "engine = create_async_engine(DATABASE_URL, echo=False, future=True)\n"
            "async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)\n\n"
            "async def get_db_session():\n"
            "    async with async_session_factory() as session:\n"
            "        try:\n"
            "            yield session\n"
            "        finally:\n"
            "            await session.close()\n"
        )

        models_code = self.generate_models()
        queries_code = self.generate_queries(model_name)
        migration_code = ""
        if self.migration_agent:
            mig_res = self.migration_agent.process({"payload": {"table_name": f"{model_name.lower()}s"}})
            migration_code = mig_res["migration_code"]

        return {
            "session_code": session_code,
            "models_code": models_code,
            "queries_code": queries_code,
            "migration_code": migration_code,
        }
