"""Comprehensive Test Suite for Deployment & Distribution Layer Agents (Session 14)."""

import os
import sys
import unittest

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT_DIR in sys.path:
    sys.path.remove(_ROOT_DIR)
sys.path.insert(0, _ROOT_DIR)

from agents.deployment import (
    CiCdPipelineBuilder,
    CloudDeployer,
    DeploymentOrchestrator,
    DockerDeployer,
    EnvironmentSetup,
    HealthCheckDeployer,
    K8sDeployer,
    PackageBuilder,
    ReleaseManager,
    RollbackManager,
    SecretDeployer,
    SetupScriptGenerator,
    UpdateManager,
    VersionManager,
    register_all_deployment_agents,
)
from core.registry import AgentRegistry


class TestDeploymentLayer(unittest.TestCase):
    """Test suite covering all 14 deployment agents, subagents, and deployment artifacts."""

    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.registry.clear()

    def test_deployment_orchestrator_spawns_subsystems(self) -> None:
        """Verify DeploymentOrchestrator spawns all 13 L4 deployment coordinators."""
        orch = DeploymentOrchestrator(agent_id="TEST_DEP_ORCH", auto_spawn_subagents=True, max_depth=7)
        self.assertIsNotNone(orch.setup_gen)
        self.assertIsNotNone(orch.docker_dep)
        self.assertIsNotNone(orch.k8s_dep)
        self.assertIsNotNone(orch.cloud_dep)
        self.assertIsNotNone(orch.pkg_builder)
        self.assertIsNotNone(orch.version_mgr)
        self.assertIsNotNone(orch.release_mgr)
        self.assertIsNotNone(orch.update_mgr)
        self.assertIsNotNone(orch.rollback_mgr)
        self.assertIsNotNone(orch.cicd_builder)
        self.assertIsNotNone(orch.env_setup)
        self.assertIsNotNone(orch.secret_dep)
        self.assertIsNotNone(orch.health_dep)

        child_names = [c.name for c in orch.children.values()]
        self.assertEqual(len(child_names), 13)
        self.assertIn("SetupScriptGenerator", child_names)
        self.assertIn("DockerDeployer", child_names)
        self.assertIn("K8sDeployer", child_names)
        self.assertIn("CloudDeployer", child_names)
        self.assertIn("PackageBuilder", child_names)
        self.assertIn("VersionManager", child_names)
        self.assertIn("ReleaseManager", child_names)
        self.assertIn("UpdateManager", child_names)
        self.assertIn("RollbackManager", child_names)
        self.assertIn("CiCdPipelineBuilder", child_names)
        self.assertIn("EnvironmentSetup", child_names)
        self.assertIn("SecretDeployer", child_names)
        self.assertIn("HealthCheckDeployer", child_names)

    def test_setup_script_generator(self) -> None:
        """Verify SetupScriptGenerator coordinates install, config, dependencies, and verification."""
        gen = SetupScriptGenerator(agent_id="TEST_SETUP_GEN", auto_spawn_subagents=True, max_depth=7)
        res = gen.generate_setup_scripts()
        self.assertTrue(res["all_generated"])
        self.assertTrue(res["install"]["generated"])
        self.assertTrue(res["config"]["generated"])
        self.assertTrue(res["dependencies"]["generated"])
        self.assertTrue(res["verification"]["generated"])

    def test_docker_deployer(self) -> None:
        """Verify DockerDeployer coordinates build, push, runner, and docker-compose."""
        dep = DockerDeployer(agent_id="TEST_DOCKER_DEP", auto_spawn_subagents=True, max_depth=7)
        res = dep.deploy_docker()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["build"]["built"])
        self.assertTrue(res["push"]["pushed"])
        self.assertTrue(res["runner"]["running"])
        self.assertTrue(res["compose"]["deployed"])

    def test_k8s_deployer(self) -> None:
        """Verify K8sDeployer coordinates apply, delete, scale, and rollout."""
        dep = K8sDeployer(agent_id="TEST_K8S_DEP", auto_spawn_subagents=True, max_depth=7)
        res = dep.deploy_k8s()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["apply"]["applied"])
        self.assertTrue(res["delete"]["deleted"])
        self.assertTrue(res["scale"]["scaled"])
        self.assertTrue(res["rollout"]["verified"])

    def test_cloud_deployer(self) -> None:
        """Verify CloudDeployer coordinates AWS, GCP, Azure, and Terraform."""
        dep = CloudDeployer(agent_id="TEST_CLOUD_DEP", auto_spawn_subagents=True, max_depth=7)
        res = dep.deploy_cloud()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["aws"]["deployed"])
        self.assertTrue(res["gcp"]["deployed"])
        self.assertTrue(res["azure"]["deployed"])
        self.assertTrue(res["multi_cloud"]["validated"])

    def test_package_builder(self) -> None:
        """Verify PackageBuilder coordinates wheel, docker image, exe, and distribution."""
        builder = PackageBuilder(agent_id="TEST_PKG_BUILDER", auto_spawn_subagents=True, max_depth=7)
        res = builder.build_all_packages()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["wheel"]["built"])
        self.assertTrue(res["docker_tar"]["built"])
        self.assertTrue(res["executable"]["built"])
        self.assertTrue(res["distribution"]["prepared"])

    def test_version_manager(self) -> None:
        """Verify VersionManager coordinates semver bump, tag, compare, and history."""
        mgr = VersionManager(agent_id="TEST_VER_MGR", auto_spawn_subagents=True, max_depth=7)
        res = mgr.manage_version()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["update"]["updated"])
        self.assertTrue(res["tag"]["tagged"])
        self.assertTrue(res["history"]["recorded"])

    def test_release_manager(self) -> None:
        """Verify ReleaseManager coordinates release creation, notes, validation, and publishing."""
        mgr = ReleaseManager(agent_id="TEST_REL_MGR", auto_spawn_subagents=True, max_depth=7)
        res = mgr.manage_release()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["create"]["created"])
        self.assertTrue(res["notes"]["generated"])
        self.assertTrue(res["validate"]["validated"])
        self.assertTrue(res["publish"]["published"])

    def test_update_manager(self) -> None:
        """Verify UpdateManager coordinates update check, download, install, and verification."""
        mgr = UpdateManager(agent_id="TEST_UPD_MGR", auto_spawn_subagents=True, max_depth=7)
        res = mgr.manage_update()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["check"]["checked"])
        self.assertTrue(res["download"]["downloaded"])
        self.assertTrue(res["install"]["installed"])
        self.assertTrue(res["verify"]["verified"])

    def test_rollback_manager(self) -> None:
        """Verify RollbackManager coordinates restore points, execution, verification, and history."""
        mgr = RollbackManager(agent_id="TEST_ROL_MGR", auto_spawn_subagents=True, max_depth=7)
        res = mgr.manage_rollback()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["point"]["created"])
        self.assertTrue(res["execute"]["executed"])
        self.assertTrue(res["verify"]["verified"])
        self.assertTrue(res["history"]["recorded"])

    def test_cicd_pipeline_builder(self) -> None:
        """Verify CiCdPipelineBuilder coordinates GitHub Actions, Jenkins, GitLab, and CircleCI."""
        builder = CiCdPipelineBuilder(agent_id="TEST_CICD_BLD", auto_spawn_subagents=True, max_depth=7)
        res = builder.build_all_pipelines()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["github_actions"]["generated"])
        self.assertTrue(res["jenkins"]["generated"])
        self.assertTrue(res["gitlab"]["generated"])
        self.assertTrue(res["circleci"]["generated"])

    def test_environment_setup(self) -> None:
        """Verify EnvironmentSetup coordinates dev, staging, prod, and validation."""
        setup_env = EnvironmentSetup(agent_id="TEST_ENV_SET", auto_spawn_subagents=True, max_depth=7)
        res = setup_env.setup_environments()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["dev"]["configured"])
        self.assertTrue(res["staging"]["configured"])
        self.assertTrue(res["production"]["configured"])
        self.assertTrue(res["validator"]["valid"])

    def test_secret_deployer(self) -> None:
        """Verify SecretDeployer coordinates Vault, AWS Secrets, K8s Secrets, and KMS."""
        sec = SecretDeployer(agent_id="TEST_SEC_DEP", auto_spawn_subagents=True, max_depth=7)
        res = sec.deploy_secrets()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["vault"]["provisioned"])
        self.assertTrue(res["aws_secrets"]["provisioned"])
        self.assertTrue(res["k8s_secrets"]["provisioned"])
        self.assertTrue(res["encryption"]["provisioned"])

    def test_health_check_deployer(self) -> None:
        """Verify HealthCheckDeployer coordinates liveness, readiness, startup, and metrics probes."""
        hlt = HealthCheckDeployer(agent_id="TEST_HLT_DEP", auto_spawn_subagents=True, max_depth=7)
        res = hlt.deploy_health_checks()
        self.assertTrue(res["all_successful"])
        self.assertTrue(res["liveness"]["configured"])
        self.assertTrue(res["readiness"]["configured"])
        self.assertTrue(res["startup"]["configured"])
        self.assertTrue(res["metrics"]["configured"])

    def test_deployment_orchestrator_lifecycle(self) -> None:
        """Verify DeploymentOrchestrator runs full lifecycle across all 13 coordinators."""
        orch = DeploymentOrchestrator(agent_id="TEST_FULL_DEP", auto_spawn_subagents=True, max_depth=7)
        envelope = {"task_id": "T_DEP_FULL", "payload": {}}
        res = orch.execute_lifecycle(envelope)

        self.assertEqual(res["status"], "COMPLETED")
        rep = res["deployment_report"]
        self.assertTrue(rep["all_deployments_successful"])
        self.assertEqual(rep["total_subsystems"], 13)

    def test_register_all_deployment_agents(self) -> None:
        """Verify register_all_deployment_agents registers root, coordinators, and subagents."""
        res = register_all_deployment_agents(self.registry, max_depth=7)
        total = res["total_registered"]
        self.assertGreaterEqual(total, 66)  # 1 + 13 + 52 = 66
        self.assertIsNotNone(self.registry.get_agent("DD1_DEPLOYMENT_ORCHESTRATOR"))

    def test_generated_deployment_files_exist(self) -> None:
        """Verify all key deployment manifests, scripts, dockerfiles, and pipelines exist."""
        required = [
            "setup/__init__.py", "setup/install.py", "setup/configure.py", "setup/dependencies.py", "setup/verify.py",
            "install.sh", "install.bat", "setup.py", "requirements.txt", "requirements-dev.txt",
            "docker/__init__.py", "docker/Dockerfile", "docker/docker-compose.yml", "docker/docker_builder.py",
            "k8s/__init__.py", "k8s/deployment.yaml", "k8s/service.yaml", "k8s/ingress.yaml", "k8s/hpa.yaml",
            "cloud/__init__.py", "cloud/aws_deployer.py", "cloud/gcp_deployer.py", "cloud/terraform/main.tf",
            "package/__init__.py", "package/python_package.py", "package/distribution.py",
            "version/__init__.py", "version/version_manager.py", "version/release_manager.py",
            "cicd/__init__.py", "cicd/github_actions/ci.yml", "cicd/jenkins/Jenkinsfile", "cicd/gitlab/.gitlab-ci.yml"
        ]
        for rel in required:
            fp = os.path.join(_ROOT_DIR, rel)
            self.assertTrue(os.path.isfile(fp), f"Missing deployment file: {rel}")
            self.assertGreater(os.path.getsize(fp), 10, f"Empty file: {rel}")


if __name__ == "__main__":
    unittest.main()
