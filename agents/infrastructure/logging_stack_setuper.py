"""LoggingStackSetuper agent configuring Elasticsearch, Logstash pipelines, and Kibana visualizations."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.infrastructure.exceptions import LoggingError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Infrastructure.LoggingStackSetuper")


# ==============================================================================
# L5 Atomic Logging Subagents
# ==============================================================================

class ElasticsearchConfigurer(BaseAgent):
    """L5 agent authoring Elasticsearch index templates and lifecycle retention policies."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ElasticsearchConfigurer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        ilm_policy = (
            "{\n"
            "  \"policy\": {\n"
            "    \"phases\": {\n"
            "      \"hot\": { \"min_age\": \"0ms\", \"actions\": { \"rollover\": { \"max_size\": \"50gb\", \"max_age\": \"7d\" } } },\n"
            "      \"delete\": { \"min_age\": \"30d\", \"actions\": { \"delete\": {} } }\n"
            "    }\n"
            "  }\n"
            "}\n"
        )
        return {"status": "COMPLETED", "ilm_policy_json": ilm_policy}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ElasticsearchConfigurer %s cleaned up.", self.agent_id)


class LogstashConfigurer(BaseAgent):
    """L5 agent authoring logstash.conf pipeline: Beats input, JSON filter, and Elasticsearch output."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LogstashConfigurer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        logstash_conf = (
            "input {\n"
            "  beats { port => 5044 }\n"
            "  tcp { port => 5000 codec => json }\n"
            "}\n\n"
            "filter {\n"
            "  mutate {\n"
            "    add_field => { \"application\" => \"microservice\" }\n"
            "  }\n"
            "}\n\n"
            "output {\n"
            "  elasticsearch {\n"
            "    hosts => [\"http://elasticsearch:9200\"]\n"
            "    index => \"microservice-logs-%{+YYYY.MM.dd}\"\n"
            "  }\n"
            "}\n"
        )
        return {"status": "COMPLETED", "logstash_conf": logstash_conf}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("LogstashConfigurer %s cleaned up.", self.agent_id)


class KibanaConfigurer(BaseAgent):
    """L5 agent authoring Kibana default index pattern and log stream discovery views."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("KibanaConfigurer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        kibana_setup = (
            "POST api/saved_objects/index-pattern/microservice-logs-*\n"
            "{\n"
            "  \"attributes\": {\n"
            "    \"title\": \"microservice-logs-*\",\n"
            "    \"timeFieldName\": \"@timestamp\"\n"
            "  }\n"
            "}\n"
        )
        return {"status": "COMPLETED", "kibana_setup_script": kibana_setup}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("KibanaConfigurer %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 LoggingStackSetuper Agent
# ==============================================================================

class LoggingStackSetuper(BaseAgent):
    """L4 coordinator synthesizing ELK stack ingestion, filtering, and indexing configurations."""

    def __init__(
        self,
        name: str = "LoggingStackSetuper",
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
            "logging_stack_setup",
            "elasticsearch_configuration",
            "logstash_pipelines",
            "kibana_dashboards",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "I11_LOGGING_STACK_SETUPER",
        )

        self.es_cfg: Optional[ElasticsearchConfigurer] = None
        self.ls_cfg: Optional[LogstashConfigurer] = None
        self.kb_cfg: Optional[KibanaConfigurer] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_logging_bundle", self.generate_logging_bundle)

    def _spawn_subagents(self) -> None:
        """Spawn atomic logging subagents (Rule 1 & Rule 5)."""
        logger.info("LoggingStackSetuper %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.es_cfg = self.spawn_subagent(
            ElasticsearchConfigurer,
            name="ElasticsearchConfigurer",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.ls_cfg = self.spawn_subagent(
            LogstashConfigurer,
            name="LogstashConfigurer",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.kb_cfg = self.spawn_subagent(
            KibanaConfigurer,
            name="KibanaConfigurer",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LoggingStackSetuper %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        bundle = self.generate_logging_bundle()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "logging_bundle": bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        bundle = result.get("logging_bundle")
        if not bundle or "logstash" not in bundle:
            raise LoggingError("LoggingStackSetuper produced incomplete bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("LoggingStackSetuper %s cleanup complete.", self.agent_id)

    def generate_logging_bundle(self) -> Dict[str, str]:
        """Synthesize Elasticsearch ILM, Logstash, and Kibana configuration scripts."""
        e = self.es_cfg.process({}) if self.es_cfg else {"ilm_policy_json": ""}
        l = self.ls_cfg.process({}) if self.ls_cfg else {"logstash_conf": ""}
        k = self.kb_cfg.process({}) if self.kb_cfg else {"kibana_setup_script": ""}

        return {
            "elasticsearch_ilm": e.get("ilm_policy_json", ""),
            "logstash": l.get("logstash_conf", ""),
            "kibana_setup": k.get("kibana_setup_script", ""),
            "passed": True,
        }
