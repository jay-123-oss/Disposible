"""Comprehensive Test Suite for Distributed Architecture Layer Agents (Session 25)."""

import os
import sys
import unittest

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT_DIR in sys.path:
    sys.path.remove(_ROOT_DIR)
sys.path.insert(0, _ROOT_DIR)

from core.registry import AgentRegistry
from distributed import (
    ClusterCoordinator,
    ConsensusManager,
    DistributedOrchestrator,
    FaultTolerance,
    LoadBalancer,
    LogAggregator,
    MessageBroker,
    NodeManager,
    PerformanceMonitor,
    RaftEngine,
    ReplicationManager,
    SecurityManager,
    ServiceDiscovery,
    StateSynchronizer,
    TaskDistributor,
    register_all_distributed_agents,
)


class TestDistributedArchitectureLayer(unittest.TestCase):
    """Covers all 14 distributed agents, subagents, and cluster coordination workflows."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_orchestrator_spawns_13_subsystems(self) -> None:
        orch = DistributedOrchestrator(agent_id="TEST_DIST_ORCH", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(orch.node_manager)
        self.assertIsNotNone(orch.cluster_coordinator)
        self.assertIsNotNone(orch.load_balancer)
        self.assertIsNotNone(orch.service_discovery)
        self.assertIsNotNone(orch.state_synchronizer)
        self.assertIsNotNone(orch.message_broker)
        self.assertIsNotNone(orch.task_distributor)
        self.assertIsNotNone(orch.fault_tolerance)
        self.assertIsNotNone(orch.replication_manager)
        self.assertIsNotNone(orch.consensus_manager)
        self.assertIsNotNone(orch.performance_monitor)
        self.assertIsNotNone(orch.security_manager)
        self.assertIsNotNone(orch.log_aggregator)
        self.assertEqual(len(orch.children), 13)

    def test_node_manager_lifecycle(self) -> None:
        mgr = NodeManager(agent_id="TEST_NODE_MGR", auto_spawn_subagents=True, max_depth=7)
        res = mgr.register_node({"id": "node-test-1", "host": "10.0.0.1", "port": 8000, "role": "follower"})
        self.assertTrue(res["registered"])
        self.assertEqual(res["total_nodes"], 1)

        hb = mgr.record_heartbeat("node-test-1")
        self.assertTrue(hb)

        health = mgr.check_nodes_health(timeout=30.0)
        self.assertEqual(health["healthy"], 1)

        dereg = mgr.deregister_node("node-test-1")
        self.assertTrue(dereg["deregistered"])
        self.assertEqual(dereg["remaining"], 0)

    def test_cluster_coordinator_and_election(self) -> None:
        coord = ClusterCoordinator(agent_id="TEST_COORD", auto_spawn_subagents=True, max_depth=7)
        coord.join_cluster("node-1", {"id": "node-1", "role": "follower"})
        coord.join_cluster("node-2", {"id": "node-2", "role": "follower"})
        top = coord.get_cluster_topology()
        self.assertEqual(top["size"], 2)

        elect = coord.elect_leader("node-2")
        self.assertTrue(elect["elected"])
        self.assertEqual(coord.current_leader, "node-2")

        leave = coord.leave_cluster("node-1")
        self.assertTrue(leave["left"])
        self.assertEqual(coord.get_cluster_topology()["size"], 1)

    def test_load_balancer_algorithms(self) -> None:
        lb = LoadBalancer(agent_id="TEST_LB", auto_spawn_subagents=True, max_depth=7)
        nodes = ["node-1", "node-2", "node-3"]
        lb.update_nodes(nodes, weights={"node-1": 10, "node-2": 20, "node-3": 30})

        # Round robin
        n1 = lb.route_request("round_robin")
        n2 = lb.route_request("round_robin")
        self.assertIn(n1, nodes)
        self.assertIn(n2, nodes)

        # Consistent hash
        h_node = lb.route_request("consistent_hash", key="user_session_123")
        self.assertIn(h_node, nodes)

        # Weighted distribution
        w_node = lb.route_request("weighted_distribution")
        self.assertEqual(w_node, "node-3")

    def test_service_discovery_lifecycle(self) -> None:
        sd = ServiceDiscovery(agent_id="TEST_SD", auto_spawn_subagents=True, max_depth=7)
        reg = sd.register_service("auth-service", "10.0.0.5:5000", ttl=60)
        self.assertTrue(reg["registered"])

        instances = sd.discover_service("auth-service")
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]["endpoint"], "10.0.0.5:5000")

        pruned = sd.prune_expired()
        self.assertEqual(pruned["active_count"], 1)

    def test_state_synchronizer(self) -> None:
        sync = StateSynchronizer(agent_id="TEST_SYNC", auto_spawn_subagents=True, max_depth=7)
        sync.set_entry("config.timeout", 30)

        remote = {"config.timeout": {"value": 45, "timestamp": 9999999999}}
        res = sync.sync_state(remote)
        self.assertTrue(res["synced"])
        self.assertEqual(sync.local_state["config.timeout"]["value"], 45)

    def test_message_broker_pubsub(self) -> None:
        broker = MessageBroker(agent_id="TEST_MB", auto_spawn_subagents=True, max_depth=7)
        received = []

        broker.subscribe("cluster.events", lambda msg: received.append(msg))
        pub = broker.publish("cluster.events", {"event": "node_joined", "node": "node-5"})
        self.assertTrue(pub["published"])
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["payload"]["node"], "node-5")

    def test_task_distributor(self) -> None:
        dist = TaskDistributor(agent_id="TEST_TD", auto_spawn_subagents=True, max_depth=7)
        task = {
            "id": "job-100",
            "items": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        }
        res = dist.distribute_task(task, nodes=["node-1", "node-2"])
        self.assertTrue(res["distributed"])
        self.assertGreater(res["subtask_count"], 1)

    def test_fault_tolerance_and_circuit_breaker(self) -> None:
        ft = FaultTolerance(agent_id="TEST_FT", auto_spawn_subagents=True, max_depth=7, failure_threshold=2)
        # Healthy service check
        self.assertTrue(ft.can_execute_service("payment-api"))

        # Trip circuit breaker
        ft.record_service_failure("payment-api")
        ft.record_service_failure("payment-api")
        self.assertFalse(ft.can_execute_service("payment-api"))

        # Reset
        ft.record_service_success("payment-api")
        self.assertTrue(ft.can_execute_service("payment-api"))

    def test_replication_manager(self) -> None:
        rep = ReplicationManager(agent_id="TEST_REP", auto_spawn_subagents=True, max_depth=7, factor=3)
        rep.set_nodes(["node-1", "node-2", "node-3"])
        res = rep.replicate_data({"key": "data_val", "id": "rec-1"}, mode="sync")
        self.assertTrue(res["replicated"])
        self.assertEqual(res["target_count"], 3)

    def test_consensus_manager_and_raft(self) -> None:
        cm = ConsensusManager(agent_id="TEST_CM", auto_spawn_subagents=True, max_depth=7)
        res = cm.submit_command({"op": "set", "key": "k1", "val": "v1"})
        self.assertTrue(res["committed"])
        self.assertEqual(res["entry_index"], 1)

        status = cm.get_consensus_status()
        self.assertEqual(status["role"], "leader")
        self.assertEqual(status["commit_index"], 1)

    def test_performance_monitor(self) -> None:
        pm = PerformanceMonitor(agent_id="TEST_PM", auto_spawn_subagents=True, max_depth=7, alert_threshold=80.0)
        pm.collect_metrics("node-1", cpu_percent=30.0, memory_mb=256)
        pm.collect_metrics("node-2", cpu_percent=40.0, memory_mb=512)
        health = pm.evaluate_cluster_health()
        self.assertTrue(health["healthy"])
        self.assertEqual(health["aggregated"]["node_count"], 2)

    def test_security_manager(self) -> None:
        sm = SecurityManager(agent_id="TEST_SM", auto_spawn_subagents=True, max_depth=7)
        token = sm.generate_node_token("node-42")
        auth = sm.authenticate_node("node-42", token)
        self.assertTrue(auth["authenticated"])

        bad_auth = sm.authenticate_node("node-42", "invalid-token")
        self.assertFalse(bad_auth["authenticated"])

    def test_log_aggregator(self) -> None:
        la = LogAggregator(agent_id="TEST_LA", auto_spawn_subagents=True, max_depth=7)
        la.ingest_logs("node-1", ["cluster boot initiated", "heartbeat ok"])
        matches = la.search_logs(query="boot")
        self.assertEqual(len(matches), 1)

    def test_cluster_lifecycle_orchestrator(self) -> None:
        orch = DistributedOrchestrator(agent_id="TEST_LIFECYCLE_ORCH", auto_spawn_subagents=True, max_depth=7)
        res = orch.run_cluster_lifecycle()
        self.assertTrue(res["bootstrapped"])
        self.assertEqual(res["node_count"], 3)
        self.assertIsNotNone(res["leader"])

    def test_register_all_distributed_agents(self) -> None:
        result = register_all_distributed_agents(self.registry)
        self.assertEqual(result["total_registered"], 66)


if __name__ == "__main__":
    unittest.main()
