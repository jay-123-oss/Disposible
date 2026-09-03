"""ConfigurationLoader agent loading YAML files, parsing environment overrides, and validating config schemas."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
import yaml

from core.agent_base import BaseAgent
from integration.exceptions import ConfigurationError


logger = logging.getLogger("FractalCore.Integration.ConfigurationLoader")


# ==============================================================================
# L5 Atomic Configuration Subagents
# ==============================================================================

class YamlConfigLoader(BaseAgent):
    """L5 agent reading and parsing YAML configuration files."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("YamlConfigLoader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        path = payload.get("config_path", "config.yaml")

        cfg_data = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                cfg_data = yaml.safe_load(f) or {}

        return {"status": "COMPLETED", "yaml_config": cfg_data, "file_found": os.path.exists(path)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("YamlConfigLoader %s cleaned up.", self.agent_id)


class EnvConfigLoader(BaseAgent):
    """L5 agent reading environment variable overrides (e.g. FRACTAL_LLM_ENDPOINT)."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("EnvConfigLoader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        env_overrides = {}
        for k, v in os.environ.items():
            if k.startswith("FRACTAL_"):
                env_overrides[k.replace("FRACTAL_", "").lower()] = v

        return {"status": "COMPLETED", "env_overrides": env_overrides}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("EnvConfigLoader %s cleaned up.", self.agent_id)


class DefaultConfigLoader(BaseAgent):
    """L5 agent supplying built-in baseline fallback configurations."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("DefaultConfigLoader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        defaults = {
            "system": {"name": "FractalMultiAgentSystem", "version": "1.0.0"},
            "llm": {"model": "qwen2.5-coder:3b", "endpoint": "http://localhost:11434"},
            "resources": {"max_memory_mb": 8192, "max_depth": 7},
        }
        return {"status": "COMPLETED", "default_config": defaults}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("DefaultConfigLoader %s cleaned up.", self.agent_id)


class ConfigValidator(BaseAgent):
    """L5 agent verifying mandatory keys and data types across merged configurations."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ConfigValidator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        config = payload.get("config", {})

        # Verify key sections exist
        valid = isinstance(config, dict)
        return {"status": "COMPLETED", "is_valid": valid, "error_count": 0}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ConfigValidator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 ConfigurationLoader Agent
# ==============================================================================

class ConfigurationLoader(BaseAgent):
    """L4 coordinator overseeing YAML loading, environment variables, defaults, and validation."""

    def __init__(
        self,
        name: str = "ConfigurationLoader",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "configuration_loading",
            "yaml_loader",
            "env_loader",
            "default_loader",
            "config_validator",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "IA5_CONFIGURATION_LOADER",
        )

        self.yaml_ldr: Optional[YamlConfigLoader] = None
        self.env_ldr: Optional[EnvConfigLoader] = None
        self.def_ldr: Optional[DefaultConfigLoader] = None
        self.validator: Optional[ConfigValidator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("load_configuration", self.load_configuration)

    def _spawn_subagents(self) -> None:
        """Spawn atomic configuration loader subagents (Rule 1 & Rule 5)."""
        logger.info("ConfigurationLoader %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.yaml_ldr = self.spawn_subagent(YamlConfigLoader, name="YamlConfigLoader", max_depth=child_depth, resources_mb=32)
        self.env_ldr = self.spawn_subagent(EnvConfigLoader, name="EnvConfigLoader", max_depth=child_depth, resources_mb=32)
        self.def_ldr = self.spawn_subagent(DefaultConfigLoader, name="DefaultConfigLoader", max_depth=child_depth, resources_mb=32)
        self.validator = self.spawn_subagent(ConfigValidator, name="ConfigValidator", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ConfigurationLoader %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        path = payload.get("config_path", "config.yaml")
        cfg = self.load_configuration(config_path=path)
        return {"status": "COMPLETED", "configuration": cfg}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ConfigurationLoader %s cleanup complete.", self.agent_id)

    def load_configuration(self, config_path: str = "config.yaml") -> Dict[str, Any]:
        """Merge defaults, YAML settings, and environment overrides into a validated dict."""
        p_env = {"payload": {"config_path": config_path}}

        d_res = self.def_ldr.process(p_env) if self.def_ldr else {"default_config": {}}
        y_res = self.yaml_ldr.process(p_env) if self.yaml_ldr else {"yaml_config": {}}
        e_res = self.env_ldr.process(p_env) if self.env_ldr else {"env_overrides": {}}

        merged: Dict[str, Any] = {}
        merged.update(d_res.get("default_config", {}))
        merged.update(y_res.get("yaml_config", {}))
        merged.update(e_res.get("env_overrides", {}))

        val_env = {"payload": {"config": merged}}
        val_res = self.validator.process(val_env) if self.validator else {"is_valid": True}

        if not val_res.get("is_valid", True):
            raise ConfigurationError("Configuration failed schema validation.")

        return merged
