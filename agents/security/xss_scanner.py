"""XSSScanner coordinating output encoding and input sanitization audits."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.security.exceptions import XSSVulnerability
from agents.security.xss_subagents import (
    InputSanitizer,
    OutputEncoder,
)
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Security.XSSScanner")


class XSSScanner(BaseAgent):
    """L4 coordinator scanning templates and handlers for Cross-Site Scripting (XSS) weaknesses."""

    def __init__(
        self,
        name: str = "XSSScanner",
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
            "xss_scanning",
            "output_encoding_verification",
            "input_sanitization_check",
            "csp_validation",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "S11_XSS_SCANNER",
        )

        self.output_encoder: Optional[OutputEncoder] = None
        self.input_sanitizer: Optional[InputSanitizer] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("scan_for_xss", self.scan_for_xss)

    def _spawn_subagents(self) -> None:
        """Spawn OutputEncoder and InputSanitizer (Rule 1 & Rule 5)."""
        logger.info("XSSScanner %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.output_encoder = self.spawn_subagent(
            OutputEncoder,
            name="OutputEncoder",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.input_sanitizer = self.spawn_subagent(
            InputSanitizer,
            name="InputSanitizer",
            max_depth=child_depth,
            resources_mb=128,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("XSSScanner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        scan_res = self.scan_for_xss(payload.get("raw_inputs"))
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "xss_scan_result": scan_res,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        scan = result.get("xss_scan_result")
        if not scan or "composite_score" not in scan:
            raise XSSVulnerability("XSSScanner produced incomplete scan result.")
        return result

    def cleanup(self) -> None:
        logger.debug("XSSScanner %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def scan_for_xss(self, raw_inputs: Optional[List[str]] = None) -> Dict[str, Any]:
        """Aggregate output encoding and input sanitization scores."""
        o_res = self.output_encoder.audit_output_encoding() if self.output_encoder else {"score": 100, "findings": []}
        i_res = self.input_sanitizer.audit_input_sanitization(raw_inputs) if self.input_sanitizer else {"score": 100, "findings": []}

        o_score = o_res.get("score", 100)
        i_score = i_res.get("score", 100)
        composite = round(0.50 * o_score + 0.50 * i_score, 2)

        findings = o_res.get("findings", []) + i_res.get("findings", [])

        return {
            "composite_score": composite,
            "output_encoding": o_res,
            "input_sanitization": i_res,
            "findings": findings,
            "passed": composite >= 85 and len([f for f in findings if f["severity"] == "CRITICAL"]) == 0,
        }
