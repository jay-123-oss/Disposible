"""ControllerAgent and specialized controllers: AuthController and UserController."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.coding.exceptions import ControllerGenerationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Coding.ControllerAgent")


# ==============================================================================
# L5 Specialized Controllers
# ==============================================================================

class AuthController(BaseAgent):
    """L5 agent generating controllers for register, login, and logout actions."""

    def __init__(
        self,
        name: str = "AuthController",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["auth_controller", "register_handler", "login_handler", "logout_handler"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C12_AUTH_CONTROLLER",
        )
        self.register_tool("generate_auth_controller_code", self.generate_auth_controller_code)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AuthController %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        code = self.generate_auth_controller_code()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "controller_name": "AuthController",
            "code": code,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise ControllerGenerationError("AuthController produced empty code output.")
        return result

    def cleanup(self) -> None:
        logger.debug("AuthController %s cleaned up.", self.agent_id)

    def generate_auth_controller_code(self) -> str:
        """Generate controller methods for registration, login, and logout."""
        return (
            "class AuthController:\n"
            "    def __init__(self, auth_service: AuthService):\n"
            "        self.auth_service = auth_service\n\n"
            "    async def handle_register(self, payload: UserRegisterRequest, db: AsyncSession) -> AuthResponse:\n"
            "        \"\"\"Handle user account registration.\"\"\"\n"
            "        try:\n"
            "            user, token = await self.auth_service.register_user(\n"
            "                email=payload.email, password=payload.password, db=db\n"
            "            )\n"
            "            return AuthResponse(user=user, access_token=token, token_type='bearer')\n"
            "        except ValueError as err:\n"
            "            raise HTTPException(status_code=400, detail=str(err))\n\n"
            "    async def handle_login(self, payload: UserLoginRequest, db: AsyncSession) -> AuthResponse:\n"
            "        \"\"\"Handle user authentication and token creation.\"\"\"\n"
            "        token = await self.auth_service.login_user(\n"
            "            email=payload.email, password=payload.password, db=db\n"
            "        )\n"
            "        if not token:\n"
            "            raise HTTPException(status_code=401, detail='Invalid email or password')\n"
            "        return AuthResponse(access_token=token, token_type='bearer')\n\n"
            "    async def handle_logout(self, token: str) -> dict:\n"
            "        \"\"\"Handle token revocation or session invalidation.\"\"\"\n"
            "        await self.auth_service.revoke_token(token)\n"
            "        return {'status': 'success', 'message': 'Successfully logged out'}\n"
        )


class UserController(BaseAgent):
    """L5 agent generating controllers for user profile CRUD operations."""

    def __init__(
        self,
        name: str = "UserController",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["user_controller", "profile_management", "account_lifecycle"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C13_USER_CONTROLLER",
        )
        self.register_tool("generate_user_controller_code", self.generate_user_controller_code)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("UserController %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        code = self.generate_user_controller_code()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "controller_name": "UserController",
            "code": code,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise ControllerGenerationError("UserController produced empty code output.")
        return result

    def cleanup(self) -> None:
        logger.debug("UserController %s cleaned up.", self.agent_id)

    def generate_user_controller_code(self) -> str:
        """Generate controller methods for profile retrieval, update, and deletion."""
        return (
            "class UserController:\n"
            "    def __init__(self, user_service: UserService):\n"
            "        self.user_service = user_service\n\n"
            "    async def get_profile(self, user_id: int, db: AsyncSession) -> UserResponse:\n"
            "        \"\"\"Retrieve public user profile.\"\"\"\n"
            "        user = await self.user_service.get_by_id(user_id, db=db)\n"
            "        if not user:\n"
            "            raise HTTPException(status_code=404, detail='User not found')\n"
            "        return UserResponse.model_validate(user)\n\n"
            "    async def update_profile(self, user_id: int, payload: UserUpdateRequest, db: AsyncSession) -> UserResponse:\n"
            "        \"\"\"Update existing user profile attributes.\"\"\"\n"
            "        updated = await self.user_service.update(user_id, payload.model_dump(exclude_unset=True), db=db)\n"
            "        if not updated:\n"
            "            raise HTTPException(status_code=404, detail='User not found')\n"
            "        return UserResponse.model_validate(updated)\n\n"
            "    async def delete_user(self, user_id: int, db: AsyncSession) -> dict:\n"
            "        \"\"\"Deactivate or delete user account.\"\"\"\n"
            "        success = await self.user_service.delete(user_id, db=db)\n"
            "        if not success:\n"
            "            raise HTTPException(status_code=404, detail='User not found')\n"
            "        return {'status': 'deleted', 'user_id': user_id}\n"
        )


# ==============================================================================
# L4 Controller Orchestrator Agent
# ==============================================================================

class ControllerAgent(BaseAgent):
    """L4 agent coordinating application controllers (AuthController, UserController)."""

    def __init__(
        self,
        name: str = "ControllerAgent",
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
            "controller_orchestration",
            "request_routing",
            "response_packaging",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C11_CONTROLLER_AGENT",
        )

        self.auth_controller: Optional[AuthController] = None
        self.user_controller: Optional[UserController] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_controller_subagents()

        self.register_tool("generate_controllers", self.generate_controllers)

    def _spawn_controller_subagents(self) -> None:
        """Spawn AuthController and UserController (Rule 1 & Rule 5)."""
        logger.info("ControllerAgent %s spawning subagents (AuthController, UserController)...", self.agent_id)
        child_depth = self.depth + 2
        self.auth_controller = self.spawn_subagent(
            AuthController,
            name="AuthController",
            max_depth=child_depth,
            resources_mb=192,
        )
        self.user_controller = self.spawn_subagent(
            UserController,
            name="UserController",
            max_depth=child_depth,
            resources_mb=192,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ControllerAgent %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        bundle = self.generate_controllers()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "controllers_bundle": bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "controllers_bundle" not in result or not result["controllers_bundle"].get("full_code"):
            raise ControllerGenerationError("ControllerAgent produced incomplete controller bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("ControllerAgent %s cleanup complete.", self.agent_id)

    def generate_controllers(self) -> Dict[str, Any]:
        """Synthesize all controllers into a cohesive controllers module."""
        codes: List[str] = [
            "from typing import Optional",
            "from fastapi import HTTPException",
            "from sqlalchemy.ext.asyncio import AsyncSession",
            "",
        ]

        if self.auth_controller:
            auth_res = self.auth_controller.process({})
            codes.append(auth_res["code"])

        if self.user_controller:
            user_res = self.user_controller.process({})
            codes.append(user_res["code"])

        full_code = "\n\n".join(codes)
        return {
            "controllers": ["AuthController", "UserController"],
            "full_code": full_code,
        }
