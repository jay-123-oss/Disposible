"""RequirementsDocumenter agent for compiling structured software requirement documents."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from agents.planning.exceptions import PlanningError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Planning.RequirementsDocumenter")


class RequirementsDocumenter(BaseAgent):
    """Generates structured requirements documentation categorized into Functional, Non-Functional, Technical, and Constraints."""

    def __init__(
        self,
        name: str = "RequirementsDocumenter",
        capabilities: Optional[List[str]] = None,
        model: str = "llama3.2:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or [
            "requirements_documentation",
            "requirements_categorization",
            "specification_formatting",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P5_REQUIREMENTS_DOC",
        )
        self.register_tool("document_requirements", self.document_requirements)
        self.register_tool("categorize_requirements", self.categorize_requirements)
        self.register_tool("generate_output", self.generate_output)

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RequirementsDocumenter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        fmt = payload.get("format", "markdown")
        doc_str = self.document_requirements(payload, output_format=fmt)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "format": fmt,
            "document": doc_str,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "document" not in result or not result["document"]:
            raise PlanningError("RequirementsDocumenter produced empty document output.")
        return result

    def cleanup(self) -> None:
        logger.debug("RequirementsDocumenter %s cleaned up.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def document_requirements(self, parsed_data: Dict[str, Any], output_format: str = "markdown") -> str:
        """Categorize raw data and render the formatted requirements specification."""
        categorized = self.categorize_requirements(parsed_data)
        return self.generate_output(categorized, output_format)

    def categorize_requirements(self, reqs: Dict[str, Any]) -> Dict[str, Any]:
        """Group requirements into Functional, Non-Functional, Technical, and Constraints."""
        entities = reqs.get("entities", {})
        project_type = entities.get("project_type") or reqs.get("project_type", "API")
        language = entities.get("language") or reqs.get("language", "python")
        framework = entities.get("framework") or reqs.get("framework", "FastAPI")
        features = entities.get("features") or reqs.get("features", ["Authentication", "CRUD Endpoints"])

        functional = [
            f"Core Capability: Deliver robust {project_type} endpoints.",
            *[f"Feature: Support {f}" for f in features],
            "Data Validation: Strict input typing and automatic error serialization.",
        ]

        non_functional = [
            "Performance: Latency under 200ms for p95 requests.",
            "Security: Zero hardcoded credentials; all inputs parameterized.",
            "Reliability: Automatic error trapping and structured JSON error responses.",
            "Quality: Comprehensive unit tests with >=90% line coverage.",
        ]

        technical = [
            f"Language Runtime: {language} (Python 3.10+ or LTS equivalent)",
            f"Routing Framework: {framework}",
            f"Data Persistence: {entities.get('database', 'SQLite/PostgreSQL')}",
            "Testing Framework: pytest or language standard test runner",
        ]

        constraints = [
            "Hardware ceiling: Must execute within <=8GB system RAM and 512MB per agent.",
            "Zero external daemon dependencies for baseline test runs.",
            "Immutable code commits backed by passing quality gates.",
        ]

        return {
            "title": f"Requirements Specification: {project_type} Project",
            "project_type": project_type,
            "functional_requirements": functional,
            "non_functional_requirements": non_functional,
            "technical_requirements": technical,
            "constraints": constraints,
        }

    def generate_output(self, reqs: Dict[str, Any], format_type: str = "markdown") -> str:
        """Format categorized requirements into Markdown or JSON string."""
        if format_type.lower() == "json":
            return json.dumps(reqs, indent=2)

        # Markdown representation
        md_lines = [
            f"# {reqs.get('title', 'Software Requirements Specification')}",
            "",
            "## 1. Functional Requirements",
        ]
        for f in reqs.get("functional_requirements", []):
            md_lines.append(f"- {f}")

        md_lines.extend(["", "## 2. Non-Functional Requirements"])
        for nf in reqs.get("non_functional_requirements", []):
            md_lines.append(f"- {nf}")

        md_lines.extend(["", "## 3. Technical Requirements"])
        for tr in reqs.get("technical_requirements", []):
            md_lines.append(f"- {tr}")

        md_lines.extend(["", "## 4. Operational Constraints"])
        for c in reqs.get("constraints", []):
            md_lines.append(f"- {c}")

        return "\n".join(md_lines)
