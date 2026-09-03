"""SecretManager agent coordinating HashiCorp Vault, AWS Secrets Manager, and key rotation."""

from __future__ import annotations

import logging
import secrets
from typing import Any, Dict, List, Optional

from agents.infrastructure.exceptions import SecretError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Infrastructure.SecretManager")


# ==============================================================================
# L5 Atomic Secret Subagents
# ==============================================================================

class VaultConfigurer(BaseAgent):
    """L5 agent authoring HashiCorp Vault AppRole and KV secret engine initialization scripts."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("VaultConfigurer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        vault_script = (
            "#!/bin/sh\n"
            "# Enable KV v2 secret engine\n"
            "vault secrets enable -version=2 kv\n"
            "vault kv put kv/production/database url='postgresql+asyncpg://...' password='...'\n\n"
            "# Enable AppRole authentication for containerized microservice\n"
            "vault auth enable approle\n"
            "vault write auth/approle/role/microservice \\\n"
            "    secret_id_ttl=10m \\\n"
            "    token_ttl=1h \\\n"
            "    policies=\"microservice-read\"\n"
        )
        return {"status": "COMPLETED", "vault_script": vault_script}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("VaultConfigurer %s cleaned up.", self.agent_id)


class AwsSecretsManager(BaseAgent):
    """L5 agent synthesizing AWS Secrets Manager retrieval and automated rotation hooks."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("AwsSecretsManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        aws_code = (
            "import boto3\n"
            "import json\n\n"
            "def get_secret(secret_name: str, region_name: str = 'us-east-1'):\n"
            "    client = boto3.client('secretsmanager', region_name=region_name)\n"
            "    resp = client.get_secret_value(SecretId=secret_name)\n"
            "    return json.loads(resp['SecretString'])\n"
        )
        return {"status": "COMPLETED", "aws_secrets_code": aws_code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("AwsSecretsManager %s cleaned up.", self.agent_id)


class EncryptionKeyGenerator(BaseAgent):
    """L5 agent generating cryptographically secure 256-bit AES symmetric keys and salts."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("EncryptionKeyGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        raw_key = secrets.token_hex(32)
        return {
            "status": "COMPLETED",
            "key_length_bits": 256,
            "sample_key_hex": raw_key,
            "algorithm": "AES-256-GCM",
            "passed": True,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("EncryptionKeyGenerator %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 SecretManager Agent
# ==============================================================================

class SecretManager(BaseAgent):
    """L4 coordinator managing Vault, AWS Secrets Manager, and cryptographic key lifecycles."""

    def __init__(
        self,
        name: str = "SecretManager",
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
            "secret_management",
            "vault_configuration",
            "aws_secrets_manager",
            "encryption_key_generation",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "I12_SECRET_MANAGER",
        )

        self.vault_cfg: Optional[VaultConfigurer] = None
        self.aws_sm: Optional[AwsSecretsManager] = None
        self.key_gen: Optional[EncryptionKeyGenerator] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("generate_secret_management_bundle", self.generate_secret_management_bundle)

    def _spawn_subagents(self) -> None:
        """Spawn atomic secret subagents (Rule 1 & Rule 5)."""
        logger.info("SecretManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.vault_cfg = self.spawn_subagent(
            VaultConfigurer,
            name="VaultConfigurer",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.aws_sm = self.spawn_subagent(
            AwsSecretsManager,
            name="AwsSecretsManager",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.key_gen = self.spawn_subagent(
            EncryptionKeyGenerator,
            name="EncryptionKeyGenerator",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SecretManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        bundle = self.generate_secret_management_bundle()
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "secret_bundle": bundle,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        bundle = result.get("secret_bundle")
        if not bundle or "vault_setup" not in bundle:
            raise SecretError("SecretManager produced incomplete bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("SecretManager %s cleanup complete.", self.agent_id)

    def generate_secret_management_bundle(self) -> Dict[str, Any]:
        """Synthesize HashiCorp Vault script, AWS Secrets Manager module, and AES keys."""
        v = self.vault_cfg.process({}) if self.vault_cfg else {"vault_script": ""}
        a = self.aws_sm.process({}) if self.aws_sm else {"aws_secrets_code": ""}
        k = self.key_gen.process({}) if self.key_gen else {"key_length_bits": 256}

        return {
            "vault_setup": v.get("vault_script", ""),
            "aws_secrets_manager": a.get("aws_secrets_code", ""),
            "encryption_meta": k,
            "passed": True,
        }
