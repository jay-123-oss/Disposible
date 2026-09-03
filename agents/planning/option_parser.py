"""OptionParser agent for mapping free-text user answers to formal choices."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from agents.planning.exceptions import ValidationError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Planning.OptionParser")


class OptionParser(BaseAgent):
    """Parses raw user input strings and maps them to standard configuration options."""

    def __init__(
        self,
        name: str = "OptionParser",
        capabilities: Optional[List[str]] = None,
        model: str = "llama3.2:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["option_parsing", "fuzzy_choice_mapping", "choice_extraction"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "OP_001",
        )
        self.register_tool("parse_response", self.parse_response)
        self.register_tool("map_to_options", self.map_to_options)
        self.register_tool("extract_choices", self.extract_choices)

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("OptionParser %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        raw_text = payload.get("response", "")
        expected_type = payload.get("expected_type", "string")

        parsed = self.parse_response(raw_text, expected_type)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "result": parsed,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "result" not in result or "parsed_value" not in result["result"]:
            raise ValidationError("OptionParser output missing parsed_value", details={"result": result})
        return result

    def cleanup(self) -> None:
        logger.debug("OptionParser %s cleaned up.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def parse_response(self, response: str, expected_type: str = "string") -> Dict[str, Any]:
        """Parse raw response string into structured value with confidence."""
        cleaned = response.strip()
        if not cleaned:
            return {
                "parsed_value": None,
                "confidence": 0.0,
                "alternative_interpretations": [],
            }

        expected_type_lower = expected_type.lower()

        if expected_type_lower in ("list", "choices", "array"):
            choices = self.extract_choices(cleaned)
            return {
                "parsed_value": choices,
                "confidence": 0.95 if choices else 0.5,
                "alternative_interpretations": [cleaned],
            }

        if expected_type_lower in ("bool", "boolean"):
            affirmative = {"yes", "y", "true", "1", "enable", "definitely", "sure", "correct"}
            negative = {"no", "n", "false", "0", "disable", "never"}
            tokens = set(re.findall(r"\w+", cleaned.lower()))
            is_true = bool(tokens & affirmative) and not bool(tokens & negative)
            is_false = bool(tokens & negative) and not bool(tokens & affirmative)
            val = True if is_true else (False if is_false else None)
            return {
                "parsed_value": val,
                "confidence": 0.95 if val is not None else 0.4,
                "alternative_interpretations": [cleaned],
            }

        if expected_type_lower in ("int", "integer", "number"):
            digits = re.findall(r"\d+", cleaned)
            val = int(digits[0]) if digits else None
            return {
                "parsed_value": val,
                "confidence": 0.95 if val is not None else 0.3,
                "alternative_interpretations": [cleaned],
            }

        # Default string handling
        return {
            "parsed_value": cleaned,
            "confidence": 0.90,
            "alternative_interpretations": [],
        }

    def map_to_options(self, response: str, options: List[str]) -> str:
        """Map a free-text response to the closest matching option string."""
        if not options:
            return response.strip()

        resp_clean = response.strip().lower()

        # 1. Exact match
        for opt in options:
            if opt.lower() == resp_clean:
                return opt

        # 2. Substring match
        for opt in options:
            if opt.lower() in resp_clean or resp_clean in opt.lower():
                return opt

        # 3. Default fallback to first option
        logger.warning("Could not definitively map '%s' to %s. Defaulting to '%s'.", response, options, options[0])
        return options[0]

    def extract_choices(self, response: str) -> List[str]:
        """Extract multi-choice list items from comma, semicolon, or newline-delimited text."""
        # Split by comma, semicolon, newline, or 'and'
        tokens = re.split(r"[,;\n\+]|\band\b", response, flags=re.IGNORECASE)
        results: List[str] = []
        for t in tokens:
            cleaned = t.strip()
            if cleaned and cleaned not in results:
                results.append(cleaned)
        return results
