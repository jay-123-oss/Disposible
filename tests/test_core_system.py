"""Comprehensive automated test suite for the Fractal Multi-Agent System Core."""

import os
import shutil
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import (
    AgentRegistry,
    BaseAgent,
    DepthLimitError,
    ExecutionResult,
    GatePhase,
    GateStatus,
    MessageBus,
    Orchestrator,
    QualityGate,
    QualityGateError,
    SandboxError,
    SandboxManager,
    StateManager,
    SystemMonitor,
    TaskPriority,
    TaskQueue,
    TaskStatus,
    TraceType,
)


class DummyAgent(BaseAgent):
    """Concrete DummyAgent for testing BaseAgent lifecycle."""

    def initialize(self, task_envelope):
        self.initialized = True

    def process(self, task_envelope):
        return {"status": "COMPLETED", "processed": True, "task_id": task_envelope.get("task_id")}

    def validate(self, result):
        if not result.get("processed"):
            raise ValueError("Validation failed")
        return result

    def cleanup(self):
        self.cleaned_up = True


class TestCoreFractalSystem(unittest.TestCase):
    """Test suite covering all 12 core files and design patterns."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="fractal_test_")
        self.state_dir = os.path.join(self.test_dir, "state")
        self.log_dir = os.path.join(self.test_dir, "logs")
        self.temp_dir = os.path.join(self.test_dir, "temp")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # 1. BaseAgent Lifecycle & Depth Bounding
    def test_base_agent_lifecycle_and_depth(self):
        root = DummyAgent(name="ROOT", max_depth=2)
        self.assertEqual(root.depth, 0)

        # Tool registration
        root.register_tool("echo", lambda x: x * 2)
        self.assertEqual(root.execute_tool("echo", 21), 42)

        # Lifecycle execution
        res = root.execute_lifecycle({"task_id": "T1"})
        self.assertTrue(res["processed"])
        self.assertEqual(root.state, "idle")

        # Spawn Child (Depth 1)
        child = root.spawn_subagent(DummyAgent, name="CHILD")
        self.assertEqual(child.depth, 1)

        # Spawn Grandchild (Depth 2)
        grandchild = child.spawn_subagent(DummyAgent, name="GRANDCHILD")
        self.assertEqual(grandchild.depth, 2)

        # Spawning beyond max_depth (Depth 3) must raise DepthLimitError
        with self.assertRaises(DepthLimitError):
            grandchild.spawn_subagent(DummyAgent, name="GREAT_GRANDCHILD")

    # 2. Agent Registry
    def test_agent_registry(self):
        registry = AgentRegistry(max_system_ram_mb=4096, max_agents=10)
        registry.clear()

        agent1 = DummyAgent(name="CODER", capabilities=["coding", "api"], resources_mb=512)
        registry.register_agent(agent1)

        self.assertEqual(len(registry.get_all_agents()), 1)
        self.assertEqual(registry.get_allocated_ram_mb(), 512)

        # Capability lookup
        found = registry.find_by_capability("coding")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].name, "CODER")

        # Health check
        health = registry.health_check_all()
        self.assertEqual(health["healthy_count"], 1)

        registry.unregister_agent(agent1.agent_id)
        self.assertEqual(len(registry.get_all_agents()), 0)
        self.assertEqual(registry.get_allocated_ram_mb(), 0)

    # 3. Task Queue & Priority & Dependencies
    def test_task_queue(self):
        queue = TaskQueue(max_retries=3)

        # Task 1 (Low Priority)
        queue.add_task("T_LOW", "Low intent", "dummy", priority=TaskPriority.LOW)
        # Task 2 (High Priority)
        queue.add_task("T_HIGH", "High intent", "dummy", priority=TaskPriority.HIGH)
        # Task 3 (Dependent on T_HIGH)
        queue.add_task("T_DEP", "Dep intent", "dummy", priority=TaskPriority.HIGH, dependencies=["T_HIGH"])

        # First task popped must be T_HIGH
        t1 = queue.get_next_task()
        self.assertIsNotNone(t1)
        self.assertEqual(t1.task_id, "T_HIGH")

        # T_DEP should NOT be runnable yet because T_HIGH is not completed
        t2 = queue.get_next_task()
        self.assertEqual(t2.task_id, "T_LOW")

        # Complete T_HIGH -> should unblock T_DEP
        queue.complete_task("T_HIGH", {"ok": True})

        t3 = queue.get_next_task()
        self.assertIsNotNone(t3)
        self.assertEqual(t3.task_id, "T_DEP")

        queue.complete_task("T_LOW")
        queue.complete_task("T_DEP")
        self.assertTrue(queue.is_all_completed())

    # 4. State Manager & Context Compression
    def test_state_manager(self):
        sm = StateManager(persist_path=self.state_dir, compression_threshold=100, max_checkpoints=3)
        sm.update_global_state({"test_key": "test_val"})
        state = sm.load_global_state()
        self.assertEqual(state.get("test_key"), "test_val")

        # Checkpoint creation
        chk_path = sm.create_checkpoint("TEST_CHK", metadata={"score": 95})
        self.assertTrue(os.path.exists(chk_path))

        # Context compression
        short_text = "Hello world"
        comp_short = sm.compress_context_if_needed(short_text, "short")
        self.assertFalse(comp_short["offloaded"])

        long_text = "A" * 600  # ~150 tokens > 100 threshold
        comp_long = sm.compress_context_if_needed(long_text, "long")
        self.assertTrue(comp_long["offloaded"])
        self.assertTrue("artifact_uri" in comp_long)

    # 5. Communication & Stigmergy
    def test_communication_and_stigmergy(self):
        mb = MessageBus(artifacts_dir=os.path.join(self.state_dir, "artifacts"))
        received = []
        mb.subscribe("AGENT_B", lambda msg: received.append(msg))

        # Send direct message
        mb.send_message("AGENT_A", "AGENT_B", "TEST_MSG", {"data": 123})
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].payload["data"], 123)

        # Stigmergy Trace
        trace_id = mb.emit_trace("AGENT_A", "SCHEMA_READY", TraceType.ATTRACTION, decay_rate=0.1)
        traces = mb.get_active_traces()
        self.assertTrue(any(t["trace_id"] == trace_id for t in traces))

        # Artifact Storage
        uri = mb.store_artifact("spec_01", "class User: pass")
        content = mb.retrieve_artifact("spec_01")
        self.assertEqual(content, "class User: pass")

    # 6. Quality Gate
    def test_quality_gate(self):
        qg = QualityGate(min_score=85.0)

        # Passing evaluation
        res_pass = qg.evaluate_phase(
            GatePhase.QG_4_TEST,
            {"correctness": 100, "security": 100, "maintainability": 90, "performance": 90, "test_coverage": 85},
        )
        self.assertEqual(res_pass.status, GateStatus.PASSED)
        self.assertGreaterEqual(res_pass.total_score, 85.0)

        # Failing evaluation (critical security finding)
        res_fail = qg.evaluate_phase(
            GatePhase.QG_5_SECURITY,
            {"correctness": 100, "critical_vulns": 1, "maintainability": 90, "performance": 90},
        )
        self.assertEqual(res_fail.status, GateStatus.FAILED)

        with self.assertRaises(QualityGateError):
            qg.validate_or_raise(
                GatePhase.QG_5_SECURITY,
                {"correctness": 100, "critical_vulns": 1, "maintainability": 90, "performance": 90},
            )

    # 7. Sandbox Manager
    def test_sandbox_manager(self):
        sb = SandboxManager(enabled=True, use_docker=False, timeout_seconds=5, temp_dir=self.temp_dir)

        # Normal execution
        code = "print(40 + 2)"
        res = sb.execute_python_code(code)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.stdout.strip(), "42")

        # Timeout execution
        timeout_code = "import time; time.sleep(10)"
        res_timeout = sb.execute_python_code(timeout_code, timeout_seconds=1)
        self.assertTrue(res_timeout.timed_out)

        # Forbidden import safety
        dangerous_code = "import ctypes; print('unsafe')"
        with self.assertRaises(SandboxError):
            sb.execute_python_code(dangerous_code)

    # 8. System Monitor
    def test_system_monitor(self):
        mon = SystemMonitor(log_dir=self.log_dir)
        mon.record_task_execution("T1", 2.5, 150)
        mon.record_error("Worker", "Simulated error")
        summary = mon.get_summary()
        self.assertEqual(summary["total_tasks_monitored"], 1)
        self.assertEqual(summary["error_count"], 1)
        self.assertGreater(summary["total_tokens_consumed"], 0)


if __name__ == "__main__":
    unittest.main()
