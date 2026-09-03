"""AnswerValidator agent for enforcing answer validity and planning completeness."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from agents.planning.exceptions import ValidationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Planning.AnswerValidator")


class AnswerValidator(BaseAgent):
    """Validates user responses against semantic and syntactic constraints."""

    ALLOWED_PROJECT_TYPES = {"api", "web", "cli", "microservice"}

    def __init__(
        self,
        name: str = "AnswerValidator",
        capabilities: Optional[List[str]] = None,
        model: str = "llama3.2:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["answer_validation", "constraint_checking", "completeness_verification"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "AV_001",
        )
        self.register_tool("validate_response", self.validate_response)
        self.register_tool("check_completeness", self.check_completeness)
        self.register_tool("get_missing_fields", self.get_missing_fields)

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AnswerValidator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        response = payload.get("response")
        rule = payload.get("rule")
        responses_list = payload.get("responses_list")

        if responses_list is not None:
            is_complete = self.check_completeness(responses_list)
            missing = self.get_missing_fields(responses_list)
            return {
                "status": "COMPLETED",
                "agent_id": self.agent_id,
                "is_complete": is_complete,
                "missing_fields": missing,
            }

        valid = self.validate_response(str(response or ""), str(rule or "general"))
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "is_valid": valid,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "is_valid" not in result and "is_complete" not in result:
            raise ValidationError("AnswerValidator output missing validity indicators", details={"result": result})
        return result

    def cleanup(self) -> None:
        logger.debug("AnswerValidator %s cleaned up.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def validate_response(self, response: str, rule: str) -> bool:
        """Validate answer text against a named rule constraint."""
        resp_clean = response.strip().lower()
        rule_lower = rule.strip().lower()

        if not resp_clean:
            return False

        if rule_lower in ("project_type", "project type"):
            # Must be one of [API, Web, CLI, Microservice]
            return any(pt in resp_clean for pt in self.ALLOWED_PROJECT_TYPES)

        if rule_lower in ("tech_stack", "tech stack"):
            # Must specify at least one recognized language or framework
            common_keywords = {"python", "fastapi", "django", "flask", "node", "express", "nestjs", "go", "gin", "rust", "axum", "java", "spring"}
            return any(kw in resp_clean for kw in common_keywords)

        if rule_lower in ("features", "feature list"):
            # Minimum 1, Maximum 10 features
            tokens = [f.strip() for f in re.split(r"[,;\n]", response) if f.strip()]
            return 1 <= len(tokens) <= 10

        if rule_lower in ("constraints",):
            # Free text, not empty
            return len(resp_clean) >= 3

        if rule_lower in ("success_criteria", "success criteria"):
            # Must contain metrics (e.g. percentages, milliseconds, counts)
            has_numbers = bool(re.search(r"\d+", response))
            has_metric_terms = any(term in resp_clean for term in ["%", "ms", "sec", "second", "coverage", "requests", "users", "zero"])
            return has_numbers or has_metric_terms

        return len(resp_clean) > 0

    def check_completeness(self, responses: List[Dict[str, Any]]) -> bool:
        """Check if all required answers have been provided."""
        missing = self.get_missing_fields(responses)
        return len(missing) == 0

    def get_missing_fields(self, responses: List[Dict[str, Any]]) -> List[str]:
        """Return list of essential categories missing from responses."""
        provided_categories = {r.get("category", "").lower() for r in responses if r.get("answer")}
        required_categories = ["project type", "tech stack", "features"]
        missing: List[str] = []

        for req in required_categories:
            if not any(req in cat for cat in provided_categories):
                missing.append(req)

        return missing
