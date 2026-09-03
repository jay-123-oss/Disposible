"""Infrastructure Agent: Generates Dockerfiles, k8s manifests, and CI/CD configurations.

Model: Llama3.2:3B
RAM: ~3GB
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from llm import generate_text, resolve_model

logger = logging.getLogger("InfrastructureAgent")


class InfrastructureAgent:
    """Specialized DevOps and deployment agent using Llama3.2:3B."""

    def __init__(
        self,
        ollama_url: Optional[str] = None,
        model: str = "llama3.2:3b",
    ) -> None:
        self.name = "Infrastructure Agent"
        self.agent_id = "infrastructure"
        self.model = model
        self.ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.system_prompt = "You are a DevOps expert. Generate Dockerfiles, k8s manifests, and CI/CD configs."

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute DevOps infrastructure task via the configured LLM provider or the structured fallback."""
        user_prompt = task
        if context:
            user_prompt += f"\n\nContext:\n{context}"

        # Effective model after LLM_MODEL override resolution — reported in results.
        model_used = resolve_model(self.model)
        # Generate via the configured LLM provider (hosted API key or local Ollama).
        output = generate_text(
            system=self.system_prompt,
            prompt=user_prompt,
            model=self.model,
            max_tokens=1500,
        )
        if output:
            return {"success": True, "agent": self.agent_id, "model": model_used, "output": output}


        fallback_output = (
            f"```dockerfile\n"
            f"# Infrastructure configuration for: {task}\n"
            f"FROM python:3.10-slim\n"
            f"WORKDIR /app\n"
            f"COPY . /app\n"
            f"RUN pip install --no-cache-dir -r requirements.txt\n"
            f"EXPOSE 8000\n"
            f"CMD [\"python\", \"server.py\"]\n"
            f"```"
        )
        return {
            "success": True,
            "agent": self.agent_id,
            "model": model_used,
            "output": fallback_output,
            "note": "Generated via offline engine",
        }
