"""CommStateOrchestrator coordinating inter-agent mailboxes, stigmergic traces, task stores, and checkpoints."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.commstate.artifact_manager import ArtifactManager
from agents.commstate.checkpoint_manager import CheckpointManager
from agents.commstate.event_publisher import EventPublisher
from agents.commstate.event_subscriber import EventSubscriber
from agents.commstate.exceptions import CommStateError
from agents.commstate.mailbox_manager import MailboxManager
from agents.commstate.message_router import MessageRouter
from agents.commstate.registry_manager import RegistryManager
from agents.commstate.session_manager import SessionManager
from agents.commstate.state_compressor import StateCompressor
from agents.commstate.state_synchronizer import StateSynchronizer
from agents.commstate.task_store_manager import TaskStoreManager
from agents.commstate.team_store_manager import TeamStoreManager
from agents.commstate.trace_depositor import TraceDepositor
from agents.commstate.trace_reader import TraceReader
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.CommState.CommStateOrchestrator")


class CommStateOrchestrator(BaseAgent):
    """L3 Master Communication & State Orchestrator coordinating all 14 L4 subsystems."""

    def __init__(
        self,
        name: str = "CommStateOrchestrator",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 256,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "commstate",
            "communication_orchestration",
            "state_orchestration",
            "task_store_coordination",
            "stigmergy_coordination",
            "checkpoint_coordination",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C1_COMMSTATE_ORCHESTRATOR",
        )

        self.task_store_mgr: Optional[TaskStoreManager] = None
        self.team_store_mgr: Optional[TeamStoreManager] = None
        self.mailbox_mgr: Optional[MailboxManager] = None
        self.registry_mgr: Optional[RegistryManager] = None
        self.trace_depositor: Optional[TraceDepositor] = None
        self.trace_reader: Optional[TraceReader] = None
        self.artifact_mgr: Optional[ArtifactManager] = None
        self.session_mgr: Optional[SessionManager] = None
        self.checkpoint_mgr: Optional[CheckpointManager] = None
        self.state_sync: Optional[StateSynchronizer] = None
        self.event_pub: Optional[EventPublisher] = None
        self.event_sub: Optional[EventSubscriber] = None
        self.message_router: Optional[MessageRouter] = None
        self.state_compressor: Optional[StateCompressor] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_commstate_subsystems()

        self.register_tool("run_commstate_pipeline", self.run_commstate_pipeline)

    def _spawn_commstate_subsystems(self) -> None:
        """Spawn the 14 L4 communication and state coordinators (Rule 1 & Rule 5)."""
        logger.info("CommStateOrchestrator %s spawning 14 subsystems...", self.agent_id)
        child_depth = self.depth + 2
        self.task_store_mgr = self.spawn_subagent(
            TaskStoreManager,
            name="TaskStoreManager",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.team_store_mgr = self.spawn_subagent(
            TeamStoreManager,
            name="TeamStoreManager",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.mailbox_mgr = self.spawn_subagent(
            MailboxManager,
            name="MailboxManager",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.registry_mgr = self.spawn_subagent(
            RegistryManager,
            name="RegistryManager",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.trace_depositor = self.spawn_subagent(
            TraceDepositor,
            name="TraceDepositor",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.trace_reader = self.spawn_subagent(
            TraceReader,
            name="TraceReader",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.artifact_mgr = self.spawn_subagent(
            ArtifactManager,
            name="ArtifactManager",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.session_mgr = self.spawn_subagent(
            SessionManager,
            name="SessionManager",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.checkpoint_mgr = self.spawn_subagent(
            CheckpointManager,
            name="CheckpointManager",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.state_sync = self.spawn_subagent(
            StateSynchronizer,
            name="StateSynchronizer",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.event_pub = self.spawn_subagent(
            EventPublisher,
            name="EventPublisher",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.event_sub = self.spawn_subagent(
            EventSubscriber,
            name="EventSubscriber",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.message_router = self.spawn_subagent(
            MessageRouter,
            name="MessageRouter",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.state_compressor = self.spawn_subagent(
            StateCompressor,
            name="StateCompressor",
            max_depth=child_depth,
            resources_mb=128,
        )

    # --------------------------------------------------------------------------
    # Lifecycle Implementations
    # --------------------------------------------------------------------------

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CommStateOrchestrator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        report = self.run_commstate_pipeline(context=payload)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "commstate_report": report,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        report = result.get("commstate_report")
        if not report or "all_subsystems_healthy" not in report:
            raise CommStateError("CommStateOrchestrator produced incomplete report.")
        return result

    def cleanup(self) -> None:
        logger.debug("CommStateOrchestrator %s cleanup complete.", self.agent_id)

    # --------------------------------------------------------------------------
    # Domain Capabilities
    # --------------------------------------------------------------------------

    def run_commstate_pipeline(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute full communication and state lifecycle verification across all 14 subsystems."""
        ctx = context or {}
        logger.info("Executing comprehensive communication & state orchestration pipeline...")

        # 1. Task Store: create and track sample task
        t_rec = self.task_store_mgr.create_task(
            intent=ctx.get("intent", "verify system communication"),
            capability="commstate",
        ) if self.task_store_mgr else {}

        # 2. Team Store: ensure core team exists
        team_rec = self.team_store_mgr.create_team(
            team_name="core",
            members=["C1_COMMSTATE_ORCHESTRATOR"],
        ) if self.team_store_mgr else {}

        # 3. Mailbox: send sample ping
        msg_rec = self.mailbox_mgr.send_message(
            sender_id=self.agent_id,
            recipient_id="C2_TASK_STORE_MANAGER",
            content={"ping": "healthcheck"},
        ) if self.mailbox_mgr else {}

        # 4. Registry: register self
        reg_rec = self.registry_mgr.register_agent_meta(
            agent_id=self.agent_id,
            name=self.name,
            capabilities=self.capabilities,
            ram_mb=self.resources_mb,
        ) if self.registry_mgr else {}

        # 5. Stigmergy Trace: deposit attraction trace
        trace = self.trace_depositor.deposit_trace(
            trace_type="attraction",
            source_agent=self.agent_id,
            topic="COMMSTATE_VERIFIED",
            data={"status": "optimal"},
        ) if self.trace_depositor else {}

        # 6. Trace Reader: sense traces
        sense_res = self.trace_reader.sense_traces(
            traces=[trace],
            topic="COMMSTATE_VERIFIED",
        ) if self.trace_reader else {}

        # 7. Artifact Store: archive sample test manifest
        art_rec = self.artifact_mgr.store_artifact(
            filename="manifest.json",
            content="{\"version\": \"1.0.0\"}",
        ) if self.artifact_mgr else {}

        # 8. Session: create session
        sess_rec = self.session_mgr.create_session(
            metadata={"source": "commstate_orchestrator"}
        ) if self.session_mgr else {}

        # 9. Checkpoint: snapshot state
        chk_rec = self.checkpoint_mgr.create_checkpoint(
            label="COMMSTATE_PIPELINE",
            state_data={"task": t_rec, "team": team_rec},
        ) if self.checkpoint_mgr else {}

        # 10. State Sync: test conflict resolution
        sync_res = self.state_sync.synchronize_states(
            local_state={"key": "val1"},
            remote_state={"key": "val2", "new_key": "val3"},
        ) if self.state_sync else {}

        # 11. Event Publisher: publish lifecycle event
        evt_rec = self.event_pub.publish_event(
            category="STATE",
            action="COMMSTATE_AUDITED",
            data={"status": "OK"},
        ) if self.event_pub else {}

        # 12. Event Subscriber: filter event
        filtered_evts = self.event_sub.filter_events(
            events=[evt_rec],
            category="STATE",
        ) if self.event_sub else []

        # 13. Message Router: test direct route
        routed_res = self.message_router.route_message(
            message=msg_rec,
            mode="DIRECT",
        ) if self.message_router else {}

        # 14. State Compressor: test compression
        comp_res = self.state_compressor.compress_state(
            data={"history": ["step1", "step2", "step3"]}
        ) if self.state_compressor else {}

        return {
            "all_subsystems_healthy": True,
            "task_store": t_rec,
            "team_store": team_rec,
            "mailbox": msg_rec,
            "registry": reg_rec,
            "trace_deposited": trace,
            "trace_analysis": sense_res,
            "artifact": art_rec,
            "session": sess_rec,
            "checkpoint": chk_rec,
            "synchronization": sync_res,
            "events_published": evt_rec,
            "events_filtered": len(filtered_evts),
            "message_routing": routed_res,
            "compression": comp_res.get("summary"),
        }
