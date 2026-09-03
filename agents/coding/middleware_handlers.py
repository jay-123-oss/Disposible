"""Middleware handler agents: AuthMiddleware, LoggingMiddleware, RateLimiter with sub-handlers."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.coding.exceptions import MiddlewareGenerationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Coding.MiddlewareHandlers")


# ==============================================================================
# L5 Specialized Middleware Agents
# ==============================================================================

class AuthMiddleware(BaseAgent):
    """L5 agent generating JWT bearer token validation and user injection middleware."""

    def __init__(
        self,
        name: str = "AuthMiddleware",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["jwt_auth_middleware", "token_verification", "rbac_enforcement"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C8_AUTH_MIDDLEWARE",
        )
        self.register_tool("generate_auth_code", self.generate_auth_code)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AuthMiddleware %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        code = self.generate_auth_code()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "middleware_type": "authentication",
            "code": code,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise MiddlewareGenerationError("AuthMiddleware produced empty code.")
        return result

    def cleanup(self) -> None:
        logger.debug("AuthMiddleware %s cleaned up.", self.agent_id)

    def generate_auth_code(self) -> str:
        """Generate JWT authentication middleware function."""
        return (
            "async def auth_middleware(request: Request, call_next):\n"
            "    # Skip public paths\n"
            "    public_paths = ['/docs', '/redoc', '/openapi.json', '/api/v1/auth/login', '/api/v1/auth/register']\n"
            "    if any(request.url.path.startswith(p) for p in public_paths):\n"
            "        return await call_next(request)\n\n"
            "    auth_header = request.headers.get('Authorization', '')\n"
            "    if not auth_header.startswith('Bearer '):\n"
            "        return JSONResponse(status_code=401, content={'detail': 'Missing or invalid Authorization header'})\n\n"
            "    token = auth_header.replace('Bearer ', '').strip()\n"
            "    try:\n"
            "        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])\n"
            "        user_id = payload.get('sub')\n"
            "        if not user_id:\n"
            "            return JSONResponse(status_code=401, content={'detail': 'Invalid token payload'})\n"
            "        request.state.current_user_id = user_id\n"
            "        request.state.user_roles = payload.get('roles', ['user'])\n"
            "    except (JWTError, Exception) as err:\n"
            "        return JSONResponse(status_code=401, content={'detail': f'Authentication failure: {str(err)}'})\n\n"
            "    response = await call_next(request)\n"
            "    return response\n"
        )


class LoggingMiddleware(BaseAgent):
    """L5 agent generating structured request/response duration and audit logging middleware."""

    def __init__(
        self,
        name: str = "LoggingMiddleware",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["logging_middleware", "request_tracing", "duration_monitoring"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C9_LOGGING_MIDDLEWARE",
        )
        self.register_tool("generate_logging_code", self.generate_logging_code)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LoggingMiddleware %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        code = self.generate_logging_code()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "middleware_type": "logging",
            "code": code,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise MiddlewareGenerationError("LoggingMiddleware produced empty code.")
        return result

    def cleanup(self) -> None:
        logger.debug("LoggingMiddleware %s cleaned up.", self.agent_id)

    def generate_logging_code(self) -> str:
        """Generate structured logging middleware function."""
        return (
            "async def logging_middleware(request: Request, call_next):\n"
            "    start_time = time.time()\n"
            "    req_id = str(uuid.uuid4())\n"
            "    request.state.request_id = req_id\n"
            "    logger.info(f'[START] Req {req_id} - {request.method} {request.url.path}')\n\n"
            "    response = await call_next(request)\n\n"
            "    duration_ms = round((time.time() - start_time) * 1000, 2)\n"
            "    response.headers['X-Request-ID'] = req_id\n"
            "    response.headers['X-Response-Time-Ms'] = str(duration_ms)\n"
            "    logger.info(f'[END] Req {req_id} - Status {response.status_code} in {duration_ms}ms')\n"
            "    return response\n"
        )


class RateLimiter(BaseAgent):
    """L5 agent generating in-memory / redis token-bucket rate limiting middleware."""

    def __init__(
        self,
        name: str = "RateLimiter",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["rate_limiting", "request_throttling", "client_ip_tracking"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C10_RATE_LIMITER",
        )
        self.register_tool("generate_rate_limit_code", self.generate_rate_limit_code)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RateLimiter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        max_req = payload.get("max_requests", 100)
        window_s = payload.get("window_seconds", 60)
        code = self.generate_rate_limit_code(max_requests=max_req, window_seconds=window_s)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "middleware_type": "rate_limiting",
            "code": code,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result or not result["code"]:
            raise MiddlewareGenerationError("RateLimiter produced empty code.")
        return result

    def cleanup(self) -> None:
        logger.debug("RateLimiter %s cleaned up.", self.agent_id)

    def generate_rate_limit_code(self, max_requests: int = 100, window_seconds: int = 60) -> str:
        """Generate sliding window rate-limiting middleware."""
        return (
            "from collections import defaultdict\n"
            "_rate_limit_store = defaultdict(list)\n\n"
            f"async def rate_limit_middleware(request: Request, call_next):\n"
            f"    client_ip = request.client.host if request.client else 'anonymous'\n"
            f"    now = time.time()\n"
            f"    window_cutoff = now - {window_seconds}\n\n"
            f"    # Prune old timestamps\n"
            f"    _rate_limit_store[client_ip] = [t for t in _rate_limit_store[client_ip] if t > window_cutoff]\n\n"
            f"    if len(_rate_limit_store[client_ip]) >= {max_requests}:\n"
            f"        return JSONResponse(status_code=429, content={{'detail': 'Too Many Requests - Rate limit exceeded'}})\n\n"
            f"    _rate_limit_store[client_ip].append(now)\n"
            f"    return await call_next(request)\n"
        )
