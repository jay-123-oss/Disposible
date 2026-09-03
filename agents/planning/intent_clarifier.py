"""IntentClarifier agent for detecting user intent, extracting entities, and spawning sub-agents."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from agents.planning.answer_validator import AnswerValidator
from agents.planning.exceptions import IntentClarificationError
from agents.planning.option_parser import OptionParser
from agents.planning.question_generator import QuestionGenerator
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Planning.IntentClarifier")


class IntentClarifier(BaseAgent):
    """L2 Planning Agent that disambiguates user requirements and manages clarification sub-agents."""

    def __init__(
        self,
        name: str = "IntentClarifier",
        capabilities: Optional[List[str]] = None,
        model: str = "llama3.2:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "intent_detection",
            "entity_extraction",
            "ambiguity_detection",
            "clarification_coordination",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P1_INTENT_CLARIFIER",
        )

        self.register_tool("clarify_intent", self.clarify_intent)
        self.register_tool("detect_intents", self.detect_intents)
        self.register_tool("calculate_confidence", self.calculate_confidence)
        self.register_tool("extract_entities", self.extract_entities)

        # Sub-agents (L3)
        self.question_generator: Optional[QuestionGenerator] = None
        self.option_parser: Optional[OptionParser] = None
        self.answer_validator: Optional[AnswerValidator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_planning_subagents()

    def _spawn_planning_subagents(self) -> None:
        """Spawn specialized child sub-agents (Rule 1 & Rule 5)."""
        logger.info("IntentClarifier %s spawning clarification subagents (QG, OP, AV)...", self.agent_id)
        self.question_generator = self.spawn_subagent(
            QuestionGenerator,
            name="QuestionGenerator",
            agent_id=f"QG_{self.agent_id[:6]}",
        )
        self.option_parser = self.spawn_subagent(
            OptionParser,
            name="OptionParser",
            agent_id=f"OP_{self.agent_id[:6]}",
        )
        self.answer_validator = self.spawn_subagent(
            AnswerValidator,
            name="AnswerValidator",
            agent_id=f"AV_{self.agent_id[:6]}",
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("IntentClarifier %s initialized for task %s", self.agent_id, task_envelope.get("task_id"))

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        user_input = task_envelope.get("intent", "")
        if not user_input:
            user_input = task_envelope.get("payload", {}).get("user_input", "")

        clarified = self.clarify_intent(user_input)

        # If clarification is needed and QuestionGenerator is available, attach clarifying questions
        if clarified["clarification_needed"] and self.question_generator:
            questions = self.question_generator.generate_questions(clarified["entities"])
            clarified["clarification_questions"] = questions

        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "clarification": clarified,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        clarification = result.get("clarification")
        if not clarification or "confidence_score" not in clarification:
            raise IntentClarificationError(
                "IntentClarifier produced malformed result.",
                details={"result": result, "agent_id": self.agent_id},
            )
        return result

    def cleanup(self) -> None:
        logger.debug("IntentClarifier %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def clarify_intent(self, user_input: str) -> Dict[str, Any]:
        """Analyze user prompt, detect intents, score confidence, and extract key entities."""
        if not user_input or not user_input.strip():
            raise IntentClarificationError("Cannot clarify empty user input.")

        intents = self.detect_intents(user_input)
        confidence = self.calculate_confidence(intents)
        entities = self.extract_entities(user_input)

        ambiguities: List[str] = []
        if not entities.get("project_type"):
            ambiguities.append("Target project type (API, Web, CLI, Microservice) is unspecified.")
        if not entities.get("language"):
            ambiguities.append("Programming language or runtime is unspecified.")
        if not entities.get("features"):
            ambiguities.append("No specific feature requirements or endpoints declared.")

        clarification_needed = len(ambiguities) > 0 or confidence < 70.0

        return {
            "original_input": user_input,
            "detected_intents": intents,
            "confidence_score": confidence,
            "ambiguities": ambiguities,
            "clarification_needed": clarification_needed,
            "entities": entities,
        }

    def detect_intents(self, text: str) -> List[str]:
        """Detect operational intents using semantic keyword mapping."""
        intents: List[str] = []
        lower_text = text.lower()

        patterns = {
            "build_api": ["api", "rest", "endpoint", "crud", "graphql", "route", "http"],
            "build_web_ui": ["frontend", "ui", "web", "html", "react", "dashboard", "page"],
            "build_cli": ["cli", "terminal", "command line", "script", "tool", "console"],
            "database_modeling": ["database", "schema", "table", "sql", "migration", "orm", "postgres", "sqlite"],
            "authentication": ["auth", "jwt", "login", "password", "register", "token", "session"],
            "testing": ["test", "pytest", "unit test", "mock", "coverage"],
            "docker_deployment": ["docker", "container", "deploy", "dockerfile", "cicd"],
        }

        for intent_name, keywords in patterns.items():
            if any(re.search(r"\b" + re.escape(kw) + r"\b", lower_text) for kw in keywords):
                intents.append(intent_name)

        if not intents:
            intents.append("general_software_development")

        logger.debug("Detected intents: %s", intents)
        return intents

    def calculate_confidence(self, intents: List[str]) -> float:
        """Compute confidence score between 0.0 and 100.0 based on intent clarity."""
        if not intents or intents == ["general_software_development"]:
            return 40.0
        # More concrete detected intents correlate with higher clarity
        score = min(98.0, 50.0 + (len(intents) * 15.0))
        return round(score, 1)

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract domain entities (project_type, language, framework, database, features)."""
        entities: Dict[str, Any] = {
            "project_type": None,
            "language": None,
            "framework": None,
            "database": None,
            "features": [],
            "constraints": [],
        }
        lower = text.lower()

        # Project Type Detection
        if re.search(r"\b(api|rest|microservice)\b", lower):
            entities["project_type"] = "API"
        elif re.search(r"\b(web|frontend|ui|website)\b", lower):
            entities["project_type"] = "Web"
        elif re.search(r"\b(cli|terminal|console|script)\b", lower):
            entities["project_type"] = "CLI"

        # Language Detection
        languages = ["python", "node", "javascript", "typescript", "go", "rust", "java"]
        for lang in languages:
            if re.search(r"\b" + lang + r"\b", lower):
                entities["language"] = "node" if lang in ("javascript", "typescript") else lang
                break

        # Framework Detection
        frameworks = ["fastapi", "django", "flask", "express", "nestjs", "gin", "axum", "spring"]
        for fw in frameworks:
            if re.search(r"\b" + fw + r"\b", lower):
                entities["framework"] = fw.capitalize()
                break

        # Database Detection
        databases = ["postgres", "postgresql", "sqlite", "mysql", "mongodb", "redis"]
        for db in databases:
            if re.search(r"\b" + db + r"\b", lower):
                entities["database"] = "PostgreSQL" if "postgres" in db else db.capitalize()
                break

        # Features Detection
        feature_candidates = [
            ("Authentication", ["auth", "login", "jwt", "session"]),
            ("Database Storage", ["database", "crud", "storage", "models"]),
            ("File Upload", ["upload", "files", "attachment"]),
            ("Docker Packaging", ["docker", "container", "compose"]),
            ("Rate Limiting", ["rate limit", "throttle"]),
        ]
        for feat_name, kws in feature_candidates:
            if any(re.search(r"\b" + kw + r"\b", lower) for kw in kws):
                entities["features"].append(feat_name)

        return entities
