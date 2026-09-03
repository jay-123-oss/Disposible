"""Comprehensive Unit Test Suite for Communication & State Layer Agents (Session 9)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.commstate import (
    ArtifactCreator,
    ArtifactManager,
    CheckpointCreator,
    CheckpointManager,
    CommStateOrchestrator,
    EventPublisher,
    EventSubscriber,
    MailboxManager,
    MessageRouter,
    MessageSender,
    RegistryManager,
    SessionManager,
    StateCompressor,
    StateSynchronizer,
    TaskCreator,
    TaskStoreManager,
    TeamCreator,
    TeamStoreManager,
    TraceDepositor,
    TraceReader,
    register_all_commstate_agents,
)
from core.registry import AgentRegistry


class TestCommStateAgents(unittest.TestCase):
    """Test suite covering all 15 CommState domain agents and fractal subagent structures."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_commstate_orchestrator_spawns_subsystems(self) -> None:
        """Verify CommStateOrchestrator spawns all 14 L4 coordinators."""
        orch = CommStateOrchestrator(agent_id="TEST_COMMSTATE_ORCH", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(orch.task_store_mgr)
        self.assertIsNotNone(orch.team_store_mgr)
        self.assertIsNotNone(orch.mailbox_mgr)
        self.assertIsNotNone(orch.registry_mgr)
        self.assertIsNotNone(orch.trace_depositor)
        self.assertIsNotNone(orch.trace_reader)
        self.assertIsNotNone(orch.artifact_mgr)
        self.assertIsNotNone(orch.session_mgr)
        self.assertIsNotNone(orch.checkpoint_mgr)
        self.assertIsNotNone(orch.state_sync)
        self.assertIsNotNone(orch.event_pub)
        self.assertIsNotNone(orch.event_sub)
        self.assertIsNotNone(orch.message_router)
        self.assertIsNotNone(orch.state_compressor)

        child_names = [c.name for c in orch.children.values()]
        self.assertIn("TaskStoreManager", child_names)
        self.assertIn("TeamStoreManager", child_names)
        self.assertIn("MailboxManager", child_names)
        self.assertIn("RegistryManager", child_names)
        self.assertIn("TraceDepositor", child_names)
        self.assertIn("TraceReader", child_names)
        self.assertIn("ArtifactManager", child_names)
        self.assertIn("SessionManager", child_names)
        self.assertIn("CheckpointManager", child_names)
        self.assertIn("StateSynchronizer", child_names)
        self.assertIn("EventPublisher", child_names)
        self.assertIn("EventSubscriber", child_names)
        self.assertIn("MessageRouter", child_names)
        self.assertIn("StateCompressor", child_names)

    def test_task_store_manager_crud(self) -> None:
        """Verify TaskStoreManager creates, finds, updates, and deletes tasks."""
        tsm = TaskStoreManager(agent_id="TEST_TSM", auto_spawn_subagents=True, max_depth=7)
        self.assertIsInstance(tsm.creator, TaskCreator)

        t = tsm.create_task(intent="Test Task Store", capability="testing", priority="HIGH")
        task_id = t["task_id"]
        self.assertIn(task_id, tsm._store)

        matched = tsm.find_tasks(capability="testing")
        self.assertEqual(len(matched), 1)

        updated = tsm.update_task(task_id=task_id, status="COMPLETED", result_data={"out": "done"})
        self.assertEqual(updated["status"], "COMPLETED")

        deleted = tsm.delete_task(task_id)
        self.assertTrue(deleted)
        self.assertNotIn(task_id, tsm._store)

    def test_team_store_manager_grouping(self) -> None:
        """Verify TeamStoreManager creates teams and updates rosters."""
        ts = TeamStoreManager(agent_id="TEST_TEAM", auto_spawn_subagents=True, max_depth=7)
        self.assertIsInstance(ts.creator, TeamCreator)

        tm = ts.create_team(team_name="infra", members=["A1", "A2"])
        self.assertIn("infra", ts._teams)

        ts.add_to_team("infra", ["A3"])
        found = ts.find_teams(team_name="infra")
        self.assertEqual(len(found[0]["members"]), 3)

    def test_mailbox_manager_delivery(self) -> None:
        """Verify MailboxManager sends and reads messages."""
        mb = MailboxManager(agent_id="TEST_MB", auto_spawn_subagents=True, max_depth=7)
        self.assertIsInstance(mb.sender, MessageSender)

        msg = mb.send_message(sender_id="AGENT_A", recipient_id="AGENT_B", content={"cmd": "run"})
        inbox = mb.read_messages(recipient_id="AGENT_B", unread_only=True)
        self.assertEqual(len(inbox), 1)
        self.assertEqual(inbox[0]["content"]["cmd"], "run")

        deleted = mb.delete_message("AGENT_B", msg["message_id"])
        self.assertTrue(deleted)

    def test_registry_manager_indexing(self) -> None:
        """Verify RegistryManager registers capabilities and finds agents."""
        rm = RegistryManager(agent_id="TEST_RM", auto_spawn_subagents=True, max_depth=7)
        rm.register_agent_meta(agent_id="A_SEC", name="SecurityAgent", capabilities=["security_audit", "vulnerability_scan"])

        found = rm.find_agents_by_capability("security_audit")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["agent_id"], "A_SEC")

    def test_trace_depositor_and_reader(self) -> None:
        """Verify TraceDepositor emits traces and TraceReader analyzes safety."""
        td = TraceDepositor(agent_id="TEST_TD", auto_spawn_subagents=True, max_depth=7)
        tr = TraceReader(agent_id="TEST_TR", auto_spawn_subagents=True, max_depth=7)

        t1 = td.deposit_trace(trace_type="attraction", source_agent="A_UNIT", topic="TEST_PASS", strength=2.0)
        t2 = td.deposit_trace(trace_type="danger", source_agent="A_REG", topic="TEST_FAIL", strength=0.5)

        analysis = tr.sense_traces(traces=[t1, t2])
        self.assertEqual(len(analysis["attractions"]), 1)
        self.assertEqual(len(analysis["dangers"]), 1)
        self.assertTrue(analysis["safe"])

    def test_artifact_manager_sha256_versioning(self) -> None:
        """Verify ArtifactManager calculates SHA-256 and bumps versions."""
        am = ArtifactManager(agent_id="TEST_AM", auto_spawn_subagents=True, max_depth=7)
        self.assertIsInstance(am.creator, ArtifactCreator)

        art = am.store_artifact(filename="script.py", content="print('hello world')")
        self.assertEqual(art["version"], 1)
        orig_sha = art["sha256"]

        updated = am.update_artifact(art["artifact_id"], "print('hello universe')")
        self.assertEqual(updated["version"], 2)
        self.assertNotEqual(updated["sha256"], orig_sha)

    def test_session_manager_lifecycle(self) -> None:
        """Verify SessionManager creates and fetches active sessions."""
        sm = SessionManager(agent_id="TEST_SM", auto_spawn_subagents=True, max_depth=7)
        s = sm.create_session(metadata={"flow": "test"})
        self.assertIn("session_id", s)
        fetched = sm.get_session(s["session_id"])
        self.assertIsNotNone(fetched)

    def test_checkpoint_manager_snapshot(self) -> None:
        """Verify CheckpointManager creates and restores snapshots."""
        cm = CheckpointManager(agent_id="TEST_CM", auto_spawn_subagents=True, max_depth=7)
        self.assertIsInstance(cm.creator, CheckpointCreator)

        chk = cm.create_checkpoint(label="SNAP_1", state_data={"x": 42})
        restored = cm.restore_checkpoint(chk["checkpoint_id"])
        self.assertEqual(restored["x"], 42)

    def test_state_synchronizer_conflict_resolution(self) -> None:
        """Verify StateSynchronizer resolves conflicts using Last-Write-Wins."""
        ss = StateSynchronizer(agent_id="TEST_SS", auto_spawn_subagents=True, max_depth=7)
        loc = {"cfg": {"updated_at": 100, "v": 1}}
        rem = {"cfg": {"updated_at": 200, "v": 2}}
        res = ss.synchronize_states(local_state=loc, remote_state=rem)
        self.assertEqual(res["merged_state"]["cfg"]["v"], 2)

    def test_event_pub_sub(self) -> None:
        """Verify EventPublisher and EventSubscriber filter events."""
        ep = EventPublisher(agent_id="TEST_EP", auto_spawn_subagents=True, max_depth=7)
        es = EventSubscriber(agent_id="TEST_ES", auto_spawn_subagents=True, max_depth=7)

        e1 = ep.publish_event(category="TASK", action="TASK_STARTED")
        e2 = ep.publish_event(category="ERROR", action="SYS_ALERT")

        filtered = es.filter_events(events=[e1, e2], category="TASK")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["category"], "TASK")

    def test_message_router_priorities(self) -> None:
        """Verify MessageRouter sorts messages by descending priority."""
        mr = MessageRouter(agent_id="TEST_MR", auto_spawn_subagents=True, max_depth=7)
        msgs = [
            {"id": "1", "priority": "LOW"},
            {"id": "2", "priority": "CRITICAL"},
            {"id": "3", "priority": "NORMAL"},
        ]
        sorted_m = mr.prioritize_queue(msgs)
        self.assertEqual(sorted_m[0]["priority"], "CRITICAL")
        self.assertEqual(sorted_m[2]["priority"], "LOW")

    def test_state_compressor_gzip_roundtrip(self) -> None:
        """Verify StateCompressor compresses with gzip and decompresses cleanly."""
        sc = StateCompressor(agent_id="TEST_SC", auto_spawn_subagents=True, max_depth=7)
        raw_data = {"records": [f"item_{i}" for i in range(100)]}
        comp = sc.compress_state(data=raw_data)
        self.assertIn("compressed_payload", comp)

        decompressed = sc.decompress_state(comp["compressed_payload"])
        self.assertEqual(decompressed, raw_data)

    def test_commstate_orchestrator_end_to_end_pipeline(self) -> None:
        """Verify CommStateOrchestrator runs full 14-subsystem verification pipeline."""
        orch = CommStateOrchestrator(agent_id="TEST_CS_E2E", auto_spawn_subagents=True, max_depth=7)
        envelope = {
            "task_id": "T_CS_E2E",
            "payload": {"intent": "Verify communication & state subsystems"},
        }
        result = orch.execute_lifecycle(envelope)

        self.assertEqual(result["status"], "COMPLETED")
        rep = result["commstate_report"]
        self.assertTrue(rep["all_subsystems_healthy"])
        self.assertIn("task_store", rep)
        self.assertIn("trace_deposited", rep)
        self.assertIn("checkpoint", rep)

    def test_register_all_commstate_agents(self) -> None:
        """Verify registration helper registers all commstate agents into AgentRegistry."""
        res = register_all_commstate_agents(self.registry, max_depth=7)
        total = res["total_registered"]
        self.assertGreaterEqual(total, 15)
        self.assertIsNotNone(self.registry.get_agent("C1_COMMSTATE_ORCHESTRATOR"))


if __name__ == "__main__":
    unittest.main()
