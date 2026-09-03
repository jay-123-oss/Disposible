"""Planning domain agents package for the Fractal Multi-Agent Coding System.

Exports:
- IntentClarifier (P1)
- QuestionGenerator (P2)
- OptionParser (P3)
- AnswerValidator (P4)
- RequirementsDocumenter (P5)
- TechStackSelector (P6)
- ArchitectureDesigner (P7)
- TaskDecomposer (P8)
- RiskAssessor (P9)
- PlanGenerator (P10)
- KnowledgeBase
- PlanningError and sub-exceptions
- register_all_planning_agents() helper
"""

from typing import Any, Dict, List, Optional

from agents.planning.answer_validator import AnswerValidator
from agents.planning.architecture_designer import ArchitectureDesigner
from agents.planning.exceptions import (
    ArchitectureDesignError,
    IntentClarificationError,
    PlanGenerationError,
    PlanningError,
    QuestionGenerationError,
    RiskAssessmentError,
    TaskDecompositionError,
    TechStackSelectionError,
    ValidationError,
)
from agents.planning.intent_clarifier import IntentClarifier
from agents.planning.knowledge_base import KnowledgeBase
from agents.planning.option_parser import OptionParser
from agents.planning.plan_generator import PlanGenerator
from agents.planning.question_generator import QuestionGenerator
from agents.planning.requirements_documenter import RequirementsDocumenter
from agents.planning.risk_assessor import RiskAssessor
from agents.planning.task_decomposer import TaskDecomposer
from agents.planning.tech_stack_selector import TechStackSelector
from core.agent_base import BaseAgent
from core.registry import AgentRegistry


def register_all_planning_agents(
    registry: AgentRegistry,
    planning_parent: Optional[BaseAgent] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, BaseAgent]:
    """Helper to instantiate and register all 10 planning agents in the AgentRegistry.

    Hierarchy respects max_depth=2:
    - Root/L1: Planning Parent (if supplied) or root
    - L2: IntentClarifier, RequirementsDocumenter, TechStackSelector,
          ArchitectureDesigner, TaskDecomposer, RiskAssessor, PlanGenerator
    - L3: Sub-agents of IntentClarifier (QuestionGenerator, OptionParser, AnswerValidator)
    """
    cfg = config or {}
    llm_cfg = cfg.get("llm", {})
    endpoint = llm_cfg.get("endpoint", "http://localhost:11434")
    model = llm_cfg.get("model", "qwen2.5-coder:3b")

    registered: Dict[str, BaseAgent] = {}

    # 1. Instantiate IntentClarifier (which auto-spawns QG, OP, AV at Level 3)
    intent_clarifier = IntentClarifier(
        name="IntentClarifier",
        parent=planning_parent,
        model=model,
        llm_endpoint=endpoint,
        auto_spawn_subagents=True,
    )
    registry.register_agent(intent_clarifier)
    registered["intent_clarifier"] = intent_clarifier

    # Register its spawned sub-agents
    if intent_clarifier.question_generator:
        registry.register_agent(intent_clarifier.question_generator)
        registered["question_generator"] = intent_clarifier.question_generator

    if intent_clarifier.option_parser:
        registry.register_agent(intent_clarifier.option_parser)
        registered["option_parser"] = intent_clarifier.option_parser

    if intent_clarifier.answer_validator:
        registry.register_agent(intent_clarifier.answer_validator)
        registered["answer_validator"] = intent_clarifier.answer_validator

    # 2. Instantiate peer planning agents under planning_parent
    req_doc = RequirementsDocumenter(
        name="RequirementsDocumenter",
        parent=planning_parent,
        model=model,
        llm_endpoint=endpoint,
    )
    registry.register_agent(req_doc)
    registered["requirements_documenter"] = req_doc

    tech_selector = TechStackSelector(
        name="TechStackSelector",
        parent=planning_parent,
        model=model,
        llm_endpoint=endpoint,
    )
    registry.register_agent(tech_selector)
    registered["tech_stack_selector"] = tech_selector

    arch_designer = ArchitectureDesigner(
        name="ArchitectureDesigner",
        parent=planning_parent,
        model=model,
        llm_endpoint=endpoint,
    )
    registry.register_agent(arch_designer)
    registered["architecture_designer"] = arch_designer

    task_decomposer = TaskDecomposer(
        name="TaskDecomposer",
        parent=planning_parent,
        model=model,
        llm_endpoint=endpoint,
    )
    registry.register_agent(task_decomposer)
    registered["task_decomposer"] = task_decomposer

    risk_assessor = RiskAssessor(
        name="RiskAssessor",
        parent=planning_parent,
        model=model,
        llm_endpoint=endpoint,
    )
    registry.register_agent(risk_assessor)
    registered["risk_assessor"] = risk_assessor

    plan_generator = PlanGenerator(
        name="PlanGenerator",
        parent=planning_parent,
        model=model,
        llm_endpoint=endpoint,
    )
    registry.register_agent(plan_generator)
    registered["plan_generator"] = plan_generator

    return registered


__all__ = [
    "IntentClarifier",
    "QuestionGenerator",
    "OptionParser",
    "AnswerValidator",
    "RequirementsDocumenter",
    "TechStackSelector",
    "ArchitectureDesigner",
    "TaskDecomposer",
    "RiskAssessor",
    "PlanGenerator",
    "KnowledgeBase",
    "PlanningError",
    "IntentClarificationError",
    "QuestionGenerationError",
    "ValidationError",
    "TechStackSelectionError",
    "ArchitectureDesignError",
    "TaskDecompositionError",
    "RiskAssessmentError",
    "PlanGenerationError",
    "register_all_planning_agents",
]
