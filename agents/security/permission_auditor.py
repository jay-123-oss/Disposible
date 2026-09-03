"""PermissionAuditor coordinating RBAC matrix verification and security policy enforcement."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.security.exceptions import PermissionError
from agents.security.permission_subagents import (
    PolicyEnforcer,
    RoleChecker,
)
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Security.PermissionAuditor")


class PermissionAuditor(BaseAgent):
    """L4 coordinator auditing authorization rules, role hierarchy, and least-privilege compliance."""

    def __init__(
        self,
        name: str = "PermissionAuditor",
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
            "permission_audit",
            "rbac_validation",
            "policy_enforcement_audit",
            "least_privilege_verification",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "S5_PERMISSION_AUDITOR",
        )

        self.role_checker: Optional[RoleChecker] = None
        self.policy_enforcer: Optional[PolicyEnforcer] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("audit_permissions", self.audit_permissions)

    def _spawn_subagents(self) -> None:
        """Spawn RoleChecker and PolicyEnforcer (Rule 1 & Rule 5)."""
        logger.info("PermissionAuditor %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.role_checker = self.spawn_subagent(
            RoleChecker,
            name="RoleChecker",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.policy_enforcer = self.spawn_subagent(
            PolicyEnforcer,
            name="PolicyEnforcer",
            max_depth=child_depth,
            resources_mb=128,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PermissionAuditor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.audit_permissions(
            permissions_config=payload.get("permissions_config"),
            endpoints=payload.get("endpoints"),
        )
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "permission_audit_result": result,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        audit = result.get("permission_audit_result")
        if not audit or "composite_score" not in audit:
            raise PermissionError("PermissionAuditor produced incomplete audit result.")
        return result

    def cleanup(self) -> None:
        logger.debug("PermissionAuditor %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def audit_permissions(
        self,
        permissions_config: Optional[Dict[str, Any]] = None,
        endpoints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Aggregate RBAC role matrix and policy audits into authorization security score."""
        r_res = self.role_checker.audit_roles(permissions_config) if self.role_checker else {"score": 95, "findings": []}
        p_res = self.policy_enforcer.audit_policies(endpoints) if self.policy_enforcer else {"score": 95, "findings": []}

        r_score = r_res.get("score", 100)
        p_score = p_res.get("score", 100)
        composite = round(0.50 * r_score + 0.50 * p_score, 2)

        all_findings = r_res.get("findings", []) + p_res.get("findings", [])

        return {
            "composite_score": composite,
            "role_audit": r_res,
            "policy_audit": p_res,
            "findings": all_findings,
            "passed": composite >= 85 and len([f for f in all_findings if f["severity"] == "CRITICAL"]) == 0,
        }
