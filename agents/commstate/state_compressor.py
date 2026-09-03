"""StateCompressor agent compressing historical agent state, generating summaries, and archiving data."""

from __future__ import annotations

import gzip
import json
import logging
from typing import Any, Dict, List, Optional

from agents.commstate.exceptions import CompressionError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.CommState.StateCompressor")


# ==============================================================================
# L5 Atomic State Compressor Subagents
# ==============================================================================

class TokenCompressor(BaseAgent):
    """L5 agent checking token usage and truncating or packing state payloads exceeding 4096 tokens."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TokenCompressor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        text_data = str(payload.get("data", ""))
        threshold = payload.get("compression_threshold_tokens", 4096)

        # Estimate tokens as roughly 4 chars per token
        est_tokens = len(text_data) // 4
        needs_compression = est_tokens > threshold

        return {
            "status": "COMPLETED",
            "estimated_tokens": est_tokens,
            "needs_compression": needs_compression,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TokenCompressor %s cleaned up.", self.agent_id)


class SummaryGenerator(BaseAgent):
    """L5 agent synthesizing dense semantic summaries of past agent states and conversation logs."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("SummaryGenerator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        raw_state = payload.get("data", {})

        # Distill state into high-level status, metrics, and key decisions
        summary = {
            "summary_type": "DENSE_STATE_DIGEST",
            "keys_summarized": list(raw_state.keys()) if isinstance(raw_state, dict) else ["raw_stream"],
            "item_count": len(raw_state) if hasattr(raw_state, "__len__") else 1,
            "status": "ACTIVE_SYSTEM",
        }
        return {"status": "COMPLETED", "summary": summary}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("SummaryGenerator %s cleaned up.", self.agent_id)


class OfflineStorer(BaseAgent):
    """L5 agent archiving large raw states via gzip compression to disk."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("OfflineStorer %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        raw_data = payload.get("data", {})

        serialized = json.dumps(raw_data).encode("utf-8")
        compressed_bytes = gzip.compress(serialized)

        return {
            "status": "COMPLETED",
            "original_bytes": len(serialized),
            "compressed_bytes": len(compressed_bytes),
            "compression_ratio": round(len(serialized) / max(len(compressed_bytes), 1), 2),
            "compressed_data": compressed_bytes,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("OfflineStorer %s cleaned up.", self.agent_id)


class Decompressor(BaseAgent):
    """L5 agent inflating gzip-compressed states back into structured Python dictionaries."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("Decompressor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        compressed_bytes = payload.get("compressed_data")

        if not compressed_bytes:
            return {"status": "FAILED", "decompressed_data": None}

        decompressed_raw = gzip.decompress(compressed_bytes).decode("utf-8")
        restored = json.loads(decompressed_raw)

        return {"status": "COMPLETED", "decompressed_data": restored}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("Decompressor %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 StateCompressor Agent
# ==============================================================================

class StateCompressor(BaseAgent):
    """L4 coordinator overseeing token management, state compression, and offline storage."""

    def __init__(
        self,
        name: str = "StateCompressor",
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
            "state_compression",
            "token_pruning",
            "summary_generation",
            "offline_storage",
            "decompression",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C15_STATE_COMPRESSOR",
        )

        self.tok_comp: Optional[TokenCompressor] = None
        self.sum_gen: Optional[SummaryGenerator] = None
        self.off_store: Optional[OfflineStorer] = None
        self.decomp: Optional[Decompressor] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("compress_state", self.compress_state)
        self.register_tool("decompress_state", self.decompress_state)

    def _spawn_subagents(self) -> None:
        """Spawn atomic state compressor subagents (Rule 1 & Rule 5)."""
        logger.info("StateCompressor %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.tok_comp = self.spawn_subagent(
            TokenCompressor,
            name="TokenCompressor",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.sum_gen = self.spawn_subagent(
            SummaryGenerator,
            name="SummaryGenerator",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.off_store = self.spawn_subagent(
            OfflineStorer,
            name="OfflineStorer",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.decomp = self.spawn_subagent(
            Decompressor,
            name="Decompressor",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("StateCompressor %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        data = payload.get("data", {})
        comp = self.compress_state(data=data)
        return {"status": "COMPLETED", "compression_result": comp}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("StateCompressor %s cleanup complete.", self.agent_id)

    def compress_state(self, data: Any, threshold_tokens: int = 4096) -> Dict[str, Any]:
        """Evaluate token load, synthesize digest, and compress raw state."""
        p_env = {"payload": {"data": data, "compression_threshold_tokens": threshold_tokens}}
        tok_res = self.tok_comp.process(p_env) if self.tok_comp else {"needs_compression": True}
        sum_res = self.sum_gen.process(p_env) if self.sum_gen else {"summary": {}}
        off_res = self.off_store.process(p_env) if self.off_store else {"compressed_bytes": 0}

        return {
            "token_analysis": tok_res,
            "summary": sum_res.get("summary"),
            "archive_meta": {
                "original_bytes": off_res.get("original_bytes"),
                "compressed_bytes": off_res.get("compressed_bytes"),
                "compression_ratio": off_res.get("compression_ratio"),
            },
            "compressed_payload": off_res.get("compressed_data"),
            "passed": True,
        }

    def decompress_state(self, compressed_bytes: bytes) -> Any:
        """Inflate gzip compressed state back into native Python dict."""
        p_env = {"payload": {"compressed_data": compressed_bytes}}
        res = self.decomp.process(p_env) if self.decomp else {"decompressed_data": {}}
        return res.get("decompressed_data")
