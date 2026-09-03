"""ServiceAgent and specialized business services: AuthService and UserService."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.coding.exceptions import ServiceGenerationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Coding.ServiceAgent")


# ==============================================================================
# L5 Specialized Service Agents
# ==============================================================================

class AuthService(BaseAgent):
    """L5 agent generating credential validation, password hashing, and token issue services."""

    def __init__(
        self,
        name: str = "AuthService",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["auth_service", "password_hashing", "token_issuance"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C15_AUTH_SERVICE",
        )
        self.register_tool("generate_auth_service_code", self.generate_auth_service_code)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AuthService %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        code = self.generate_auth_service_code()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "service_name": "AuthService",
            "code": code,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise ServiceGenerationError("AuthService produced empty service code.")
        return result

    def cleanup(self) -> None:
        logger.debug("AuthService %s cleaned up.", self.agent_id)

    def generate_auth_service_code(self) -> str:
        """Generate business service handling password hashing and JWT issuance."""
        return (
            "class AuthService:\n"
            "    def __init__(self, user_repo: UserRepository, secret_key: str, algorithm: str = 'HS256'):\n"
            "        self.user_repo = user_repo\n"
            "        self.secret_key = secret_key\n"
            "        self.algorithm = algorithm\n\n"
            "    async def register_user(self, email: str, password: str, db: AsyncSession):\n"
            "        \"\"\"Check uniqueness, hash password with bcrypt, and persist user entity.\"\"\"\n"
            "        existing = await self.user_repo.find_by_email(email, db=db)\n"
            "        if existing:\n"
            "            raise ValueError('Email address already registered')\n\n"
            "        hashed = pwd_context.hash(password)\n"
            "        user = await self.user_repo.create({'email': email, 'password_hash': hashed}, db=db)\n"
            "        token = self._create_jwt_token(user.id, roles=['user'])\n"
            "        return user, token\n\n"
            "    async def login_user(self, email: str, password: str, db: AsyncSession) -> Optional[str]:\n"
            "        \"\"\"Verify credentials against constant-time hash comparator.\"\"\"\n"
            "        user = await self.user_repo.find_by_email(email, db=db)\n"
            "        if not user or not pwd_context.verify(password, user.password_hash):\n"
            "            return None\n"
            "        return self._create_jwt_token(user.id, roles=['user'])\n\n"
            "    def _create_jwt_token(self, user_id: int, roles: list) -> str:\n"
            "        expire = datetime.utcnow() + timedelta(hours=24)\n"
            "        payload = {'sub': str(user_id), 'roles': roles, 'exp': expire}\n"
            "        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)\n\n"
            "    async def revoke_token(self, token: str) -> None:\n"
            "        # Token blacklist or cache eviction\n"
            "        pass\n"
        )


class UserService(BaseAgent):
    """L5 agent generating user lifecycle and profile management services."""

    def __init__(
        self,
        name: str = "UserService",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["user_service", "profile_management", "account_crud"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C16_USER_SERVICE",
        )
        self.register_tool("generate_user_service_code", self.generate_user_service_code)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("UserService %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        code = self.generate_user_service_code()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "service_name": "UserService",
            "code": code,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise ServiceGenerationError("UserService produced empty service code.")
        return result

    def cleanup(self) -> None:
        logger.debug("UserService %s cleaned up.", self.agent_id)

    def generate_user_service_code(self) -> str:
        """Generate user profile lookup, update, and soft deletion service logic."""
        return (
            "class UserService:\n"
            "    def __init__(self, user_repo: UserRepository):\n"
            "        self.user_repo = user_repo\n\n"
            "    async def get_by_id(self, user_id: int, db: AsyncSession):\n"
            "        \"\"\"Retrieve user record by primary key.\"\"\"\n"
            "        return await self.user_repo.find_by_id(user_id, db=db)\n\n"
            "    async def update(self, user_id: int, updates: dict, db: AsyncSession):\n"
            "        \"\"\"Apply validated attribute updates with optimistic concurrency.\"\"\"\n"
            "        return await self.user_repo.update(user_id, updates, db=db)\n\n"
            "    async def delete(self, user_id: int, db: AsyncSession) -> bool:\n"
            "        \"\"\"Execute soft delete on user record.\"\"\"\n"
            "        return await self.user_repo.delete(user_id, db=db)\n"
        )


# ==============================================================================
# L4 Service Orchestrator Agent
# ==============================================================================

class ServiceAgent(BaseAgent):
    """L4 agent coordinating business domain services (AuthService, UserService)."""

    def __init__(
        self,
        name: str = "ServiceAgent",
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
            "service_orchestration",
            "business_logic_assembly",
            "transaction_management",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C14_SERVICE_AGENT",
        )

        self.auth_service: Optional[AuthService] = None
        self.user_service: Optional[UserService] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_service_subagents()

        self.register_tool("generate_services", self.generate_services)

    def _spawn_service_subagents(self) -> None:
        """Spawn AuthService and UserService (Rule 1 & Rule 5)."""
        logger.info("ServiceAgent %s spawning subagents (AuthService, UserService)...", self.agent_id)
        child_depth = self.depth + 2
        self.auth_service = self.spawn_subagent(
            AuthService,
            name="AuthService",
            max_depth=child_depth,
            resources_mb=192,
        )
        self.user_service = self.spawn_subagent(
            UserService,
            name="UserService",
            max_depth=child_depth,
            resources_mb=192,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ServiceAgent %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        bundle = self.generate_services()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "services_bundle": bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "services_bundle" not in result or not result["services_bundle"].get("full_code"):
            raise ServiceGenerationError("ServiceAgent produced incomplete service bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("ServiceAgent %s cleanup complete.", self.agent_id)

    def generate_services(self) -> Dict[str, Any]:
        """Synthesize all domain services into a cohesive services module."""
        codes: List[str] = [
            "from typing import Optional",
            "from datetime import datetime, timedelta",
            "from jose import jwt",
            "from passlib.context import CryptContext",
            "from sqlalchemy.ext.asyncio import AsyncSession",
            "",
            "pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')",
            "",
        ]

        if self.auth_service:
            auth_res = self.auth_service.process({})
            codes.append(auth_res["code"])

        if self.user_service:
            user_res = self.user_service.process({})
            codes.append(user_res["code"])

        full_code = "\n\n".join(codes)
        return {
            "services": ["AuthService", "UserService"],
            "full_code": full_code,
        }
