"""QueryAgent and specialized query builders: SelectQuery, InsertQuery, and UpdateQuery."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.coding.exceptions import QueryGenerationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Coding.QueryAgent")


# ==============================================================================
# L6 Specialized Query Builders
# ==============================================================================

class SelectQuery(BaseAgent):
    """L6 agent generating parameterized SELECT and find queries with filters and joins."""

    def __init__(
        self,
        name: str = "SelectQuery",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["select_query_builder", "where_clause_builder", "join_builder"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C22_SELECT_QUERY",
        )
        self.register_tool("build_select", self.build_select)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SelectQuery %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        model_name = payload.get("model_name", "User")
        query_code = self.build_select(model_name)
        return {"status": "COMPLETED", "agent_id": self.agent_id, "code": query_code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise QueryGenerationError("SelectQuery produced empty query code.")
        return result

    def cleanup(self) -> None:
        logger.debug("SelectQuery %s cleaned up.", self.agent_id)

    def build_select(self, model_name: str = "User") -> str:
        """Generate parameterized find and list queries."""
        return (
            f"async def find_{model_name.lower()}_by_id(db: AsyncSession, entity_id: int) -> Optional[{model_name}]:\n"
            f"    stmt = select({model_name}).where({model_name}.id == entity_id)\n"
            f"    res = await db.execute(stmt)\n"
            f"    return res.scalars().first()\n\n"
            f"async def list_{model_name.lower()}s(db: AsyncSession, limit: int = 20, offset: int = 0) -> list[{model_name}]:\n"
            f"    stmt = select({model_name}).order_by({model_name}.id.desc()).limit(limit).offset(offset)\n"
            f"    res = await db.execute(stmt)\n"
            f"    return list(res.scalars().all())\n"
        )


class InsertQuery(BaseAgent):
    """L6 agent generating parameterized INSERT statements with RETURNING clauses."""

    def __init__(
        self,
        name: str = "InsertQuery",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["insert_query_builder", "value_builder", "returning_builder"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C23_INSERT_QUERY",
        )
        self.register_tool("build_insert", self.build_insert)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("InsertQuery %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        model_name = payload.get("model_name", "User")
        query_code = self.build_insert(model_name)
        return {"status": "COMPLETED", "agent_id": self.agent_id, "code": query_code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise QueryGenerationError("InsertQuery produced empty query code.")
        return result

    def cleanup(self) -> None:
        logger.debug("InsertQuery %s cleaned up.", self.agent_id)

    def build_insert(self, model_name: str = "User") -> str:
        """Generate transactional insert query."""
        return (
            f"async def create_{model_name.lower()}(db: AsyncSession, attributes: dict) -> {model_name}:\n"
            f"    record = {model_name}(**attributes)\n"
            f"    db.add(record)\n"
            f"    await db.commit()\n"
            f"    await db.refresh(record)\n"
            f"    return record\n"
        )


class UpdateQuery(BaseAgent):
    """L6 agent generating parameterized UPDATE statements with SET and WHERE clauses."""

    def __init__(
        self,
        name: str = "UpdateQuery",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["update_query_builder", "set_builder", "conditional_updater"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "UPDATE_QUERY",
        )
        self.register_tool("build_update", self.build_update)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("UpdateQuery %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        model_name = payload.get("model_name", "User")
        query_code = self.build_update(model_name)
        return {"status": "COMPLETED", "agent_id": self.agent_id, "code": query_code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise QueryGenerationError("UpdateQuery produced empty query code.")
        return result

    def cleanup(self) -> None:
        logger.debug("UpdateQuery %s cleaned up.", self.agent_id)

    def build_update(self, model_name: str = "User") -> str:
        """Generate atomic update query."""
        return (
            f"async def update_{model_name.lower()}(db: AsyncSession, entity_id: int, updates: dict) -> Optional[{model_name}]:\n"
            f"    stmt = update({model_name}).where({model_name}.id == entity_id).values(**updates).execution_options(synchronize_session='fetch')\n"
            f"    await db.execute(stmt)\n"
            f"    await db.commit()\n"
            f"    return await find_{model_name.lower()}_by_id(db, entity_id)\n"
        )


# ==============================================================================
# L5 Query Orchestrator Agent
# ==============================================================================

class QueryAgent(BaseAgent):
    """L5 agent coordinating SQL query synthesis across Select, Insert, and Update builders."""

    def __init__(
        self,
        name: str = "QueryAgent",
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
            "query_orchestration",
            "sql_generation",
            "injection_prevention",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C21_QUERY_AGENT",
        )

        self.select_query: Optional[SelectQuery] = None
        self.insert_query: Optional[InsertQuery] = None
        self.update_query: Optional[UpdateQuery] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_query_subagents()

        self.register_tool("generate_crud_queries", self.generate_crud_queries)

    def _spawn_query_subagents(self) -> None:
        """Spawn SelectQuery, InsertQuery, and UpdateQuery (Rule 1 & Rule 5)."""
        logger.info("QueryAgent %s spawning query subagents (Select, Insert, Update)...", self.agent_id)
        child_depth = self.depth + 2
        self.select_query = self.spawn_subagent(
            SelectQuery,
            name="SelectQuery",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.insert_query = self.spawn_subagent(
            InsertQuery,
            name="InsertQuery",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.update_query = self.spawn_subagent(
            UpdateQuery,
            name="UpdateQuery",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("QueryAgent %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        model_name = payload.get("model_name", "User")
        queries = self.generate_crud_queries(model_name)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "queries_bundle": queries,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "queries_bundle" not in result or not result["queries_bundle"].get("full_code"):
            raise QueryGenerationError("QueryAgent produced incomplete query bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("QueryAgent %s cleanup complete.", self.agent_id)

    def generate_crud_queries(self, model_name: str = "User") -> Dict[str, Any]:
        """Generate comprehensive CRUD repository functions for the entity."""
        codes: List[str] = [
            "from typing import Optional",
            "from sqlalchemy import select, update, delete",
            "from sqlalchemy.ext.asyncio import AsyncSession",
            f"from app.models.{model_name.lower()} import {model_name}",
            "",
        ]

        if self.select_query:
            sel_res = self.select_query.process({"payload": {"model_name": model_name}})
            codes.append(sel_res["code"])

        if self.insert_query:
            ins_res = self.insert_query.process({"payload": {"model_name": model_name}})
            codes.append(ins_res["code"])

        if self.update_query:
            upd_res = self.update_query.process({"payload": {"model_name": model_name}})
            codes.append(upd_res["code"])

        full_code = "\n\n".join(codes)
        return {
            "model_name": model_name,
            "operations": ["select", "insert", "update"],
            "full_code": full_code,
        }
