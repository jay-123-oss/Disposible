"""SQLInjectionScanner coordinating query AST pattern detection and parameter binding verification."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.security.exceptions import InjectionVulnerability
from agents.security.sql_subagents import (
    ParameterValidator,
    QueryAnalyzer,
)
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Security.SQLInjectionScanner")


class SQLInjectionScanner(BaseAgent):
    """L4 coordinator scanning source code for SQL injection vulnerabilities and unparameterized statements."""

    def __init__(
        self,
        name: str = "SQLInjectionScanner",
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
            "sql_injection_scanning",
            "query_analysis",
            "parameter_verification",
            "injection_prevention",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "S8_SQL_INJECTION_SCANNER",
        )

        self.query_analyzer: Optional[QueryAnalyzer] = None
        self.parameter_validator: Optional[ParameterValidator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("scan_for_sql_injection", self.scan_for_sql_injection)

    def _spawn_subagents(self) -> None:
        """Spawn QueryAnalyzer and ParameterValidator (Rule 1 & Rule 5)."""
        logger.info("SQLInjectionScanner %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.query_analyzer = self.spawn_subagent(
            QueryAnalyzer,
            name="QueryAnalyzer",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.parameter_validator = self.spawn_subagent(
            ParameterValidator,
            name="ParameterValidator",
            max_depth=child_depth,
            resources_mb=128,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SQLInjectionScanner %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        scan_res = self.scan_for_sql_injection(payload.get("code_snippets"))
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "sql_scan_result": scan_res,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        scan = result.get("sql_scan_result")
        if not scan or "composite_score" not in scan:
            raise InjectionVulnerability("SQLInjectionScanner produced incomplete scan result.")
        return result

    def cleanup(self) -> None:
        logger.debug("SQLInjectionScanner %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def scan_for_sql_injection(self, code_snippets: Optional[List[str]] = None) -> Dict[str, Any]:
        """Aggregate query pattern detection and parameter binding verification."""
        q_res = self.query_analyzer.analyze_queries(code_snippets) if self.query_analyzer else {"score": 100, "flaws_detected": []}
        p_res = self.parameter_validator.validate_parameters() if self.parameter_validator else {"score": 100, "findings": []}

        q_score = q_res.get("score", 100)
        p_score = p_res.get("score", 100)
        composite = round(0.60 * q_score + 0.40 * p_score, 2)

        flaws = q_res.get("flaws_detected", [])
        findings = [
            {
                "severity": f["severity"],
                "issue": f["issue"],
                "snippet": f["snippet"],
                "remediation": "Replace raw SQL string interpolation with SQLAlchemy select()/insert() expressions.",
            }
            for f in flaws
        ]

        return {
            "composite_score": composite,
            "query_analysis": q_res,
            "parameter_validation": p_res,
            "findings": findings,
            "passed": composite >= 85 and len(flaws) == 0,
        }
