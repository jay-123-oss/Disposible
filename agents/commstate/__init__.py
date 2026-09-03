"""Communication & State Domain Agents for the Fractal Multi-Agent Coding System.

Exports all 15 specialized communication and state agents and atomic subagents across levels L3 to L5,
along with the registration helper `register_all_commstate_agents`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from agents.commstate.artifact_manager import (
    ArtifactCreator,
    ArtifactDeleter,
    ArtifactManager,
    ArtifactRetriever,
    ArtifactUpdater,
)
from agents.commstate.checkpoint_manager import (
    CheckpointCleaner,
    CheckpointCreator,
    CheckpointList,
    CheckpointManager,
    CheckpointRestorer,
)
from agents.commstate.commstate_orchestrator import CommStateOrchestrator
from agents.commstate.event_publisher import (
    AgentEventPublisher,
    ErrorEventPublisher,
    EventPublisher,
    StateEventPublisher,
    TaskEventPublisher,
)
from agents.commstate.event_subscriber import (
    AgentEventSubscriber,
    ErrorEventSubscriber,
    EventSubscriber,
    StateEventSubscriber,
    TaskEventSubscriber,
)
from agents.commstate.exceptions import (
    ArtifactError,
    CheckpointError,
    CommStateError,
    CompressionError,
    EventError,
    MailboxError,
    RegistryError,
    RoutingError,
    SessionError,
    SynchronizationError,
    TaskStoreError,
    TeamStoreError,
    TraceError,
)
from agents.commstate.mailbox_manager import (
    MailboxManager,
    MessageDeleter,
    MessageReader,
    MessageReceiver,
    MessageSender,
)
from agents.commstate.message_router import (
    BroadcastRouter,
    DirectRouter,
    MessageRouter,
    PriorityRouter,
    TopicRouter,
)
from agents.commstate.registry_manager import (
    AgentFinder,
    AgentRegistrar,
    AgentStatusChecker,
    AgentUnregistrar,
    RegistryManager,
)
from agents.commstate.session_manager import (
    SessionCleaner,
    SessionCreator,
    SessionLoader,
    SessionManager,
    SessionSaver,
)
from agents.commstate.state_compressor import (
    Decompressor,
    OfflineStorer,
    StateCompressor,
    SummaryGenerator,
    TokenCompressor,
)
from agents.commstate.state_synchronizer import (
    ConflictResolver,
    StatePullSync,
    StatePushSync,
    StateSynchronizer,
    StateVerifier,
)
from agents.commstate.task_store_manager import (
    TaskCreator,
    TaskDeleter,
    TaskFinder,
    TaskStoreManager,
    TaskUpdater,
)
from agents.commstate.team_store_manager import (
    TeamCreator,
    TeamDeleter,
    TeamFinder,
    TeamStoreManager,
    TeamUpdater,
)
from agents.commstate.trace_depositor import (
    AttractionTraceLeaver,
    DangerTraceLeaver,
    InfoTraceLeaver,
    TraceDecayer,
    TraceDepositor,
)
from agents.commstate.trace_reader import (
    AttractionTraceReader,
    DangerTraceReader,
    InfoTraceReader,
    TraceAnalyzer,
    TraceReader,
)
from core.registry import AgentRegistry


logger = logging.getLogger("FractalCore.CommState")

__all__ = [
    # Master Orchestrator
    "CommStateOrchestrator",
    # Task Store
    "TaskStoreManager",
    "TaskCreator",
    "TaskUpdater",
    "TaskFinder",
    "TaskDeleter",
    # Team Store
    "TeamStoreManager",
    "TeamCreator",
    "TeamUpdater",
    "TeamFinder",
    "TeamDeleter",
    # Mailbox
    "MailboxManager",
    "MessageSender",
    "MessageReceiver",
    "MessageReader",
    "MessageDeleter",
    # Registry
    "RegistryManager",
    "AgentRegistrar",
    "AgentUnregistrar",
    "AgentFinder",
    "AgentStatusChecker",
    # Trace Depositor
    "TraceDepositor",
    "AttractionTraceLeaver",
    "DangerTraceLeaver",
    "InfoTraceLeaver",
    "TraceDecayer",
    # Trace Reader
    "TraceReader",
    "AttractionTraceReader",
    "DangerTraceReader",
    "InfoTraceReader",
    "TraceAnalyzer",
    # Artifact Manager
    "ArtifactManager",
    "ArtifactCreator",
    "ArtifactRetriever",
    "ArtifactUpdater",
    "ArtifactDeleter",
    # Session Manager
    "SessionManager",
    "SessionCreator",
    "SessionLoader",
    "SessionSaver",
    "SessionCleaner",
    # Checkpoint Manager
    "CheckpointManager",
    "CheckpointCreator",
    "CheckpointRestorer",
    "CheckpointList",
    "CheckpointCleaner",
    # State Synchronizer
    "StateSynchronizer",
    "StatePushSync",
    "StatePullSync",
    "ConflictResolver",
    "StateVerifier",
    # Event Publisher
    "EventPublisher",
    "TaskEventPublisher",
    "AgentEventPublisher",
    "StateEventPublisher",
    "ErrorEventPublisher",
    # Event Subscriber
    "EventSubscriber",
    "TaskEventSubscriber",
    "AgentEventSubscriber",
    "StateEventSubscriber",
    "ErrorEventSubscriber",
    # Message Router
    "MessageRouter",
    "DirectRouter",
    "BroadcastRouter",
    "TopicRouter",
    "PriorityRouter",
    # State Compressor
    "StateCompressor",
    "TokenCompressor",
    "SummaryGenerator",
    "OfflineStorer",
    "Decompressor",
    # Exceptions
    "CommStateError",
    "TaskStoreError",
    "TeamStoreError",
    "MailboxError",
    "RegistryError",
    "TraceError",
    "ArtifactError",
    "SessionError",
    "CheckpointError",
    "SynchronizationError",
    "EventError",
    "RoutingError",
    "CompressionError",
    # Registration Helper
    "register_all_commstate_agents",
]


def register_all_commstate_agents(
    registry: AgentRegistry,
    parent_agent: Any = None,
    max_depth: int = 7,
) -> Dict[str, Any]:
    """Register all communication and state layer agents into the AgentRegistry.

    Args:
        registry: The central AgentRegistry singleton.
        parent_agent: Optional supervising orchestrator coordinator.
        max_depth: Global depth ceiling for commstate hierarchy.

    Returns:
        Dict mapping agent_id to instantiated agent instances.
    """
    logger.info("Registering all communication and state domain agents into AgentRegistry...")

    # Root CommState Orchestrator (L3)
    commstate_orchestrator = CommStateOrchestrator(
        parent=parent_agent,
        max_depth=max_depth,
        agent_id="C1_COMMSTATE_ORCHESTRATOR",
        auto_spawn_subagents=True,
    )
    registry.register_agent(commstate_orchestrator)

    # Register all spawned children recursively
    registered_count = 1
    def _register_children(agent: Any) -> None:
        nonlocal registered_count
        for child_id, child in agent.children.items():
            registry.register_agent(child)
            registered_count += 1
            _register_children(child)

    _register_children(commstate_orchestrator)

    logger.info("Successfully registered %d commstate domain agents into registry.", registered_count)
    return {
        "commstate_orchestrator": commstate_orchestrator,
        "total_registered": registered_count,
    }
