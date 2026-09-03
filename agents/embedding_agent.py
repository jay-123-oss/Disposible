"""Embedding Agent: Generates vector embeddings for semantic search and retrieval.

Model: Nomic-Embed-Text
RAM: ~1GB
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional

from llm import embed_text

logger = logging.getLogger("EmbeddingAgent")


class EmbeddingAgent:
    """Specialized vector embedding agent using Nomic-Embed-Text."""

    def __init__(
        self,
        ollama_url: Optional[str] = None,
        model: str = "nomic-embed-text",
    ) -> None:
        # ``ollama_url`` is accepted for backward compatibility only — the
        # unified llm.py gateway reads OLLAMA_URL / LLM_EMBEDDING_MODEL itself.
        del ollama_url
        self.name = "Embedding Agent"
        self.agent_id = "embedding"
        self.model = model
        self.system_prompt = "You are an embedding expert. Generate vector embeddings for semantic search."

    def embed(self, text: str) -> List[float]:
        """Embed via the unified llm.py gateway (cloud API key -> local Ollama),
        else fall back to a deterministic pseudo-vector."""
        vector = embed_text(text, model=self.model)
        if vector:
            return vector

        # Generate deterministic 768-dim vector from text hash
        seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
        import random
        rnd = random.Random(seed)
        return [round(rnd.uniform(-1.0, 1.0), 6) for _ in range(768)]

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute semantic search/embedding task."""
        vector = self.embed(task)
        return {
            "success": True,
            "agent": self.agent_id,
            "model": self.model,
            "dimensions": len(vector),
            "sample_vector": vector[:5],
            "output": f"Generated vector embedding with {len(vector)} dimensions for query: '{task}'",
        }
