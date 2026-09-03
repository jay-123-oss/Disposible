"""RiskAssessor agent for identifying, scoring, and mitigating project engineering risks."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.planning.exceptions import RiskAssessmentError
from agents.planning.knowledge_base import KnowledgeBase
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Planning.RiskAssessor")


class RiskAssessor(BaseAgent):
    """Evaluates project blueprints to identify potential vulnerabilities, compute risk scores, and prescribe mitigations."""

    def __init__(
        self,
        name: str = "RiskAssessor",
        capabilities: Optional[List[str]] = None,
        model: str = "llama3.2:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or [
            "risk_assessment",
            "risk_scoring",
            "mitigation_strategy",
            "threat_modeling",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P9_RISK_ASSESSOR",
        )
        self._knowledge_base = KnowledgeBase()
        self.register_tool("assess_risks", self.assess_risks)
        self.register_tool("calculate_risk_score", self.calculate_risk_score)
        self.register_tool("suggest_mitigation", self.suggest_mitigation)

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RiskAssessor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        assessed_risks = self.assess_risks(payload)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "risks_count": len(assessed_risks),
            "risks": assessed_risks,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        risks = result.get("risks")
        if risks is None or not isinstance(risks, list):
            raise RiskAssessmentError("RiskAssessor returned invalid risk structure.", details={"result": result})
        return result

    def cleanup(self) -> None:
        logger.debug("RiskAssessor %s cleaned up.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def assess_risks(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential failure modes across Technical, Resource, Timeline, and Security categories."""
        risks: List[Dict[str, Any]] = []

        # 1. Technical Risk
        tech_risk = {
            "id": "RSK_TECH_01",
            "name": "Dependency Version Conflicts & API Drift",
            "category": "Technical",
            "probability": 0.4,
            "impact": 0.7,
            "description": "Third-party libraries or language minor versions may introduce subtle breaking changes.",
        }
        tech_risk["score"] = self.calculate_risk_score(tech_risk)
        tech_risk["mitigation"] = self.suggest_mitigation(tech_risk)
        risks.append(tech_risk)

        # 2. Security Risk
        sec_risk = {
            "id": "RSK_SEC_01",
            "name": "Input Injection & Unauthenticated Access",
            "category": "Security",
            "probability": 0.3,
            "impact": 0.9,
            "description": "Missing request payload validation could permit malformed payloads or data leakage.",
        }
        sec_risk["score"] = self.calculate_risk_score(sec_risk)
        sec_risk["mitigation"] = self.suggest_mitigation(sec_risk)
        risks.append(sec_risk)

        # 3. Resource Risk
        res_risk = {
            "id": "RSK_RES_01",
            "name": "Workstation RAM Saturation (>8GB ceiling)",
            "category": "Resource",
            "probability": 0.25,
            "impact": 0.8,
            "description": "Concurrent local agent processes and inference runners may approach memory limits.",
        }
        res_risk["score"] = self.calculate_risk_score(res_risk)
        res_risk["mitigation"] = self.suggest_mitigation(res_risk)
        risks.append(res_risk)

        # 4. Timeline / Quality Risk
        time_risk = {
            "id": "RSK_TIME_01",
            "name": "AI Whack-A-Mole Regression Cascades",
            "category": "Timeline",
            "probability": 0.35,
            "impact": 0.85,
            "description": "Downstream modifications may silently regress previously validated endpoints.",
        }
        time_risk["score"] = self.calculate_risk_score(time_risk)
        time_risk["mitigation"] = self.suggest_mitigation(time_risk)
        risks.append(time_risk)

        # Sort risks descending by score
        risks.sort(key=lambda r: r["score"], reverse=True)
        logger.info("Assessed %d risks with highest score: %.1f", len(risks), risks[0]["score"])
        return risks

    def calculate_risk_score(self, risk: Dict[str, Any]) -> float:
        """Calculate quantitative risk score: Probability (0-1) * Impact (0-1) * 100."""
        prob = float(risk.get("probability", 0.5))
        impact = float(risk.get("impact", 0.5))
        score = prob * impact * 100.0
        return round(score, 1)

    def suggest_mitigation(self, risk: Dict[str, Any]) -> str:
        """Formulate a concrete mitigation strategy based on the risk category and name."""
        category = risk.get("category", "").lower()
        pat = self._knowledge_base.get_risk_pattern(category)
        if pat and pat.get("mitigation"):
            return pat["mitigation"]

        if category == "technical":
            return "Pin exact library versions in requirements.txt / package.json; test in isolated sandbox."
        if category == "security":
            return "Enforce Pydantic DTO schema validation on all endpoints; require SAST gate passage."
        if category == "resource":
            return "Limit agent pool to 10 workers; enforce 512MB RAM cap per process."
        if category == "timeline":
            return "Execute full regression test suite on every git commit; auto-rollback on failure."

        return "Monitor execution telemetry and apply circuit breaker isolation upon anomaly."
