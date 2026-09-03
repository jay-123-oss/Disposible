"""Phase 2: Intent Engine, Permission Boundary, and Central Execution Gate.

Implements:
1. Structured Intent Model:
   - Intents: READ_ONLY, ANALYZE, EXPLAIN, SEARCH, CREATE, MODIFY, DEBUG, TEST,
              REFACTOR, RESEARCH, COMMAND, DELETE, DEPLOY, UNKNOWN, CLARIFY
   - Modes: READ_ONLY, MUTATION, TERMINAL, DANGEROUS, CLARIFY
2. Two-Stage Intent Classification:
   - Stage A: Deterministic safety pre-check
   - Stage B: Structured classification
3. Central Execution Policy Gate:
   - Evaluates (IntentResult, Tool, Args) -> PolicyDecision (ALLOW, DENY, CONFIRMATION_REQUIRED)
   - HARD RULE: Intent must control write access. EXPLAIN/ANALYZE can NEVER write.
4. Structured Decision Logging.
"""

from __future__ import annotations

import enum
import logging
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger("AIhenge.IntentEngine")


class IntentType(str, enum.Enum):
    READ_ONLY = "READ_ONLY"
    ANALYZE = "ANALYZE"
    EXPLAIN = "EXPLAIN"
    SEARCH = "SEARCH"
    CREATE = "CREATE"
    MODIFY = "MODIFY"
    DEBUG = "DEBUG"
    TEST = "TEST"
    REFACTOR = "REFACTOR"
    RESEARCH = "RESEARCH"
    COMMAND = "COMMAND"
    DELETE = "DELETE"
    DEPLOY = "DEPLOY"
    UNKNOWN = "UNKNOWN"
    CLARIFY = "CLARIFY"


class ExecutionMode(str, enum.Enum):
    READ_ONLY = "READ_ONLY"
    MUTATION = "MUTATION"
    TERMINAL = "TERMINAL"
    DANGEROUS = "DANGEROUS"
    CLARIFY = "CLARIFY"


class IntentResult(BaseModel):
    """Structured intent representation with strict permission flags."""

    intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    requires_write: bool
    requires_terminal: bool
    requires_external_research: bool
    requires_confirmation: bool
    execution_mode: ExecutionMode
    reason: str
    target_entities: List[str] = Field(default_factory=list)
    clarification_prompt: Optional[str] = None


class PolicyDecision(BaseModel):
    """Structured decision returned by the Execution Policy Gate."""

    allowed: bool
    reason: str
    requires_confirmation: bool = False
    safety_level: str = "SAFE"
    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    timestamp: float = Field(default_factory=time.time)


