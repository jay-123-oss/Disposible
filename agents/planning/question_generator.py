"""QuestionGenerator agent for creating prioritized, context-aware clarification questions."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.planning.exceptions import QuestionGenerationError
from agents.planning.knowledge_base import KnowledgeBase
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Planning.QuestionGenerator")


class QuestionGenerator(BaseAgent):
    """Generates structured, category-specific clarification questions based on project context."""

    def __init__(
        self,
        name: str = "QuestionGenerator",
        capabilities: Optional[List[str]] = None,
        model: str = "llama3.2:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or ["question_generation", "followup_querying", "template_lookup"]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "QG_001",
        )
        self._knowledge_base = KnowledgeBase()
        self.register_tool("generate_questions", self.generate_questions)
        self.register_tool("generate_followup", self.generate_followup)
        self.register_tool("get_question_templates", self.get_question_templates)

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("QuestionGenerator %s initialized for task %s", self.agent_id, task_envelope.get("task_id"))

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        context = task_envelope.get("payload", {})
        category = context.get("category")
        current_response = context.get("current_response")

        if current_response:
            questions = self.generate_followup(current_response, context)
        elif category:
            questions = [{"question": q, "priority": "HIGH", "category": category} for q in self.get_question_templates(category)]
        else:
            questions = self.generate_questions(context)

        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "questions_count": len(questions),
            "questions": questions,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "questions" not in result or not isinstance(result["questions"], list):
            raise QuestionGenerationError(
                "Invalid QuestionGenerator output format.",
                details={"result": result, "agent_id": self.agent_id},
            )
        return result

    def cleanup(self) -> None:
        logger.debug("QuestionGenerator %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def generate_questions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prioritized questions based on what is missing in current context."""
        questions: List[Dict[str, Any]] = []

        # Check for Project Type
        if not context.get("project_type"):
            questions.append({
                "id": "Q_PROJ_TYPE",
                "category": "Project Type",
                "question": "What type of project are you building? (API, Web, CLI, Microservice)",
                "options": ["API", "Web", "CLI", "Microservice"],
                "priority": "HIGH",
            })

        # Check for Tech Stack
        if not context.get("language"):
            questions.append({
                "id": "Q_TECH_STACK",
                "category": "Tech Stack",
                "question": "What primary programming language do you prefer? (python, node, go, rust, java)",
                "options": ["python", "node", "go", "rust", "java"],
                "priority": "HIGH",
            })

        # Check for Features
        if not context.get("features"):
            questions.append({
                "id": "Q_FEATURES",
                "category": "Features",
                "question": "What core features are required for the initial MVP? (e.g. auth, database, file upload)",
                "options": ["Authentication", "Database CRUD", "File Storage", "Payment Gateway"],
                "priority": "MEDIUM",
            })

        # Check for Constraints
        if not context.get("constraints"):
            questions.append({
                "id": "Q_CONSTRAINTS",
                "category": "Constraints",
                "question": "What are your deployment or performance constraints? (e.g., <=8GB RAM, Docker, <200ms latency)",
                "options": ["Local Execution (<=8GB RAM)", "Docker Deployment", "High Concurrency (<200ms latency)"],
                "priority": "LOW",
            })

        # Check for Success Criteria
        if not context.get("success_criteria"):
            questions.append({
                "id": "Q_SUCCESS_CRITERIA",
                "category": "Success Criteria",
                "question": "What test coverage percentage is required? (e.g. 80%, 90%, 100%)",
                "options": ["80% Coverage", "90% Coverage", "100% Zero-Defect"],
                "priority": "LOW",
            })

        logger.info("Generated %d questions based on context.", len(questions))
        return questions

    def generate_followup(self, current_response: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Formulate follow-up questions if a previous answer was partial or triggers branching."""
        followups: List[Dict[str, Any]] = []
        resp_lower = current_response.lower()

        if "api" in resp_lower and not context.get("api_spec"):
            followups.append({
                "id": "Q_FOL_API",
                "category": "Features",
                "question": "Will your API use REST with OpenAPI schemas or GraphQL?",
                "options": ["REST (OpenAPI)", "GraphQL"],
                "priority": "HIGH",
            })

        if "auth" in resp_lower and not context.get("auth_type"):
            followups.append({
                "id": "Q_FOL_AUTH",
                "category": "Features",
                "question": "What authentication mechanism is preferred? (JWT Bearer tokens, Session Cookies, OAuth2)",
                "options": ["JWT Bearer", "Session Cookies", "OAuth2"],
                "priority": "HIGH",
            })

        if "database" in resp_lower and not context.get("database_type"):
            followups.append({
                "id": "Q_FOL_DB",
                "category": "Tech Stack",
                "question": "What database technology is required? (PostgreSQL, SQLite, Redis, MongoDB)",
                "options": ["PostgreSQL", "SQLite", "Redis", "MongoDB"],
                "priority": "MEDIUM",
            })

        logger.info("Generated %d follow-up questions.", len(followups))
        return followups

    def get_question_templates(self, category: str) -> List[str]:
        """Retrieve static question templates for a category from the KnowledgeBase."""
        return self._knowledge_base.get_templates_for_category(category)
