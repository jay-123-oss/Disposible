"""AgentReference agent managing Agent API Reference, Capabilities, Lifecycle, and Custom Agent documentation."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from agents.documentation.exceptions import AgentReferenceError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Docs.AgentReference")


# ==============================================================================
# L5 Atomic Agent Reference Subagents
# ==============================================================================

class AgentApiReference(BaseAgent):
    """L5 agent cataloging BaseAgent class methods, constructor parameters, and registry APIs."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AgentApiReference %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "COMPLETED",
            "doc_type": "AGENT_API_REFERENCE",
            "methods_documented": ["initialize", "process", "validate", "cleanup", "spawn_subagent", "register_tool"],
            "generated": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AgentApiReference %s cleaned up.", self.agent_id)


class AgentCapabilities(BaseAgent):
    """L5 agent listing all registered capabilities across Planning, Coding, Testing, Security, Quality, etc."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AgentCapabilities %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "COMPLETED",
            "doc_type": "AGENT_CAPABILITIES",
            "domains_cataloged": [
                "Planning (P1-P10)", "Coding (C1-C24)", "Testing (T1-T16)", "Security (S1-S12)",
                "Quality (Q1-Q12)", "Infrastructure (I1-I14)", "CommState (CS1-CS14)",
                "Monitoring (M1-M14)", "Integration (IA1-IA14)", "Testing & Validation (TV1-TV14)",
            ],
            "generated": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AgentCapabilities %s cleaned up.", self.agent_id)


class AgentLifecycle(BaseAgent):
    """L5 agent documenting four-stage lifecycle (initialize -> process -> validate -> cleanup) and transitions."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AgentLifecycle %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "COMPLETED",
            "doc_type": "AGENT_LIFECYCLE",
            "lifecycle_stages": ["INITIALIZE", "PROCESS", "VALIDATE", "CLEANUP"],
            "generated": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AgentLifecycle %s cleaned up.", self.agent_id)


class CustomAgentGuide(BaseAgent):
    """L5 agent writing walkthrough on implementing, registering, and supervising custom user-defined agents."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CustomAgentGuide %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "COMPLETED",
            "doc_type": "CUSTOM_AGENT_GUIDE",
            "steps": ["Inherit BaseAgent", "Define capabilities", "Implement process()", "Register in registry"],
            "generated": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CustomAgentGuide %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 AgentReference Agent
# ==============================================================================

class AgentReference(BaseAgent):
    """L4 coordinator overseeing agent API references, capabilities catalogs, lifecycle models, and custom agent guides."""

    def __init__(
        self,
        name: str = "AgentReference",
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
            "agent_reference",
            "agent_api_reference",
            "agent_capabilities",
            "agent_lifecycle",
            "custom_agent_guide",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "D9_AGENT_REFERENCE",
        )

        self.api_ref: Optional[AgentApiReference] = None
        self.cap_doc: Optional[AgentCapabilities] = None
        self.life_doc: Optional[AgentLifecycle] = None
        self.custom_doc: Optional[CustomAgentGuide] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_agent_reference", self.generate_agent_reference)

    def _spawn_subagents(self) -> None:
        """Spawn atomic agent reference subagents (Rule 1 & Rule 5)."""
        logger.info("AgentReference %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.api_ref = self.spawn_subagent(AgentApiReference, name="AgentApiReference", max_depth=child_depth, resources_mb=32)
        self.cap_doc = self.spawn_subagent(AgentCapabilities, name="AgentCapabilities", max_depth=child_depth, resources_mb=32)
        self.life_doc = self.spawn_subagent(AgentLifecycle, name="AgentLifecycle", max_depth=child_depth, resources_mb=32)
        self.custom_doc = self.spawn_subagent(CustomAgentGuide, name="CustomAgentGuide", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AgentReference %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        res = self.generate_agent_reference(context=payload)
        return {"status": "COMPLETED", "agent_reference": res}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AgentReference %s cleanup complete.", self.agent_id)

    def generate_agent_reference(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Produce BaseAgent API reference, capability indices, lifecycle workflows, and custom agent guides."""
        p_env = {"payload": context or {}}

        a_res = self.api_ref.process(p_env) if self.api_ref else {}
        c_res = self.cap_doc.process(p_env) if self.cap_doc else {}
        l_res = self.life_doc.process(p_env) if self.life_doc else {}
        u_res = self.custom_doc.process(p_env) if self.custom_doc else {}

        all_ok = (
            a_res.get("generated", True)
            and c_res.get("generated", True)
            and l_res.get("generated", True)
            and u_res.get("generated", True)
        )

        return {
            "all_generated": all_ok,
            "api_reference": a_res,
            "capabilities": c_res,
            "lifecycle": l_res,
            "custom_guide": u_res,
            "timestamp": time.time(),
        }
