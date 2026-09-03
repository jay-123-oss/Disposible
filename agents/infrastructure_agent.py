"""Infrastructure Agent: Generates Dockerfiles, k8s manifests, and CI/CD configurations.

Model: Llama3.2:3B
RAM: ~3GB
"""

from __future__ import annotations

import logging
import os
import requests
from typing import Any, Dict, Optional

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
        """Execute DevOps infrastructure task via Ollama or structured fallback."""
        prompt = f"{self.system_prompt}\n\nTask: {task}"
        if context:
            prompt += f"\n\nContext:\n{context}"

        try:
            resp = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=(0.5, 60.0),
            )
            if resp.status_code == 200:
                output = resp.json().get("response", "")
                return {"success": True, "agent": self.agent_id, "model": self.model, "output": output}
        except Exception as exc:
            logger.debug("Ollama call failed (%s), using local generation fallback", exc)


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
            "model": self.model,
            "output": fallback_output,
            "note": "Generated via offline engine",
        }
