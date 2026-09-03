"""Comprehensive Unit Test Suite for Infrastructure Layer Agents (Session 8)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.infrastructure import (
    AwsAlbGenerator,
    BackupSetuper,
    CICDSetuper,
    ComposeGenerator,
    DatabaseBackupGenerator,
    DeploymentGenerator,
    DockerConfigurer,
    DockerfileGenerator,
    EnvironmentManager,
    HealthCheckDesigner,
    InfrastructureOrchestrator,
    KubernetesManifestGenerator,
    LoadBalancerConfigurer,
    LoggingStackSetuper,
    MonitoringStackSetuper,
    NetworkConfigurer,
    PrometheusConfigGenerator,
    SecretManager,
    TerraformScriptGenerator,
    VaultConfigurer,
    register_all_infrastructure_agents,
)
from core.registry import AgentRegistry


class TestInfrastructureAgents(unittest.TestCase):
    """Test suite covering all 14 Infrastructure domain agents and fractal subagent structures."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_infrastructure_orchestrator_spawns_subsystems(self) -> None:
        """Verify InfrastructureOrchestrator spawns all 13 L4 infrastructure coordinators."""
        orch = InfrastructureOrchestrator(agent_id="TEST_INFRA_ORCH", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(orch.docker_cfg)
        self.assertIsNotNone(orch.compose_gen)
        self.assertIsNotNone(orch.cicd_setup)
        self.assertIsNotNone(orch.env_mgr)
        self.assertIsNotNone(orch.k8s_gen)
        self.assertIsNotNone(orch.tf_gen)
        self.assertIsNotNone(orch.health_des)
        self.assertIsNotNone(orch.lb_cfg)
        self.assertIsNotNone(orch.mon_setup)
        self.assertIsNotNone(orch.log_setup)
        self.assertIsNotNone(orch.secret_mgr)
        self.assertIsNotNone(orch.net_cfg)
        self.assertIsNotNone(orch.backup_setup)

        child_names = [c.name for c in orch.children.values()]
        self.assertIn("DockerConfigurer", child_names)
        self.assertIn("ComposeGenerator", child_names)
        self.assertIn("CICDSetuper", child_names)
        self.assertIn("EnvironmentManager", child_names)
        self.assertIn("KubernetesManifestGenerator", child_names)
        self.assertIn("TerraformScriptGenerator", child_names)
        self.assertIn("HealthCheckDesigner", child_names)
        self.assertIn("LoadBalancerConfigurer", child_names)
        self.assertIn("MonitoringStackSetuper", child_names)
        self.assertIn("LoggingStackSetuper", child_names)
        self.assertIn("SecretManager", child_names)
        self.assertIn("NetworkConfigurer", child_names)
        self.assertIn("BackupSetuper", child_names)

    def test_docker_configurer_spawns_subagents(self) -> None:
        """Verify DockerConfigurer spawns DockerfileGenerator, MultiStageBuilder, OptimizationChecker."""
        dc = DockerConfigurer(agent_id="TEST_DC", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(dc.df_gen)
        self.assertIsNotNone(dc.ms_builder)
        self.assertIsNotNone(dc.opt_checker)
        self.assertIsInstance(dc.df_gen, DockerfileGenerator)

    def test_compose_generator_spawns_subagents(self) -> None:
        """Verify ComposeGenerator spawns ServiceDefiner, NetworkDefiner, VolumeDefiner."""
        cg = ComposeGenerator(agent_id="TEST_CG", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(cg.service_def)
        self.assertIsNotNone(cg.network_def)
        self.assertIsNotNone(cg.volume_def)

    def test_cicd_setuper_spawns_subagents(self) -> None:
        """Verify CICDSetuper spawns GithubActionsGenerator, JenkinsGenerator, GitlabCiGenerator."""
        cs = CICDSetuper(agent_id="TEST_CS", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(cs.gh_gen)
        self.assertIsNotNone(cs.jk_gen)
        self.assertIsNotNone(cs.gl_gen)

    def test_environment_manager_spawns_subagents(self) -> None:
        """Verify EnvironmentManager spawns EnvTemplateGenerator, ConfigValidator, EnvLoader."""
        em = EnvironmentManager(agent_id="TEST_EM", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(em.template_gen)
        self.assertIsNotNone(em.config_val)
        self.assertIsNotNone(em.env_loader)

    def test_kubernetes_manifest_generator_spawns_subagents(self) -> None:
        """Verify KubernetesManifestGenerator spawns Deployment, Service, Ingress, ConfigMap generators."""
        kg = KubernetesManifestGenerator(agent_id="TEST_KG", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(kg.deploy_gen)
        self.assertIsNotNone(kg.svc_gen)
        self.assertIsNotNone(kg.ing_gen)
        self.assertIsNotNone(kg.cfg_gen)
        self.assertIsInstance(kg.deploy_gen, DeploymentGenerator)

    def test_terraform_script_generator_spawns_subagents(self) -> None:
        """Verify TerraformScriptGenerator spawns ProviderConfigurer, ResourceDefiner, StateManager."""
        tg = TerraformScriptGenerator(agent_id="TEST_TG", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(tg.provider_cfg)
        self.assertIsNotNone(tg.res_def)
        self.assertIsNotNone(tg.state_mgr)

    def test_health_check_designer_spawns_subagents(self) -> None:
        """Verify HealthCheckDesigner spawns Readiness, Liveness, Startup probe generators."""
        hd = HealthCheckDesigner(agent_id="TEST_HD", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(hd.ready_gen)
        self.assertIsNotNone(hd.live_gen)
        self.assertIsNotNone(hd.startup_gen)

    def test_load_balancer_configurer_spawns_subagents(self) -> None:
        """Verify LoadBalancerConfigurer spawns Nginx, Traefik, AwsAlb generators."""
        lb = LoadBalancerConfigurer(agent_id="TEST_LB", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(lb.nginx_gen)
        self.assertIsNotNone(lb.traefik_gen)
        self.assertIsNotNone(lb.alb_gen)
        self.assertIsInstance(lb.alb_gen, AwsAlbGenerator)

    def test_monitoring_stack_setuper_spawns_subagents(self) -> None:
        """Verify MonitoringStackSetuper spawns Prometheus, Grafana, AlertManager subagents."""
        ms = MonitoringStackSetuper(agent_id="TEST_MS", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(ms.prom_gen)
        self.assertIsNotNone(ms.graf_gen)
        self.assertIsNotNone(ms.alert_cfg)
        self.assertIsInstance(ms.prom_gen, PrometheusConfigGenerator)

    def test_logging_stack_setuper_spawns_subagents(self) -> None:
        """Verify LoggingStackSetuper spawns Elasticsearch, Logstash, Kibana subagents."""
        ls = LoggingStackSetuper(agent_id="TEST_LS", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(ls.es_cfg)
        self.assertIsNotNone(ls.ls_cfg)
        self.assertIsNotNone(ls.kb_cfg)

    def test_secret_manager_spawns_subagents(self) -> None:
        """Verify SecretManager spawns Vault, AwsSecretsManager, EncryptionKeyGenerator."""
        sm = SecretManager(agent_id="TEST_SM", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(sm.vault_cfg)
        self.assertIsNotNone(sm.aws_sm)
        self.assertIsNotNone(sm.key_gen)
        self.assertIsInstance(sm.vault_cfg, VaultConfigurer)

    def test_network_configurer_spawns_subagents(self) -> None:
        """Verify NetworkConfigurer spawns Firewall, Vpc, ServiceMesh subagents."""
        nc = NetworkConfigurer(agent_id="TEST_NC", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(nc.fw_gen)
        self.assertIsNotNone(nc.vpc_cfg)
        self.assertIsNotNone(nc.mesh_cfg)

    def test_backup_setuper_spawns_subagents(self) -> None:
        """Verify BackupSetuper spawns DatabaseBackup, FileBackup, RecoveryPlan generators."""
        bs = BackupSetuper(agent_id="TEST_BS", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(bs.db_gen)
        self.assertIsNotNone(bs.file_gen)
        self.assertIsNotNone(bs.rec_gen)
        self.assertIsInstance(bs.db_gen, DatabaseBackupGenerator)

    def test_infrastructure_orchestrator_end_to_end_provisioning(self) -> None:
        """Verify InfrastructureOrchestrator generates comprehensive infrastructure bundle."""
        orch = InfrastructureOrchestrator(agent_id="TEST_INFRA_E2E", auto_spawn_subagents=True, max_depth=7)
        envelope = {
            "task_id": "T_INFRA_E2E",
            "payload": {
                "base_image": "python:3.10-slim",
                "replicas": 3,
                "namespace": "production",
                "region": "us-east-1",
            },
        }
        result = orch.execute_lifecycle(envelope)

        self.assertEqual(result["status"], "COMPLETED")
        bundle = result["infrastructure_bundle"]
        self.assertEqual(bundle["status"], "PROVISIONED")
        self.assertIn("docker", bundle)
        self.assertIn("kubernetes", bundle)
        self.assertIn("terraform", bundle)
        self.assertIn("health_checks", bundle)
        self.assertIn("backup", bundle)
        self.assertTrue(bundle["docker"]["passed"])

    def test_register_all_infrastructure_agents(self) -> None:
        """Verify registration helper registers all infrastructure agents into AgentRegistry."""
        res = register_all_infrastructure_agents(self.registry, max_depth=7)
        total = res["total_registered"]
        self.assertGreaterEqual(total, 14)
        self.assertIsNotNone(self.registry.get_agent("I1_INFRASTRUCTURE_ORCHESTRATOR"))


if __name__ == "__main__":
    unittest.main()
