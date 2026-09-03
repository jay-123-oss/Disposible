"""TechStackSelector agent for recommending languages, frameworks, and libraries."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.planning.exceptions import TechStackSelectionError
from agents.planning.knowledge_base import KnowledgeBase
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Planning.TechStackSelector")


class TechStackSelector(BaseAgent):
    """Evaluates project requirements and selects the optimal programming language, framework, and libraries."""

    def __init__(
        self,
        name: str = "TechStackSelector",
        capabilities: Optional[List[str]] = None,
        model: str = "llama3.2:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        default_caps = capabilities or [
            "tech_stack_selection",
            "framework_recommendation",
            "library_analysis",
            "compatibility_assessment",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P6_TECH_STACK_SELECTOR",
        )
        self._knowledge_base = KnowledgeBase()
        self.register_tool("select_language", self.select_language)
        self.register_tool("select_framework", self.select_framework)
        self.register_tool("suggest_libraries", self.suggest_libraries)

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TechStackSelector %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        lang_info = self.select_language(payload)
        lang = lang_info["language"]
        fw_info = self.select_framework(lang, payload)
        libs = self.suggest_libraries(payload.get("features", []), lang)

        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "language_selection": lang_info,
            "framework_selection": fw_info,
            "recommended_libraries": libs,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "language_selection" not in result or "framework_selection" not in result:
            raise TechStackSelectionError("TechStackSelector produced incomplete recommendation.", details={"result": result})
        return result

    def cleanup(self) -> None:
        logger.debug("TechStackSelector %s cleaned up.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def select_language(self, reqs: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the most appropriate programming language given constraints."""
        entities = reqs.get("entities", {})
        explicit_lang = entities.get("language") or reqs.get("language")

        if explicit_lang:
            lang_key = explicit_lang.lower()
            info = self._knowledge_base.get_tech_stack_info(lang_key)
            return {
                "language": lang_key,
                "version": "3.10+" if lang_key == "python" else "LTS",
                "reasoning": f"User explicitly specified {lang_key.capitalize()}.",
                "alternatives": [k for k in ["python", "node", "go"] if k != lang_key],
            }

        # Heuristic determination based on project type
        proj_type = (entities.get("project_type") or reqs.get("project_type", "API")).lower()
        if proj_type == "web":
            selected = "node"
            reason = "Node.js offers seamless fullstack JavaScript/TypeScript integration for web applications."
            alternatives = ["python", "go"]
        elif proj_type in ("cli", "api", "microservice"):
            selected = "python"
            reason = "Python 3.10+ provides supreme developer velocity, rich typing, and native async support."
            alternatives = ["go", "node", "rust"]
        else:
            selected = "python"
            reason = "Default high-productivity general purpose language."
            alternatives = ["node", "go"]

        return {
            "language": selected,
            "version": "3.10+" if selected == "python" else "LTS",
            "reasoning": reason,
            "alternatives": alternatives,
        }

    def select_framework(self, language: str, reqs: Dict[str, Any]) -> Dict[str, Any]:
        """Select a framework based on language and performance/concurrency needs."""
        info = self._knowledge_base.get_tech_stack_info(language)
        if not info:
            return {
                "framework": "Standard Library",
                "reasoning": f"No specialized framework profile for {language}; standard tools recommended.",
            }

        default_fw = info.get("default_framework", info.get("frameworks", ["Custom"])[0])
        return {
            "framework": default_fw,
            "supported_frameworks": info.get("frameworks", []),
            "orm": info.get("orm", []),
            "test_framework": info.get("test_framework", "pytest"),
            "reasoning": f"{default_fw} provides optimal balance of performance, strict typing, and ecosystem support for {language}.",
        }

    def suggest_libraries(self, requirements: List[str], language: str) -> List[Dict[str, str]]:
        """Suggest specific battle-tested libraries matching required feature domains."""
        info = self._knowledge_base.get_tech_stack_info(language)
        if not info:
            return []

        lib_map = info.get("libraries", {})
        suggestions: List[Dict[str, str]] = []

        req_str = " ".join(requirements).lower()

        if any(w in req_str for w in ["auth", "jwt", "login", "user"]):
            for lib in lib_map.get("auth", []):
                suggestions.append({"library": lib, "category": "Authentication & Cryptography"})

        if any(w in req_str for w in ["validation", "schema", "dto", "type"]):
            for lib in lib_map.get("validation", []):
                suggestions.append({"library": lib, "category": "Data Validation"})

        if any(w in req_str for w in ["http", "network", "client", "request"]):
            for lib in lib_map.get("networking", []):
                suggestions.append({"library": lib, "category": "HTTP Client / Networking"})

        # Default standard libraries if none matched
        if not suggestions:
            for cat, libs in lib_map.items():
                if libs:
                    suggestions.append({"library": libs[0], "category": cat.capitalize()})

        return suggestions
