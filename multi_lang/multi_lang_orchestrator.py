"""MultiLanguageOrchestrator (M1) L3 agent coordinating all 13 multi-language support subsystems.

Spawns the complete M2-M14 hierarchy:
- 5 language generators (python, node, go, rust, java)
- LanguageDetector, LanguageTranslator, CrossLanguageValidator
- PackageManager, FrameworkSelector, DependencyResolver
- CodeFormatter, DocumentationGenerator
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from multi_lang.code_formatter import CodeFormatter
from multi_lang.cross_language_validator import CrossLanguageValidator
from multi_lang.dependency_resolver import DependencyResolver
from multi_lang.documentation_generator import DocumentationGenerator
from multi_lang.exceptions import MultiLanguageError
from multi_lang.framework_selector import FrameworkSelector
from multi_lang.go_generator import GoGenerator
from multi_lang.java_generator import JavaGenerator
from multi_lang.language_detector import LanguageDetector
from multi_lang.language_translator import LanguageTranslator
from multi_lang.node_generator import NodeGenerator
from multi_lang.package_manager import PackageManager
from multi_lang.python_generator import PythonGenerator
from multi_lang.rust_generator import RustGenerator


logger = logging.getLogger("FractalCore.MultiLang.MultiLanguageOrchestrator")


class MultiLanguageOrchestrator(BaseAgent):
    """L3 Master Multi-Language Orchestrator supervising all 13 L4 subsystem coordinators."""

    def __init__(
        self,
        name: str = "MultiLanguageOrchestrator",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 256,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
        default_language: str = "python",
    ) -> None:
        default_caps = capabilities or [
            "multi_language",
            "multi_language_orchestration",
            "python_generator",
            "node_generator",
            "go_generator",
            "rust_generator",
            "java_generator",
            "language_detector",
            "language_translator",
            "cross_language_validator",
            "package_manager",
            "framework_selector",
            "dependency_resolver",
            "code_formatter",
            "documentation_generator",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "M1_MULTI_LANGUAGE_ORCHESTRATOR",
        )
        self.default_language = default_language

        self.python_gen: Optional[PythonGenerator] = None
        self.node_gen: Optional[NodeGenerator] = None
        self.go_gen: Optional[GoGenerator] = None
        self.rust_gen: Optional[RustGenerator] = None
        self.java_gen: Optional[JavaGenerator] = None
        self.detector: Optional[LanguageDetector] = None
        self.translator: Optional[LanguageTranslator] = None
        self.validator: Optional[CrossLanguageValidator] = None
        self.package_mgr: Optional[PackageManager] = None
        self.framework_sel: Optional[FrameworkSelector] = None
        self.dependency_res: Optional[DependencyResolver] = None
        self.formatter: Optional[CodeFormatter] = None
        self.doc_gen: Optional[DocumentationGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_multilang_subsystems()

        self.register_tool("run_all_language_support", self.run_all_language_support)

    def _spawn_multilang_subsystems(self) -> None:
        """Spawn the 13 L4 multi-language coordinators (Rule 1 & Rule 5)."""
        logger.info("MultiLanguageOrchestrator %s spawning 13 coordinators...", self.agent_id)
        child_depth = self.depth + 2

        self.python_gen = self.spawn_subagent(PythonGenerator, name="PythonGenerator", max_depth=child_depth, resources_mb=64)
        self.node_gen = self.spawn_subagent(NodeGenerator, name="NodeGenerator", max_depth=child_depth, resources_mb=64)
        self.go_gen = self.spawn_subagent(GoGenerator, name="GoGenerator", max_depth=child_depth, resources_mb=64)
        self.rust_gen = self.spawn_subagent(RustGenerator, name="RustGenerator", max_depth=child_depth, resources_mb=64)
        self.java_gen = self.spawn_subagent(JavaGenerator, name="JavaGenerator", max_depth=child_depth, resources_mb=64)
        self.detector = self.spawn_subagent(LanguageDetector, name="LanguageDetector", max_depth=child_depth, resources_mb=64)
        self.translator = self.spawn_subagent(LanguageTranslator, name="LanguageTranslator", max_depth=child_depth, resources_mb=64)
        self.validator = self.spawn_subagent(CrossLanguageValidator, name="CrossLanguageValidator", max_depth=child_depth, resources_mb=64)
        self.package_mgr = self.spawn_subagent(PackageManager, name="PackageManager", max_depth=child_depth, resources_mb=64)
        self.framework_sel = self.spawn_subagent(FrameworkSelector, name="FrameworkSelector", max_depth=child_depth, resources_mb=64)
        self.dependency_res = self.spawn_subagent(DependencyResolver, name="DependencyResolver", max_depth=child_depth, resources_mb=64)
        self.formatter = self.spawn_subagent(CodeFormatter, name="CodeFormatter", max_depth=child_depth, resources_mb=64)
        self.doc_gen = self.spawn_subagent(DocumentationGenerator, name="DocumentationGenerator", max_depth=child_depth, resources_mb=64)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("MultiLanguageOrchestrator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        report = self.run_all_language_support(payload)
        return {"status": "COMPLETED", "multi_language_report": report}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        report = result.get("multi_language_report")
        if not report or "all_support_active" not in report:
            raise MultiLanguageError("MultiLanguageOrchestrator produced an incomplete support summary.")
        return result

    def cleanup(self) -> None:
        logger.debug("MultiLanguageOrchestrator %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def generate_project(self, language: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a complete project in the given language."""
        generator_map = {
            "python": self.python_gen,
            "node": self.node_gen,
            "go": self.go_gen,
            "rust": self.rust_gen,
            "java": self.java_gen,
        }
        generator = generator_map.get(language.lower())
        if generator is None:
            raise MultiLanguageError(f"Unsupported generation language: {language}")
        method = getattr(generator, f"generate_{language.lower()}_project")
        return method(context)

    def run_all_language_support(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trigger the full multi-language support cycle across all 13 subsystem coordinators."""
        ctx = context or {}
        logger.info("Executing comprehensive multi-language support cycle...")
        lang = ctx.get("language", self.default_language)
        spec = {"module_name": ctx.get("module_name", "myservice"), "model_name": ctx.get("model_name", "Item")}

        detection = self.detector.detect_language(ctx.get("sample_code", ""), ctx.get("sample_file")) if self.detector else {"accepted": True}
        sample_provided = bool(ctx.get("sample_code") or ctx.get("sample_file"))
        generation = self.generate_project(lang, spec) if lang in {"python", "node", "go", "rust", "java"} else {}
        translation = (
            self.translator.translate_language("python", lang, ctx.get("source_code", ""))
            if self.translator and ctx.get("source_code") and lang != "python"
            else {"success": True, "skipped": lang == "python"}
        )
        validation = self.validator.validate_code(generation.get("api", {}).get("generated_code", ""), lang) if self.validator else {"all_passed": True}
        packages = self.package_mgr.manage_packages(lang, ctx.get("packages", [])) if self.package_mgr else {"manager": lang}
        framework = self.framework_sel.select_framework(lang) if self.framework_sel else {"framework": "default"}
        deps = self.dependency_res.resolve_dependencies({pkg: "*" for pkg in ctx.get("packages", [])}) if self.dependency_res else {"success": True}
        formatted = self.formatter.format_code(lang, generation.get("api", {}).get("generated_code", "")) if self.formatter else {"formatter": lang}
        docs = self.doc_gen.generate_documentation(lang, spec["module_name"]) if self.doc_gen else {"tool": "default"}

        all_ok = (
            (detection.get("accepted", True) or not sample_provided)
            and generation.get("all_generated", True)
            and translation.get("success", True)
            and validation.get("all_passed", True)
            and packages.get("status") == "COMPLETED"
            and framework.get("optimal", True)
            and deps.get("success", True)
            and bool(formatted.get("formatted_code"))
            and bool(docs.get("doc_content"))
        )

        return {
            "all_support_active": all_ok,
            "language": lang,
            "total_subsystems": 13,
            "generation": generation,
            "detection": detection,
            "translation": translation,
            "validation": validation,
            "packages": packages,
            "framework": framework,
            "dependencies": deps,
            "formatting": formatted,
            "documentation": docs,
            "timestamp": time.time(),
        }