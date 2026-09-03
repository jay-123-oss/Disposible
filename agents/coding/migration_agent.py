"""MigrationAgent and specialized DDL agents: CreateTable, AlterTable, and DropTable."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.coding.exceptions import MigrationGenerationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Coding.MigrationAgent")


# ==============================================================================
# L6 Specialized DDL Builders
# ==============================================================================

class CreateTable(BaseAgent):
    """L6 agent generating reversible DDL for table creation."""

    def __init__(
        self,
        name: str = "CreateTable",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["create_table_ddl", "schema_definition"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "CREATE_TABLE",
        )
        self.register_tool("build_create_table", self.build_create_table)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CreateTable %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        table = payload.get("table_name", "users")
        code = self.build_create_table(table)
        return {"status": "COMPLETED", "agent_id": self.agent_id, "code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise MigrationGenerationError("CreateTable produced empty DDL code.")
        return result

    def cleanup(self) -> None:
        logger.debug("CreateTable %s cleaned up.", self.agent_id)

    def build_create_table(self, table_name: str = "users") -> str:
        """Generate op.create_table Alembic revision call."""
        return (
            f"    op.create_table(\n"
            f"        '{table_name}',\n"
            f"        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),\n"
            f"        sa.Column('email', sa.String(length=255), nullable=False),\n"
            f"        sa.Column('password_hash', sa.String(length=255), nullable=False),\n"
            f"        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),\n"
            f"        sa.PrimaryKeyConstraint('id'),\n"
            f"        sa.UniqueConstraint('email')\n"
            f"    )\n"
            f"    op.create_index(op.f('ix_{table_name}_email'), '{table_name}', ['email'], unique=True)\n"
        )


class AlterTable(BaseAgent):
    """L6 agent generating non-locking column additions and alterations."""

    def __init__(
        self,
        name: str = "AlterTable",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["alter_table_ddl", "schema_evolution"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "ALTER_TABLE",
        )
        self.register_tool("build_alter_table", self.build_alter_table)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AlterTable %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        table = payload.get("table_name", "users")
        col = payload.get("column_name", "is_active")
        code = self.build_alter_table(table, col)
        return {"status": "COMPLETED", "agent_id": self.agent_id, "code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise MigrationGenerationError("AlterTable produced empty DDL code.")
        return result

    def cleanup(self) -> None:
        logger.debug("AlterTable %s cleaned up.", self.agent_id)

    def build_alter_table(self, table_name: str = "users", column_name: str = "is_active") -> str:
        """Generate op.add_column Alembic revision call."""
        return (
            f"    op.add_column('{table_name}', sa.Column('{column_name}', sa.Boolean(), server_default='true', nullable=False))\n"
        )


class DropTable(BaseAgent):
    """L6 agent generating safe downgrade DROP TABLE DDL."""

    def __init__(
        self,
        name: str = "DropTable",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["drop_table_ddl", "migration_rollback"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "DROP_TABLE",
        )
        self.register_tool("build_drop_table", self.build_drop_table)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DropTable %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        table = payload.get("table_name", "users")
        code = self.build_drop_table(table)
        return {"status": "COMPLETED", "agent_id": self.agent_id, "code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise MigrationGenerationError("DropTable produced empty DDL code.")
        return result

    def cleanup(self) -> None:
        logger.debug("DropTable %s cleaned up.", self.agent_id)

    def build_drop_table(self, table_name: str = "users") -> str:
        """Generate op.drop_table Alembic downgrade call."""
        return f"    op.drop_table('{table_name}')\n"


# ==============================================================================
# L5 Migration Orchestrator Agent
# ==============================================================================

class MigrationAgent(BaseAgent):
    """L5 agent coordinating schema evolution and reversible Alembic migration scripts."""

    def __init__(
        self,
        name: str = "MigrationAgent",
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
            "migration_orchestration",
            "schema_versioning",
            "rollback_generation",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C24_MIGRATION_AGENT",
        )

        self.create_table: Optional[CreateTable] = None
        self.alter_table: Optional[AlterTable] = None
        self.drop_table: Optional[DropTable] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_migration_subagents()

        self.register_tool("generate_migration_script", self.generate_migration_script)

    def _spawn_migration_subagents(self) -> None:
        """Spawn CreateTable, AlterTable, and DropTable (Rule 1 & Rule 5)."""
        logger.info("MigrationAgent %s spawning subagents (CreateTable, AlterTable, DropTable)...", self.agent_id)
        child_depth = self.depth + 2
        self.create_table = self.spawn_subagent(
            CreateTable,
            name="CreateTable",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.alter_table = self.spawn_subagent(
            AlterTable,
            name="AlterTable",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.drop_table = self.spawn_subagent(
            DropTable,
            name="DropTable",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MigrationAgent %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        revision_id = payload.get("revision_id", "0001_initial_schema")
        table_name = payload.get("table_name", "users")
        migration_code = self.generate_migration_script(revision_id, table_name)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "revision_id": revision_id,
            "migration_code": migration_code,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "migration_code" not in result or not result["migration_code"]:
            raise MigrationGenerationError("MigrationAgent produced empty migration script.")
        return result

    def cleanup(self) -> None:
        logger.debug("MigrationAgent %s cleanup complete.", self.agent_id)

    def generate_migration_script(self, revision_id: str = "0001_initial", table_name: str = "users") -> str:
        """Generate a complete Alembic migration script with upgrade() and downgrade()."""
        create_code = self.create_table.build_create_table(table_name) if self.create_table else ""
        drop_code = self.drop_table.build_drop_table(table_name) if self.drop_table else ""

        return (
            f"\"\"\"Revision ID: {revision_id}\n"
            f"Create {table_name} table\n\"\"\"\n"
            f"from alembic import op\n"
            f"import sqlalchemy as sa\n\n"
            f"revision = '{revision_id}'\n"
            f"down_revision = None\n"
            f"branch_labels = None\n"
            f"depends_on = None\n\n"
            f"def upgrade() -> None:\n"
            f"{create_code}\n"
            f"def downgrade() -> None:\n"
            f"{drop_code}\n"
        )
