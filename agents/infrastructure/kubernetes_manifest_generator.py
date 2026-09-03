"""KubernetesManifestGenerator agent synthesizing production Deployment, Service, Ingress, and ConfigMap manifests."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.infrastructure.exceptions import KubernetesError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Infrastructure.KubernetesManifestGenerator")


# ==============================================================================
# L5 Atomic Kubernetes Subagents
# ==============================================================================

class DeploymentGenerator(BaseAgent):
    """L5 agent authoring Kubernetes Deployment manifests with resource limits and health probes."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DeploymentGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        replicas = payload.get("replicas", 3)
        namespace = payload.get("namespace", "production")

        deploy_yaml = (
            "apiVersion: apps/v1\n"
            "kind: Deployment\n"
            "metadata:\n"
            "  name: app-deployment\n"
            f"  namespace: {namespace}\n"
            "  labels:\n"
            "    app: microservice\n"
            "spec:\n"
            f"  replicas: {replicas}\n"
            "  selector:\n"
            "    matchLabels:\n"
            "      app: microservice\n"
            "  template:\n"
            "    metadata:\n"
            "      labels:\n"
            "        app: microservice\n"
            "    spec:\n"
            "      securityContext:\n"
            "        runAsNonRoot: true\n"
            "        runAsUser: 1001\n"
            "      containers:\n"
            "        - name: api\n"
            "          image: microservice:latest\n"
            "          imagePullPolicy: IfNotPresent\n"
            "          ports:\n"
            "            - containerPort: 8000\n"
            "          resources:\n"
            "            limits:\n"
            "              cpu: \"500m\"\n"
            "              memory: \"512Mi\"\n"
            "            requests:\n"
            "              cpu: \"100m\"\n"
            "              memory: \"128Mi\"\n"
            "          livenessProbe:\n"
            "            httpGet:\n"
            "              path: /health/live\n"
            "              port: 8000\n"
            "            initialDelaySeconds: 15\n"
            "            periodSeconds: 10\n"
            "          readinessProbe:\n"
            "            httpGet:\n"
            "              path: /health/ready\n"
            "              port: 8000\n"
            "            initialDelaySeconds: 5\n"
            "            periodSeconds: 5\n"
        )
        return {"status": "COMPLETED", "deployment_yaml": deploy_yaml}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DeploymentGenerator %s cleaned up.", self.agent_id)


class ServiceGenerator(BaseAgent):
    """L5 agent authoring ClusterIP Service manifest for internal pod routing."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ServiceGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        namespace = payload.get("namespace", "production")

        service_yaml = (
            "apiVersion: v1\n"
            "kind: Service\n"
            "metadata:\n"
            "  name: app-service\n"
            f"  namespace: {namespace}\n"
            "spec:\n"
            "  type: ClusterIP\n"
            "  selector:\n"
            "    app: microservice\n"
            "  ports:\n"
            "    - port: 80\n"
            "      targetPort: 8000\n"
            "      protocol: TCP\n"
        )
        return {"status": "COMPLETED", "service_yaml": service_yaml}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ServiceGenerator %s cleaned up.", self.agent_id)


class IngressGenerator(BaseAgent):
    """L5 agent authoring Kubernetes Ingress manifest with TLS termination and host rules."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("IngressGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        namespace = payload.get("namespace", "production")

        ingress_yaml = (
            "apiVersion: networking.k8s.io/v1\n"
            "kind: Ingress\n"
            "metadata:\n"
            "  name: app-ingress\n"
            f"  namespace: {namespace}\n"
            "  annotations:\n"
            "    kubernetes.io/ingress.class: nginx\n"
            "    cert-manager.io/cluster-issuer: letsencrypt-prod\n"
            "spec:\n"
            "  tls:\n"
            "    - hosts:\n"
            "        - api.example.com\n"
            "      secretName: api-tls-cert\n"
            "  rules:\n"
            "    - host: api.example.com\n"
            "      http:\n"
            "        paths:\n"
            "          - path: /\n"
            "            pathType: Prefix\n"
            "            backend:\n"
            "              service:\n"
            "                name: app-service\n"
            "                port:\n"
            "                  number: 80\n"
        )
        return {"status": "COMPLETED", "ingress_yaml": ingress_yaml}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("IngressGenerator %s cleaned up.", self.agent_id)


class ConfigMapGenerator(BaseAgent):
    """L5 agent authoring Kubernetes ConfigMap and Secret manifests."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ConfigMapGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        namespace = payload.get("namespace", "production")

        config_yaml = (
            "apiVersion: v1\n"
            "kind: ConfigMap\n"
            "metadata:\n"
            "  name: app-config\n"
            f"  namespace: {namespace}\n"
            "data:\n"
            "  ENVIRONMENT: \"production\"\n"
            "  LOG_LEVEL: \"info\"\n"
        )
        return {"status": "COMPLETED", "configmap_yaml": config_yaml}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ConfigMapGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 KubernetesManifestGenerator Agent
# ==============================================================================

class KubernetesManifestGenerator(BaseAgent):
    """L4 coordinator synthesizing complete Kubernetes infrastructure manifests."""

    def __init__(
        self,
        name: str = "KubernetesManifestGenerator",
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
            "kubernetes_manifest_generation",
            "deployment_synthesis",
            "service_synthesis",
            "ingress_synthesis",
            "configmap_synthesis",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "I6_KUBERNETES_MANIFEST_GENERATOR",
        )

        self.deploy_gen: Optional[DeploymentGenerator] = None
        self.svc_gen: Optional[ServiceGenerator] = None
        self.ing_gen: Optional[IngressGenerator] = None
        self.cfg_gen: Optional[ConfigMapGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_kubernetes_bundle", self.generate_kubernetes_bundle)

    def _spawn_subagents(self) -> None:
        """Spawn atomic Kubernetes subagents (Rule 1 & Rule 5)."""
        logger.info("KubernetesManifestGenerator %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.deploy_gen = self.spawn_subagent(
            DeploymentGenerator,
            name="DeploymentGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.svc_gen = self.spawn_subagent(
            ServiceGenerator,
            name="ServiceGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.ing_gen = self.spawn_subagent(
            IngressGenerator,
            name="IngressGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.cfg_gen = self.spawn_subagent(
            ConfigMapGenerator,
            name="ConfigMapGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("KubernetesManifestGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        bundle = self.generate_kubernetes_bundle(
            replicas=payload.get("replicas", 3),
            namespace=payload.get("namespace", "production"),
        )
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "k8s_bundle": bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        bundle = result.get("k8s_bundle")
        if not bundle or "deployment" not in bundle:
            raise KubernetesError("KubernetesManifestGenerator produced incomplete bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("KubernetesManifestGenerator %s cleanup complete.", self.agent_id)

    def generate_kubernetes_bundle(self, replicas: int = 3, namespace: str = "production") -> Dict[str, str]:
        """Synthesize all Kubernetes manifests into an integrated bundle."""
        p_env = {"payload": {"replicas": replicas, "namespace": namespace}}
        d = self.deploy_gen.process(p_env) if self.deploy_gen else {"deployment_yaml": ""}
        s = self.svc_gen.process(p_env) if self.svc_gen else {"service_yaml": ""}
        i = self.ing_gen.process(p_env) if self.ing_gen else {"ingress_yaml": ""}
        c = self.cfg_gen.process(p_env) if self.cfg_gen else {"configmap_yaml": ""}

        return {
            "deployment": d.get("deployment_yaml", ""),
            "service": s.get("service_yaml", ""),
            "ingress": i.get("ingress_yaml", ""),
            "configmap": c.get("configmap_yaml", ""),
        }