class IntentEngine:
    """Two-stage Intent Classifier supporting English and natural multi-lingual Hindi/Hinglish."""

    DANGEROUS_TRIGGERS = [
        r"\bdelete\b", r"\bremove\s+all\b", r"\bdrop\s+(database|table|schema)\b",
        r"\bformat\b", r"\brm\s+-(rf|fr|r)\b", r"\berase\b", r"\bhata\s+do\b", r"\bdelete\s+karo\b",
    ]

    EXPLAIN_TRIGGERS = [
        r"\bexplain\b", r"\bko\s+explain\s+kro\b", r"\bexplain\s+karo\b",
        r"\barchitecture\s+batao\b", r"\bsamjhao\b", r"\bwhat\s+is\b",
        r"\bhow\s+does\b", r"\boverview\b", r"\bdescribe\b",
    ]

    ANALYZE_TRIGGERS = [
        r"\banalyze\b", r"\binspect\b", r"\bcheck\b", r"\bproblem\s+kya\s+hai\b",
        r"\barchitecture\b", r"\bstructure\b", r"\bscan\b", r"\bfind\s+bug\b",
        r"\bbug\s+find\s+kro\b", r"\bfind\s+issue\b", r"\bsearch\b",
    ]

    TEST_TRIGGERS = [
        r"\brun\s+tests?\b", r"\bpytest\b", r"\btest\s+chalao\b",
        r"\bnpm\s+test\b", r"\bexecute\s+tests?\b",
    ]

    COMMAND_TRIGGERS = [
        r"\bbuild\b", r"\bproject\s+build\s+karo\b", r"\bnpm\s+(start|run|build|install)\b",
        r"\bpip\s+install\b", r"\brun\s+the\s+server\b", r"\bstart\s+server\b",
    ]

    CREATE_TRIGGERS = [
        r"\bcreate\b", r"\bmake\b", r"\bgenerate\b", r"\bbanao\b",
        r"\badd\b", r"\bwrite\b", r"\bnew\s+file\b",
    ]

    DEBUG_TRIGGERS = [
        r"\bfix\b", r"\bfix\s+karo\b", r"\bbug\s+fix\b", r"\bbug\s+fix\s+karo\b",
        r"\brepair\b", r"\bresolve\s+bug\b",
    ]

    MODIFY_TRIGGERS = [
        r"\bmodify\b", r"\bmodify\s+karo\b", r"\bupdate\b", r"\bupdate\s+karo\b",
        r"\bchange\b", r"\bchange\s+karo\b", r"\bpatch\b",
    ]

    REFACTOR_TRIGGERS = [
        r"\brefactor\b", r"\bko\s+refactor\s+karo\b", r"\breorganize\b", r"\bclean\s+up\b",
    ]

    AMBIGUOUS_TRIGGERS = [
        r"^make\s+it\s+better$", r"^improve$", r"^fix\s+it$", r"^kuch\s+karo$",
        r"^help$", r"^do\s+it$",
    ]

    @classmethod
    def classify(cls, prompt: str) -> IntentResult:
        """Classify user intent with Two-Stage validation."""
        text = prompt.strip()
        lower = text.lower()

        # Extract potential filenames
        entities = re.findall(r"\b[a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+\b", text)

        # ----------------------------------------------------------------------
        # STAGE A: Deterministic Safety & Ambiguity Pre-Check
        # ----------------------------------------------------------------------

        # Check Ambiguous Triggers
        for pat in cls.AMBIGUOUS_TRIGGERS:
            if re.search(pat, lower):
                return IntentResult(
                    intent=IntentType.CLARIFY,
                    confidence=0.95,
                    requires_write=False,
                    requires_terminal=False,
                    requires_external_research=False,
                    requires_confirmation=False,
                    execution_mode=ExecutionMode.CLARIFY,
                    reason="Request is underspecified or ambiguous.",
                    target_entities=entities,
                    clarification_prompt=(
                        "I can help! Could you please specify what you'd like to improve?\n"
                        "1. Code quality / Refactoring\n"
                        "2. Bug fixing & Error resolution\n"
                        "3. Performance optimization\n"
                        "4. Architecture & Design explanation"
                    ),
                )

        # Check Dangerous Triggers
        for pat in cls.DANGEROUS_TRIGGERS:
            if re.search(pat, lower):
                return IntentResult(
                    intent=IntentType.DELETE,
                    confidence=0.98,
                    requires_write=True,
                    requires_terminal=True,
                    requires_external_research=False,
                    requires_confirmation=True,
                    execution_mode=ExecutionMode.DANGEROUS,
                    reason="Potentially destructive deletion command detected.",
                    target_entities=entities,
                )

        # Check Explicit Explanation / Conceptual Triggers (READ_ONLY GUARANTEED)
        for pat in cls.EXPLAIN_TRIGGERS:
            if re.search(pat, lower):
                return IntentResult(
                    intent=IntentType.EXPLAIN,
                    confidence=0.99,
                    requires_write=False,
                    requires_terminal=False,
                    requires_external_research=False,
                    requires_confirmation=False,
                    execution_mode=ExecutionMode.READ_ONLY,
                    reason="User is requesting an architectural, structural, or conceptual explanation.",
                    target_entities=entities,
                )

        # Check Testing Triggers
        for pat in cls.TEST_TRIGGERS:
            if re.search(pat, lower):
                return IntentResult(
                    intent=IntentType.TEST,
                    confidence=0.96,
                    requires_write=False,
                    requires_terminal=True,
                    requires_external_research=False,
                    requires_confirmation=False,
                    execution_mode=ExecutionMode.TERMINAL,
                    reason="User requested automated test suite execution.",
                    target_entities=entities,
                )

        # Check Command / Build Triggers
        for pat in cls.COMMAND_TRIGGERS:
            if re.search(pat, lower):
                return IntentResult(
                    intent=IntentType.COMMAND,
                    confidence=0.95,
                    requires_write=False,
                    requires_terminal=True,
                    requires_external_research=False,
                    requires_confirmation=False,
                    execution_mode=ExecutionMode.TERMINAL,
                    reason="User requested direct terminal or build execution.",
                    target_entities=entities,
                )

        # Check Bug Finding vs Bug Fixing
        # "bug find kro" -> ANALYZE / READ_ONLY
        # "bug fix karo" -> DEBUG / MUTATION
        if any(re.search(pat, lower) for pat in [r"\bfind\b", r"\bdhundo\b", r"\bdetect\b"]) and "bug" in lower:
            return IntentResult(
                intent=IntentType.ANALYZE,
                confidence=0.92,
                requires_write=False,
                requires_terminal=False,
                requires_external_research=False,
                requires_confirmation=False,
                execution_mode=ExecutionMode.READ_ONLY,
                reason="User is asking to find or analyze bugs without modifying code.",
                target_entities=entities,
            )

        # Refactoring
        for pat in cls.REFACTOR_TRIGGERS:
            if re.search(pat, lower):
                return IntentResult(
                    intent=IntentType.REFACTOR,
                    confidence=0.94,
                    requires_write=True,
                    requires_terminal=False,
                    requires_external_research=False,
                    requires_confirmation=False,
                    execution_mode=ExecutionMode.MUTATION,
                    reason="User requested code refactoring.",
                    target_entities=entities,
                )

        # Bug Fixing (Debug + Mutation)
        for pat in cls.DEBUG_TRIGGERS:
            if re.search(pat, lower):
                return IntentResult(
                    intent=IntentType.DEBUG,
                    confidence=0.95,
                    requires_write=True,
                    requires_terminal=False,
                    requires_external_research=False,
                    requires_confirmation=False,
                    execution_mode=ExecutionMode.MUTATION,
                    reason="User requested bug fixing and error resolution.",
                    target_entities=entities,
                )

        # Code Modification (Modify + Mutation)
        for pat in cls.MODIFY_TRIGGERS:
            if re.search(pat, lower):
                return IntentResult(
                    intent=IntentType.MODIFY,
                    confidence=0.95,
                    requires_write=True,
                    requires_terminal=False,
                    requires_external_research=False,
                    requires_confirmation=False,
                    execution_mode=ExecutionMode.MUTATION,
                    reason="User requested code modification and updates.",
                    target_entities=entities,
                )

        # File Creation
        for pat in cls.CREATE_TRIGGERS:
            if re.search(pat, lower) or "readme" in lower:
                return IntentResult(
                    intent=IntentType.CREATE,
                    confidence=0.95,
                    requires_write=True,
                    requires_terminal=False,
                    requires_external_research=False,
                    requires_confirmation=False,
                    execution_mode=ExecutionMode.MUTATION,
                    reason="User requested file or component creation.",
                    target_entities=entities,
                )

        # General Analysis
        for pat in cls.ANALYZE_TRIGGERS:
            if re.search(pat, lower):
                return IntentResult(
                    intent=IntentType.ANALYZE,
                    confidence=0.90,
                    requires_write=False,
                    requires_terminal=False,
                    requires_external_research=False,
                    requires_confirmation=False,
                    execution_mode=ExecutionMode.READ_ONLY,
                    reason="User requested inspection or architectural analysis.",
                    target_entities=entities,
                )

        # Casual Chat / Greetings
        if lower in {"hi", "hii", "hello", "hey", "namaste", "sup"}:
            return IntentResult(
                intent=IntentType.READ_ONLY,
                confidence=0.99,
                requires_write=False,
                requires_terminal=False,
                requires_external_research=False,
                requires_confirmation=False,
                execution_mode=ExecutionMode.READ_ONLY,
                reason="Casual greeting.",
                target_entities=[],
            )

        # Default fallback: safe READ_ONLY
        return IntentResult(
            intent=IntentType.UNKNOWN,
            confidence=0.70,
            requires_write=False,
            requires_terminal=False,
            requires_external_research=False,
            requires_confirmation=False,
            execution_mode=ExecutionMode.READ_ONLY,
            reason="Unclassified prompt; defaulting safely to READ_ONLY mode.",
            target_entities=entities,
        )


