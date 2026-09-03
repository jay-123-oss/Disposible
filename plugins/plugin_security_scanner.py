"""PluginSecurityScanner agent scanning plugins for vulnerabilities, malware, permissions, signatures.

Implements the complete Plugin Security Scanner hierarchy (P8):
- L4 PluginSecurityScanner coordinator
- L5 atomic workers: VulnerabilityScanner, MalwareScanner, PermissionChecker, SignatureVerifier
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from plugins.exceptions import PluginSecurityError


logger = logging.getLogger("FractalCore.PluginSystem.PluginSecurityScanner")

_RISK_PATTERNS = [
    re.compile(r"os\.system\s*\(", re.IGNORECASE),
    re.compile(r"subprocess\.(call|run|Popen)\s*\(", re.IGNORECASE),
    re.compile(r"eval\s*\(", re.IGNORECASE),
    re.compile(r"exec\s*\(", re.IGNORECASE),
    re.compile(r"__import__\s*\(['\"]os['\"]"),
]


# ==============================================================================
# L5 Atomic Plugin Security Scanner Subagents
# ==============================================================================

class VulnerabilityScanner(BaseAgent):
    """L5 agent scanning plugin manifests and code for known vulnerable dependencies."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("VulnerabilityScanner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        dependencies = task_envelope.get("dependencies", [])
        known = task_envelope.get("known_vulnerable", {})
        findings = [d for d in dependencies if d in known]
        return {"status": "COMPLETED", "vulnerabilities_found": len(findings), "findings": findings, "safe": len(findings) == 0}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("VulnerabilityScanner %s cleaned up.", self.agent_id)


class MalwareScanner(BaseAgent):
    """L5 agent scanning plugin source for malware and dangerous system-access patterns."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MalwareScanner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        source = task_envelope.get("source_code", "")
        hits = [pattern.pattern for pattern in _RISK_PATTERNS if pattern.search(source)]
        return {"status": "COMPLETED", "malware_detected": len(hits) > 0, "risk_patterns": hits, "safe": len(hits) == 0}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("MalwareScanner %s cleaned up.", self.agent_id)


class PermissionChecker(BaseAgent):
    """L5 agent verifying a plugin's declared permissions against the requested access set."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PermissionChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        declared = set(task_envelope.get("declared_permissions", []))
        requested = set(task_envelope.get("requested_permissions", []))
        excess = sorted(requested - declared)
        return {"status": "COMPLETED", "allowed": len(excess) == 0, "excess_permissions": excess, "declared": sorted(declared)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PermissionChecker %s cleaned up.", self.agent_id)


class SignatureVerifier(BaseAgent):
    """L5 agent verifying cryptographic signatures of signed plugin packages."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SignatureVerifier %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        archive = task_envelope.get("archive_name", "")
        signature = task_envelope.get("signature", "") or ""
        expected = task_envelope.get("expected_signature", "")
        if not expected and not archive and not signature:
            return {"status": "COMPLETED", "verified": True, "archive": archive, "reason": "no signature verification requested"}
        digest = hashlib.sha256((archive + signature).encode("utf-8")).hexdigest()
        valid = bool(expected) and digest == expected
        return {"status": "COMPLETED", "verified": valid, "archive": archive,
                "reason": "signature match" if valid else "signature mismatch or missing"}


    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SignatureVerifier %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PluginSecurityScanner Agent
# ==============================================================================

class PluginSecurityScanner(BaseAgent):
    """L4 coordinator running the four security dimensions over a plugin."""

    def __init__(
        self,
        name: str = "PluginSecurityScanner",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "plugin_security_scanner",
            "vulnerability_scanner",
            "malware_scanner",
            "permission_checker",
            "signature_verifier",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P8_PLUGIN_SECURITY_SCANNER",
        )
        self.vuln_scanner: Optional[VulnerabilityScanner] = None
        self.malware_scanner: Optional[MalwareScanner] = None
        self.permission_checker: Optional[PermissionChecker] = None
        self.signature_verifier: Optional[SignatureVerifier] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("scan_plugin_security", self.scan_plugin_security)

    def _spawn_subagents(self) -> None:
        """Spawn atomic security scanner subagents (Rule 1 & Rule 5)."""
        logger.info("PluginSecurityScanner %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.vuln_scanner = self.spawn_subagent(VulnerabilityScanner, name="VulnerabilityScanner", max_depth=child_depth, resources_mb=32)
        self.malware_scanner = self.spawn_subagent(MalwareScanner, name="MalwareScanner", max_depth=child_depth, resources_mb=32)
        self.permission_checker = self.spawn_subagent(PermissionChecker, name="PermissionChecker", max_depth=child_depth, resources_mb=32)
        self.signature_verifier = self.spawn_subagent(SignatureVerifier, name="SignatureVerifier", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginSecurityScanner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.scan_plugin_security(payload.get("source_code", ""), payload)
        return {"status": "COMPLETED", "security": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginSecurityScanner %s cleanup complete.", self.agent_id)

    def scan_plugin_security(self, source_code: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Scan a plugin across vulnerability, malware, permission, and signature dimensions."""
        ctx = payload or {}
        logger.info("Scanning plugin security...")
        checks = {
            "vulnerability": self.vuln_scanner.process({"dependencies": ctx.get("dependencies", []), "known_vulnerable": ctx.get("known_vulnerable", {})}) if self.vuln_scanner else {"safe": True},
            "malware": self.malware_scanner.process({"source_code": source_code}) if self.malware_scanner else {"safe": True},
            "permissions": self.permission_checker.process({"declared_permissions": ctx.get("permissions", []), "requested_permissions": ctx.get("requested_permissions", [])}) if self.permission_checker else {"allowed": True},
            "signature": self.signature_verifier.process({"archive_name": ctx.get("archive_name", ""), "signature": ctx.get("signature", ""), "expected_signature": ctx.get("expected_signature", "")}) if self.signature_verifier else {"verified": True},
        }
        safe = all(
            [
                checks["vulnerability"].get("safe", True),
                checks["malware"].get("safe", True),
                checks["permissions"].get("allowed", True),
                checks["signature"].get("verified", True),
            ]
        )
        return {
            "safe": safe,
            "checks": checks,
            "issues": [c for c in checks.values() if not c.get("safe", c.get("allowed", c.get("verified", True)))],
        }