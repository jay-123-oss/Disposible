"""ModelAgent and specialized model agents: UserModel and SessionModel."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.coding.exceptions import ModelGenerationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Coding.ModelAgent")


# ==============================================================================
# L6 Specialized Model Agents
# ==============================================================================

class UserModel(BaseAgent):
    """L6 agent generating SQLAlchemy User entity schema, constraints, and relationships."""

    def __init__(
        self,
        name: str = "UserModel",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["user_model_generation", "schema_definition", "orm_mapping"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C19_USER_MODEL",
        )
        self.register_tool("generate_user_model_code", self.generate_user_model_code)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("UserModel %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        code = self.generate_user_model_code()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "model_name": "User",
            "code": code,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise ModelGenerationError("UserModel produced empty model code.")
        return result

    def cleanup(self) -> None:
        logger.debug("UserModel %s cleaned up.", self.agent_id)

    def generate_user_model_code(self) -> str:
        """Generate SQLAlchemy User declarative model with relations and helpers."""
        return (
            "class User(Base):\n"
            "    __tablename__ = 'users'\n\n"
            "    id = Column(Integer, primary_key=True, index=True, autoincrement=True)\n"
            "    email = Column(String(255), unique=True, nullable=False, index=True)\n"
            "    password_hash = Column(String(255), nullable=False)\n"
            "    is_active = Column(Boolean, default=True, nullable=False)\n"
            "    is_superuser = Column(Boolean, default=False, nullable=False)\n"
            "    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)\n"
            "    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)\n\n"
            "    sessions = relationship('Session', back_populates='user', cascade='all, delete-orphan')\n\n"
            "    @validates('email')\n"
            "    def validate_email(self, key, address):\n"
            "        if '@' not in address:\n"
            "            raise ValueError('Invalid email format')\n"
            "        return address.lower().strip()\n"
        )


class SessionModel(BaseAgent):
    """L6 agent generating SQLAlchemy Session entity schema, token expiry, and foreign keys."""

    def __init__(
        self,
        name: str = "SessionModel",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["session_model_generation", "expiry_handling", "foreign_key_mapping"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C20_SESSION_MODEL",
        )
        self.register_tool("generate_session_model_code", self.generate_session_model_code)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SessionModel %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        code = self.generate_session_model_code()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "model_name": "Session",
            "code": code,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise ModelGenerationError("SessionModel produced empty model code.")
        return result

    def cleanup(self) -> None:
        logger.debug("SessionModel %s cleaned up.", self.agent_id)

    def generate_session_model_code(self) -> str:
        """Generate SQLAlchemy Session declarative model with user foreign key."""
        return (
            "class Session(Base):\n"
            "    __tablename__ = 'sessions'\n\n"
            "    id = Column(String(64), primary_key=True, index=True)\n"
            "    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)\n"
            "    user_agent = Column(String(255), nullable=True)\n"
            "    ip_address = Column(String(45), nullable=True)\n"
            "    expires_at = Column(DateTime, nullable=False, index=True)\n"
            "    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)\n\n"
            "    user = relationship('User', back_populates='sessions')\n\n"
            "    def is_expired(self) -> bool:\n"
            "        return datetime.utcnow() > self.expires_at\n"
        )


# ==============================================================================
# L5 Model Orchestrator Agent
# ==============================================================================

class ModelAgent(BaseAgent):
    """L5 agent coordinating database ORM entities (UserModel, SessionModel)."""

    def __init__(
        self,
        name: str = "ModelAgent",
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
            "orm_modeling",
            "entity_relationship_design",
            "schema_synthesis",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C18_MODEL_AGENT",
        )

        self.user_model: Optional[UserModel] = None
        self.session_model: Optional[SessionModel] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_model_subagents()

        self.register_tool("generate_models", self.generate_models)

    def _spawn_model_subagents(self) -> None:
        """Spawn UserModel and SessionModel (Rule 1 & Rule 5)."""
        logger.info("ModelAgent %s spawning subagents (UserModel, SessionModel)...", self.agent_id)
        child_depth = self.depth + 2
        self.user_model = self.spawn_subagent(
            UserModel,
            name="UserModel",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.session_model = self.spawn_subagent(
            SessionModel,
            name="SessionModel",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ModelAgent %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        bundle = self.generate_models()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "models_bundle": bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "models_bundle" not in result or not result["models_bundle"].get("full_code"):
            raise ModelGenerationError("ModelAgent produced incomplete model bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("ModelAgent %s cleanup complete.", self.agent_id)

    def generate_models(self) -> Dict[str, Any]:
        """Synthesize all entity models into a database models module."""
        codes: List[str] = [
            "from datetime import datetime",
            "from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey",
            "from sqlalchemy.orm import declarative_base, relationship, validates",
            "",
            "Base = declarative_base()",
            "",
        ]

        if self.user_model:
            user_res = self.user_model.process({})
            codes.append(user_res["code"])

        if self.session_model:
            session_res = self.session_model.process({})
            codes.append(session_res["code"])

        full_code = "\n\n".join(codes)
        return {
            "models": ["User", "Session"],
            "full_code": full_code,
        }
