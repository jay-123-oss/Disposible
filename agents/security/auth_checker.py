"""AuthChecker coordinating password strength, hashing algorithms, and JWT token security audits."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.security.auth_subagents import (
    PasswordValidator,
    TokenValidator,
)
from agents.security.exceptions import AuthenticationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Security.AuthChecker")


class AuthChecker(BaseAgent):
    """L4 coordinator for identity authentication mechanism audits."""

    def __init__(
        self,
        name: str = "AuthChecker",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 192,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "auth_audit",
            "password_validation",
            "token_verification",
            "mfa_compliance",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "S2_AUTH_CHECKER",
        )

        self.password_validator: Optional[PasswordValidator] = None
        self.token_validator: Optional[TokenValidator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("run_auth_audit", self.run_auth_audit)

    def _spawn_subagents(self) -> None:
        """Spawn PasswordValidator and TokenValidator (Rule 1 & Rule 5)."""
        logger.info("AuthChecker %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.password_validator = self.spawn_subagent(
            PasswordValidator,
            name="PasswordValidator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.token_validator = self.spawn_subagent(
            TokenValidator,
            name="TokenValidator",
            max_depth=child_depth,
            resources_mb=128,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AuthChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.run_auth_audit(payload.get("auth_config"))
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "auth_audit_result": result,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        audit = result.get("auth_audit_result")
        if not audit or "composite_score" not in audit:
            raise AuthenticationError("AuthChecker produced incomplete audit result.")
        return result

    def cleanup(self) -> None:
        logger.debug("AuthChecker %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def run_auth_audit(self, auth_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Aggregate password and token audits into a composite authentication posture."""
        cfg = auth_config or {}
        pwd_res = self.password_validator.audit_passwords(cfg) if self.password_validator else {"score": 95, "findings": []}
        tok_res = self.token_validator.audit_tokens(cfg) if self.token_validator else {"score": 95, "findings": []}

        pwd_score = pwd_res.get("score", 100)
        tok_score = tok_res.get("score", 100)
        composite = round(0.50 * pwd_score + 0.50 * tok_score, 2)

        all_findings = pwd_res.get("findings", []) + tok_res.get("findings", [])

        return {
            "composite_score": composite,
            "password_audit": pwd_res,
            "token_audit": tok_res,
            "findings": all_findings,
            "passed": composite >= 85 and len([f for f in all_findings if f["severity"] == "CRITICAL"]) == 0,
        }
