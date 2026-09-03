"""Security Domain Agents for the Fractal Multi-Agent Coding System.

Exports all 16 specialized security agents and atomic subagents across levels L3 to L6,
along with the registration helper `register_all_security_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from agents.security.auth_checker import AuthChecker
from agents.security.auth_subagents import (
    BreachChecker,
    HashVerifier,
    PasswordValidator,
    StrengthChecker,
    TokenValidator,
)
from agents.security.compliance_checker import (
    BreachNotificationChecker,
    ComplianceChecker,
    ConsentChecker,
    DataPrivacyChecker,
    GdprChecker,
    HipaaChecker,
)
from agents.security.csrf_checker import (
    CSRFChecker,
    HeaderVerifier,
    ReferrerValidator,
    StateValidator,
    TokenChecker,
)
from agents.security.encryption_validator import (
    AlgorithmChecker,
    CipherStrengthChecker,
    EncryptionValidator,
    KeyManager,
    ModeValidator,
)
from agents.security.exceptions import (
    AuthenticationError,
    ComplianceError,
    CSRFVulnerability,
    EncryptionError,
    InjectionVulnerability,
    PermissionError,
    SecurityError,
    XSSVulnerability,
)
from agents.security.permission_auditor import PermissionAuditor
from agents.security.permission_subagents import (
    ClaimVerifier,
    PolicyEnforcer,
    RbacValidator,
    RoleChecker,
)
from agents.security.security_orchestrator import SecurityOrchestrator
from agents.security.sql_injection_scanner import SQLInjectionScanner
from agents.security.sql_subagents import (
    ParameterValidator,
    PatternDetector,
    QueryAnalyzer,
    RiskScorer,
)
from agents.security.xss_scanner import XSSScanner
from agents.security.xss_subagents import (
    HtmlEncoder,
    InputSanitizer,
    JsEncoder,
    OutputEncoder,
    UrlEncoder,
)
from core.registry import AgentRegistry


logger = logging.getLogger("FractalCore.Security")

__all__ = [
    # Orchestrator
    "SecurityOrchestrator",
    # Authentication Audit
    "AuthChecker",
    "PasswordValidator",
    "TokenValidator",
    "StrengthChecker",
    "HashVerifier",
    "BreachChecker",
    # Authorization & Permissions
    "PermissionAuditor",
    "RoleChecker",
    "PolicyEnforcer",
    "RbacValidator",
    "ClaimVerifier",
    # Injection Scanning
    "SQLInjectionScanner",
    "QueryAnalyzer",
    "ParameterValidator",
    "PatternDetector",
    "RiskScorer",
    # Cross-Site Scripting (XSS)
    "XSSScanner",
    "OutputEncoder",
    "InputSanitizer",
    "HtmlEncoder",
    "JsEncoder",
    "UrlEncoder",
    # CSRF Defenses
    "CSRFChecker",
    "TokenChecker",
    "HeaderVerifier",
    "StateValidator",
    "ReferrerValidator",
    # Cryptography & Encryption
    "EncryptionValidator",
    "AlgorithmChecker",
    "CipherStrengthChecker",
    "ModeValidator",
    "KeyManager",
    # Regulatory Compliance
    "ComplianceChecker",
    "GdprChecker",
    "HipaaChecker",
    "DataPrivacyChecker",
    "ConsentChecker",
    "BreachNotificationChecker",
    # Exceptions
    "SecurityError",
    "AuthenticationError",
    "PermissionError",
    "InjectionVulnerability",
    "XSSVulnerability",
    "CSRFVulnerability",
    "EncryptionError",
    "ComplianceError",
    # Registration Helper
    "register_all_security_agents",
]


def register_all_security_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Register all 16 security layer agents into the AgentRegistry.

    Args:
        registry: The central AgentRegistry singleton.
        parent_agent: Optional supervising security domain coordinator.
        max_depth: Global depth ceiling for security hierarchy.

    Returns:
        Dict mapping agent_id to instantiated agent instances.
    """
    logger.info("Registering all security domain agents into AgentRegistry...")

    # Root Security Orchestrator (L3)
    security_orchestrator = SecurityOrchestrator(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="S1_SECURITY_ORCHESTRATOR",
        auto_spawn_subagents=True,
    )
    registry.register_agent(security_orchestrator)

    # Register all spawned children recursively
    registered_count = 1
    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(security_orchestrator)

    logger.info("Successfully registered %d security domain agents into registry.", registered_count)
    return {
        "security_orchestrator": security_orchestrator,
        "total_registered": registered_count,
    }