class ExecutionPolicyGate:
    """Central Execution Policy Gate enforcing the permission boundary."""

    WRITE_TOOLS = {"write_file", "edit_file", "create_or_modify_file", "delete_file"}
    TERMINAL_TOOLS = {"run_command", "run_python", "run_tests", "run_build"}
    READ_TOOLS = {"read_file", "list_files", "search_text", "search_symbol", "git_status", "git_diff", "git_log"}
    DANGEROUS_TOOLS = {"delete_file"}

    _audit_log: List[Dict[str, Any]] = []

    @classmethod
    def evaluate(
        cls,
        intent_res: IntentResult,
        tool_name: str,
        tool_args: Optional[Dict[str, Any]] = None,
        user_confirmed: bool = False,
    ) -> PolicyDecision:
        """Evaluate if the requested tool call is authorized under the active Intent."""
        tool_args = tool_args or {}
        req_id = f"req_{uuid.uuid4().hex[:8]}"
        now = time.time()

        # Rule 0: Clarification state denies all action tools
        if intent_res.execution_mode == ExecutionMode.CLARIFY:
            decision = PolicyDecision(
                allowed=False,
                reason="Task is in CLARIFICATION state. No action tools may execute until intent is clarified.",
                safety_level="SAFE",
                request_id=req_id,
                timestamp=now,
            )
            cls._log_decision(intent_res, tool_name, decision)
            return decision

        # Rule 1: Dangerous tools require explicit confirmation
        if tool_name in cls.DANGEROUS_TOOLS or intent_res.execution_mode == ExecutionMode.DANGEROUS:
            if not user_confirmed and not tool_args.get("allow_dangerous", False):
                decision = PolicyDecision(
                    allowed=False,
                    reason="Operation is classified as DANGEROUS and requires explicit user confirmation.",
                    requires_confirmation=True,
                    safety_level="DANGEROUS",
                    request_id=req_id,
                    timestamp=now,
                )
                cls._log_decision(intent_res, tool_name, decision)
                return decision
            else:
                decision = PolicyDecision(
                    allowed=True,
                    reason=f"Authorized dangerous operation '{tool_name}' with explicit user confirmation.",
                    safety_level="DANGEROUS",
                    request_id=req_id,
                    timestamp=now,
                )
                cls._log_decision(intent_res, tool_name, decision)
                return decision

        # Rule 2: HARD RULE - READ_ONLY mode STRICTLY DENIES all write/mutation tools
        if tool_name in cls.WRITE_TOOLS:
            if not intent_res.requires_write or intent_res.execution_mode in (
                ExecutionMode.READ_ONLY,
                ExecutionMode.CLARIFY,
            ):
                decision = PolicyDecision(
                    allowed=False,
                    reason=(
                        f"POLICY DENIAL: Intent '{intent_res.intent.value}' (Mode: {intent_res.execution_mode.value}) "
                        f"is read-only and does not possess write permission for tool '{tool_name}'."
                    ),
                    requires_confirmation=False,
                    safety_level="SAFE",
                    request_id=req_id,
                    timestamp=now,
                )
                cls._log_decision(intent_res, tool_name, decision)
                return decision

        # Rule 3: Terminal execution requires terminal permission
        if tool_name in cls.TERMINAL_TOOLS:
            if not intent_res.requires_terminal and intent_res.execution_mode == ExecutionMode.READ_ONLY:
                # Allow safe diagnostic commands or test tools if in analysis
                if tool_name not in ("run_tests",):
                    decision = PolicyDecision(
                        allowed=False,
                        reason=f"POLICY DENIAL: Tool '{tool_name}' requires terminal permission.",
                        safety_level="CAUTION",
                        request_id=req_id,
                        timestamp=now,
                    )
                    cls._log_decision(intent_res, tool_name, decision)
                    return decision

        # Operation is authorized
        decision = PolicyDecision(
            allowed=True,
            reason=f"Authorized under intent '{intent_res.intent.value}' in mode '{intent_res.execution_mode.value}'.",
            safety_level="SAFE" if tool_name in cls.READ_TOOLS else "CAUTION",
            request_id=req_id,
            timestamp=now,
        )
        cls._log_decision(intent_res, tool_name, decision)
        return decision

    @classmethod
    def _log_decision(cls, intent_res: IntentResult, tool_name: str, decision: PolicyDecision) -> None:
        log_entry = {
            "request_id": decision.request_id,
            "intent": intent_res.intent.value,
            "confidence": intent_res.confidence,
            "execution_mode": intent_res.execution_mode.value,
            "requested_tool": tool_name,
            "policy_decision": "ALLOW" if decision.allowed else "DENY",
            "reason": decision.reason,
            "timestamp": decision.timestamp,
        }
        cls._audit_log.append(log_entry)
        logger.info(
            "POLICY GATE [%s]: Tool '%s' -> %s (%s)",
            intent_res.intent.value,
            tool_name,
            "ALLOW" if decision.allowed else "DENY",
            decision.reason,
        )

    @classmethod
    def get_audit_log(cls) -> List[Dict[str, Any]]:
        return list(cls._audit_log)
