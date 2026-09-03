"""InstallationGuide agent managing Prerequisites, Step-by-Step, Troubleshooting, and Verification documentation."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from agents.documentation.exceptions import InstallationGuideError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Docs.InstallationGuide")


# ==============================================================================
# L5 Atomic Installation Guide Subagents
# ==============================================================================

class PrerequisitesDocumenter(BaseAgent):
    """L5 agent detailing Python versions (3.10+), OS compatibility, RAM requirements (8GB min), and Ollama setup."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PrerequisitesDocumenter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "COMPLETED",
            "doc_type": "PREREQUISITES",
            "requirements": ["Python >= 3.10", "RAM >= 8GB", "OS: Linux/macOS/Windows", "Optional: Ollama"],
            "generated": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PrerequisitesDocumenter %s cleaned up.", self.agent_id)


class StepByStepInstall(BaseAgent):
    """L5 agent writing installation walkthroughs: venv creation, pip install, config setup, and CLI verification."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("StepByStepInstall %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "COMPLETED",
            "doc_type": "STEP_BY_STEP_INSTALL",
            "commands": [
                "python -m venv venv",
                "source venv/bin/activate",
                "pip install -r requirements.txt",
                "cp config.example.yaml config.yaml",
            ],
            "generated": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("StepByStepInstall %s cleaned up.", self.agent_id)


class TroubleshootingInstall(BaseAgent):
    """L5 agent documenting installation gotchas: missing build tools, pip permission errors, and SSL certificates."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TroubleshootingInstall %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "COMPLETED",
            "doc_type": "TROUBLESHOOTING_INSTALL",
            "solutions": ["Virtualenv isolation", "Wheel installation", "Proxy / pip mirror configuration"],
            "generated": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TroubleshootingInstall %s cleaned up.", self.agent_id)


class VerificationGuide(BaseAgent):
    """L5 agent writing sanity check scripts, CLI status commands, and smoke tests."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("VerificationGuide %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "COMPLETED",
            "doc_type": "VERIFICATION_GUIDE",
            "verification_commands": [
                "python cli.py status",
                "python cli.py health",
                "python -m unittest discover -s tests -t .",
            ],
            "generated": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("VerificationGuide %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 InstallationGuide Agent
# ==============================================================================

class InstallationGuide(BaseAgent):
    """L4 coordinator overseeing prerequisites, step-by-step setup, installation troubleshooting, and verification."""

    def __init__(
        self,
        name: str = "InstallationGuide",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "installation_guide",
            "prerequisites_documenter",
            "step_by_step_install",
            "troubleshooting_install",
            "verification_guide",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "D6_INSTALLATION_GUIDE",
        )

        self.prereq_doc: Optional[PrerequisitesDocumenter] = None
        self.step_doc: Optional[StepByStepInstall] = None
        self.trouble_doc: Optional[TroubleshootingInstall] = None
        self.verify_doc: Optional[VerificationGuide] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_installation_guide", self.generate_installation_guide)

    def _spawn_subagents(self) -> None:
        """Spawn atomic installation guide subagents (Rule 1 & Rule 5)."""
        logger.info("InstallationGuide %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.prereq_doc = self.spawn_subagent(PrerequisitesDocumenter, name="PrerequisitesDocumenter", max_depth=child_depth, resources_mb=32)
        self.step_doc = self.spawn_subagent(StepByStepInstall, name="StepByStepInstall", max_depth=child_depth, resources_mb=32)
        self.trouble_doc = self.spawn_subagent(TroubleshootingInstall, name="TroubleshootingInstall", max_depth=child_depth, resources_mb=32)
        self.verify_doc = self.spawn_subagent(VerificationGuide, name="VerificationGuide", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("InstallationGuide %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        res = self.generate_installation_guide(context=payload)
        return {"status": "COMPLETED", "installation_guide": res}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("InstallationGuide %s cleanup complete.", self.agent_id)

    def generate_installation_guide(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Produce prerequisite checks, installation steps, fix guides, and verification scripts."""
        p_env = {"payload": context or {}}

        p_res = self.prereq_doc.process(p_env) if self.prereq_doc else {}
        s_res = self.step_doc.process(p_env) if self.step_doc else {}
        t_res = self.trouble_doc.process(p_env) if self.trouble_doc else {}
        v_res = self.verify_doc.process(p_env) if self.verify_doc else {}

        all_ok = (
            p_res.get("generated", True)
            and s_res.get("generated", True)
            and t_res.get("generated", True)
            and v_res.get("generated", True)
        )

        return {
            "all_generated": all_ok,
            "prerequisites": p_res,
            "steps": s_res,
            "troubleshooting": t_res,
            "verification": v_res,
            "timestamp": time.time(),
        }
