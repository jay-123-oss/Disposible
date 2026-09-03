"""CICDSetuper agent generating GitHub Actions, Jenkins, and GitLab CI pipeline workflows."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.infrastructure.exceptions import CICDError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Infrastructure.CICDSetuper")


# ==============================================================================
# L5 Atomic CI/CD Subagents
# ==============================================================================

class GithubActionsGenerator(BaseAgent):
    """L5 agent authoring production GitHub Actions workflow files."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("GithubActionsGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        workflow = (
            "name: Continuous Integration & Deployment\n\n"
            "on:\n"
            "  push:\n"
            "    branches: [ main ]\n"
            "  pull_request:\n"
            "    branches: [ main ]\n\n"
            "jobs:\n"
            "  test-and-lint:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v3\n"
            "      - name: Set up Python 3.10\n"
            "        uses: actions/setup-python@v4\n"
            "        with:\n"
            "          python-version: \"3.10\"\n"
            "          cache: 'pip'\n"
            "      - name: Install dependencies\n"
            "        run: pip install -r requirements.txt pytest flake8 black\n"
            "      - name: Lint with flake8 & black\n"
            "        run: |\n"
            "          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics\n"
            "          black --check .\n"
            "      - name: Run unit & integration tests\n"
            "        run: pytest --maxfail=1 --disable-warnings -v\n\n"
            "  docker-build:\n"
            "    needs: test-and-lint\n"
            "    runs-on: ubuntu-latest\n"
            "    if: github.ref == 'refs/heads/main'\n"
            "    steps:\n"
            "      - uses: actions/checkout@v3\n"
            "      - name: Build Docker Image\n"
            "        run: docker build -t app:latest .\n"
        )
        return {"status": "COMPLETED", "github_actions_yaml": workflow}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("GithubActionsGenerator %s cleaned up.", self.agent_id)


class JenkinsGenerator(BaseAgent):
    """L5 agent authoring declarative Groovy Jenkinsfile pipelines."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("JenkinsGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        jenkinsfile = (
            "pipeline {\n"
            "    agent any\n"
            "    stages {\n"
            "        stage('Checkout') {\n"
            "            steps { checkout scm }\n"
            "        }\n"
            "        stage('Test & Quality Gate') {\n"
            "            steps { sh 'pytest && python -m unittest' }\n"
            "        }\n"
            "        stage('Build Image') {\n"
            "            steps { sh 'docker build -t app:${BUILD_NUMBER} .' }\n"
            "        }\n"
            "    }\n"
            "}\n"
        )
        return {"status": "COMPLETED", "jenkinsfile": jenkinsfile}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("JenkinsGenerator %s cleaned up.", self.agent_id)


class GitlabCiGenerator(BaseAgent):
    """L5 agent authoring .gitlab-ci.yml pipeline configuration."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("GitlabCiGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        gitlab_yaml = (
            "stages:\n"
            "  - test\n"
            "  - build\n\n"
            "unit-tests:\n"
            "  stage: test\n"
            "  image: python:3.10-slim\n"
            "  script:\n"
            "    - pip install -r requirements.txt\n"
            "    - pytest\n\n"
            "docker-image:\n"
            "  stage: build\n"
            "  image: docker:24.0\n"
            "  services:\n"
            "    - docker:dind\n"
            "  script:\n"
            "    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .\n"
        )
        return {"status": "COMPLETED", "gitlab_ci_yaml": gitlab_yaml}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("GitlabCiGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 CICDSetuper Agent
# ==============================================================================

class CICDSetuper(BaseAgent):
    """L4 coordinator generating multi-platform CI/CD automated pipeline workflows."""

    def __init__(
        self,
        name: str = "CICDSetuper",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "cicd_setup",
            "github_actions_generation",
            "jenkins_pipeline_generation",
            "gitlab_ci_generation",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "I4_CICD_SETUPER",
        )

        self.gh_gen: Optional[GithubActionsGenerator] = None
        self.jk_gen: Optional[JenkinsGenerator] = None
        self.gl_gen: Optional[GitlabCiGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_cicd_pipelines", self.generate_cicd_pipelines)

    def _spawn_subagents(self) -> None:
        """Spawn atomic CI/CD subagents (Rule 1 & Rule 5)."""
        logger.info("CICDSetuper %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.gh_gen = self.spawn_subagent(
            GithubActionsGenerator,
            name="GithubActionsGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.jk_gen = self.spawn_subagent(
            JenkinsGenerator,
            name="JenkinsGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.gl_gen = self.spawn_subagent(
            GitlabCiGenerator,
            name="GitlabCiGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CICDSetuper %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        bundle = self.generate_cicd_pipelines()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "cicd_bundle": bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        bundle = result.get("cicd_bundle")
        if not bundle or "github_actions" not in bundle:
            raise CICDError("CICDSetuper produced incomplete bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("CICDSetuper %s cleanup complete.", self.agent_id)

    def generate_cicd_pipelines(self) -> Dict[str, str]:
        """Synthesize GitHub Actions, Jenkins, and GitLab CI workflow templates."""
        gh = self.gh_gen.process({}) if self.gh_gen else {"github_actions_yaml": ""}
        jk = self.jk_gen.process({}) if self.jk_gen else {"jenkinsfile": ""}
        gl = self.gl_gen.process({}) if self.gl_gen else {"gitlab_ci_yaml": ""}

        return {
            "github_actions": gh.get("github_actions_yaml", ""),
            "jenkinsfile": jk.get("jenkinsfile", ""),
            "gitlab_ci": gl.get("gitlab_ci_yaml", ""),
        }
