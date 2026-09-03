"""Core package initialization and public API exports for Fractal Multi-Agent System."""

from core.agent_base import BaseAgent
from core.communication import (
    MessageBus,
    MessageEnvelope,
    StigmergyTrace,
    TraceType,
)
from core.exceptions import (
    AgentError,
    CommunicationError,
    DepthLimitError,
    FractalSystemError,
    OrchestratorError,
    QualityGateError,
    ResourceLimitError,
    SandboxError,
    StateError,
)
from core.monitor import (
    Alert,
    AlertSeverity,
    SystemMonitor,
)
from core.orchestrator import Orchestrator
from core.quality_gate import (
    GatePhase,
    GateStatus,
    QualityEvaluationResult,
    QualityGate,
)
from core.registry import AgentRegistry
from core.sandbox import ExecutionResult, SandboxManager
from core.state_manager import StateManager
from core.task_queue import (
    TaskItem,
    TaskPriority,
    TaskQueue,
    TaskStatus,
)
from core.master_intent_router import (
    MasterIntentRouter,
    RouterOutput,
    master_router_graph,
)
from core.intent_engine import (
    IntentEngine,
    IntentResult,
    IntentType,
    ExecutionMode,
    ExecutionPolicyGate,
    PolicyDecision,
)
from core.canonical_orchestrator import (
    CanonicalOrchestrator,
    Task,
    TaskGraph,
    TaskStatus,
    TaskPriority as CanonicalTaskPriority,
    AgentCapability,
    AgentRegistrySystem,
)

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "BaseAgent",
    "Orchestrator",
    "AgentRegistry",
    "TaskQueue",
    "TaskItem",
    "TaskPriority",
    "TaskStatus",
    "StateManager",
    "MessageBus",
    "TraceType",
    "StigmergyTrace",
    "MessageEnvelope",
    "QualityGate",
    "GatePhase",
    "GateStatus",
    "QualityEvaluationResult",
    "SystemMonitor",
    "Alert",
    "AlertSeverity",
    "SandboxManager",
    "ExecutionResult",
    "FractalSystemError",
    "AgentError",
    "OrchestratorError",
    "CommunicationError",
    "SandboxError",
    "QualityGateError",
    "StateError",
    "DepthLimitError",
    "ResourceLimitError",
]
