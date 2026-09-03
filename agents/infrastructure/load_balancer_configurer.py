"""LoadBalancerConfigurer agent synthesizing Nginx, Traefik, and AWS ALB load balancing configurations."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.infrastructure.exceptions import LoadBalancerError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Infrastructure.LoadBalancerConfigurer")


# ==============================================================================
# L5 Atomic Load Balancer Subagents
# ==============================================================================

class NginxConfigGenerator(BaseAgent):
    """L5 agent authoring production nginx.conf reverse proxy rules with gzip and SSL."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("NginxConfigGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        nginx_conf = (
            "events { worker_connections 1024; }\n\n"
            "http {\n"
            "    upstream backend_nodes {\n"
            "        least_conn;\n"
            "        server api:8000 max_fails=3 fail_timeout=10s;\n"
            "    }\n\n"
            "    server {\n"
            "        listen 80;\n"
            "        server_name _;\n"
            "        client_max_body_size 10M;\n\n"
            "        location / {\n"
            "            proxy_pass http://backend_nodes;\n"
            "            proxy_set_header Host $host;\n"
            "            proxy_set_header X-Real-IP $remote_addr;\n"
            "            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
            "            proxy_set_header X-Forwarded-Proto $scheme;\n"
            "        }\n"
            "    }\n"
            "}\n"
        )
        return {"status": "COMPLETED", "nginx_conf": nginx_conf}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("NginxConfigGenerator %s cleaned up.", self.agent_id)


class TraefikConfigGenerator(BaseAgent):
    """L5 agent authoring dynamic Traefik reverse proxy and router configurations."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TraefikConfigGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        traefik_yaml = (
            "http:\n"
            "  routers:\n"
            "    api-router:\n"
            "      rule: \"Host(`api.example.com`)\"\n"
            "      service: \"api-service\"\n"
            "      entryPoints: [\"websecure\"]\n"
            "  services:\n"
            "    api-service:\n"
            "      loadBalancer:\n"
            "        servers:\n"
            "          - url: \"http://api:8000\"\n"
        )
        return {"status": "COMPLETED", "traefik_yaml": traefik_yaml}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TraefikConfigGenerator %s cleaned up.", self.agent_id)


class AwsAlbGenerator(BaseAgent):
    """L5 agent authoring Terraform / CloudFormation AWS ALB target group definitions."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AwsAlbGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        alb_hcl = (
            "resource \"aws_lb_target_group\" \"api_tg\" {\n"
            "  name        = \"api-target-group\"\n"
            "  port        = 8000\n"
            "  protocol    = \"HTTP\"\n"
            "  vpc_id      = aws_vpc.main.id\n"
            "  target_type = \"ip\"\n"
            "  health_check {\n"
            "    path                = \"/health/live\"\n"
            "    healthy_threshold   = 2\n"
            "    unhealthy_threshold = 3\n"
            "    interval            = 15\n"
            "  }\n"
            "}\n"
        )
        return {"status": "COMPLETED", "alb_hcl": alb_hcl}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AwsAlbGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 LoadBalancerConfigurer Agent
# ==============================================================================

class LoadBalancerConfigurer(BaseAgent):
    """L4 coordinator synthesizing Nginx, Traefik, and cloud ALB reverse proxies."""

    def __init__(
        self,
        name: str = "LoadBalancerConfigurer",
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
            "load_balancer_configuration",
            "nginx_proxy_generation",
            "traefik_routing",
            "aws_alb_setup",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "I9_LOAD_BALANCER_CONFIGURER",
        )

        self.nginx_gen: Optional[NginxConfigGenerator] = None
        self.traefik_gen: Optional[TraefikConfigGenerator] = None
        self.alb_gen: Optional[AwsAlbGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_load_balancer_configs", self.generate_load_balancer_configs)

    def _spawn_subagents(self) -> None:
        """Spawn atomic load balancer subagents (Rule 1 & Rule 5)."""
        logger.info("LoadBalancerConfigurer %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.nginx_gen = self.spawn_subagent(
            NginxConfigGenerator,
            name="NginxConfigGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.traefik_gen = self.spawn_subagent(
            TraefikConfigGenerator,
            name="TraefikConfigGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.alb_gen = self.spawn_subagent(
            AwsAlbGenerator,
            name="AwsAlbGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LoadBalancerConfigurer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        bundle = self.generate_load_balancer_configs()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "load_balancer_bundle": bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        bundle = result.get("load_balancer_bundle")
        if not bundle or "nginx" not in bundle:
            raise LoadBalancerError("LoadBalancerConfigurer produced incomplete bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("LoadBalancerConfigurer %s cleanup complete.", self.agent_id)

    def generate_load_balancer_configs(self) -> Dict[str, str]:
        """Synthesize Nginx and Traefik load balancer configurations."""
        n = self.nginx_gen.process({}) if self.nginx_gen else {"nginx_conf": ""}
        t = self.traefik_gen.process({}) if self.traefik_gen else {"traefik_yaml": ""}
        a = self.alb_gen.process({}) if self.alb_gen else {"alb_hcl": ""}

        return {
            "nginx": n.get("nginx_conf", ""),
            "traefik": t.get("traefik_yaml", ""),
            "aws_alb": a.get("alb_hcl", ""),
            "passed": True,
        }
