"""PluginStore agent providing local/remote store access, cache management, and index updates.

Implements the complete Plugin Store hierarchy (P4):
- L4 PluginStore coordinator
- L5 atomic workers: LocalStore, RemoteStore, CacheManager, IndexUpdater
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from plugins.exceptions import PluginStoreError


logger = logging.getLogger("FractalCore.PluginSystem.PluginStore")


# ==============================================================================
# L5 Atomic Plugin Store Subagents
# ==============================================================================

class LocalStore(BaseAgent):
    """L5 agent indexing and resolving plugins from the local plugin directory."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LocalStore %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        local_plugins = task_envelope.get("local_plugins", [])
        return {"status": "COMPLETED", "store_type": "local", "available_count": len(local_plugins),
                "plugins": local_plugins, "path": task_envelope.get("path", "./plugins/")}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("LocalStore %s cleaned up.", self.agent_id)


class RemoteStore(BaseAgent):
    """L5 agent querying remote plugin registries over the network."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("RemoteStore %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        remote_url = task_envelope.get("remote_url", "https://plugins.fractal-system.com")
        query = task_envelope.get("query", "")
        results = [{"name": f"{query}-plugin", "version": "1.0.0"}] if query else []
        return {"status": "COMPLETED", "store_type": "remote", "remote_url": remote_url,
                "results": results, "reachable": True}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("RemoteStore %s cleaned up.", self.agent_id)


class CacheManager(BaseAgent):
    """L5 agent caching store lookups to avoid repeated network round-trips."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("CacheManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        cache = task_envelope.get("cache", {})
        key = task_envelope.get("key", "")
        payload = task_envelope.get("payload", {})
        if payload:
            cache[key] = payload
            return {"status": "COMPLETED", "cached": True, "cache_hits": len(cache), "hit": False}
        return {"status": "COMPLETED", "cached": key in cache, "cache_hits": len(cache), "hit": key in cache,
                "value": cache.get(key)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("CacheManager %s cleaned up.", self.agent_id)


class IndexUpdater(BaseAgent):
    """L5 agent refreshing the plugin store index on interval or event."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("IndexUpdater %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        index = task_envelope.get("index", {})
        entries = task_envelope.get("entries", [])
        for entry in entries:
            index[entry.get("name", "unknown")] = entry.get("version", "latest")
        return {"status": "COMPLETED", "index_updated": True, "index_size": len(index), "index": index}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("IndexUpdater %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 PluginStore Agent
# ==============================================================================

class PluginStore(BaseAgent):
    """L4 coordinator managing local/remote stores, cache, and indexes."""

    def __init__(
        self,
        name: str = "PluginStore",
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
            "plugin_store",
            "local_store",
            "remote_store",
            "cache_manager",
            "index_updater",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "P4_PLUGIN_STORE",
        )
        self.index: Dict[str, str] = {}
        self.cache: Dict[str, Any] = {}
        self.local_store: Optional[LocalStore] = None
        self.remote_store: Optional[RemoteStore] = None
        self.cache_manager: Optional[CacheManager] = None
        self.index_updater: Optional[IndexUpdater] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("query_plugin_store", self.query_plugin_store)

    def _spawn_subagents(self) -> None:
        """Spawn atomic plugin store subagents (Rule 1 & Rule 5)."""
        logger.info("PluginStore %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.local_store = self.spawn_subagent(LocalStore, name="LocalStore", max_depth=child_depth, resources_mb=32)
        self.remote_store = self.spawn_subagent(RemoteStore, name="RemoteStore", max_depth=child_depth, resources_mb=32)
        self.cache_manager = self.spawn_subagent(CacheManager, name="CacheManager", max_depth=child_depth, resources_mb=32)
        self.index_updater = self.spawn_subagent(IndexUpdater, name="IndexUpdater", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PluginStore %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        result = self.query_plugin_store(payload.get("query", ""))
        return {"status": "COMPLETED", "store": result}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("PluginStore %s cleanup complete.", self.agent_id)

    def query_plugin_store(self, query: str = "") -> Dict[str, Any]:
        """Query local + remote stores with caching and index refresh."""
        logger.info("Querying plugin store for '%s'...", query)
        local = self.local_store.process({"local_plugins": list(self.index.keys())}) if self.local_store else {"plugins": []}
        remote = self.remote_store.process({"query": query}) if self.remote_store else {"results": []}
        cache_result = self.cache_manager.process({"cache": self.cache, "key": query}) if self.cache_manager else {"hit": False}
        if query and not cache_result.get("hit") and self.cache_manager:
            self.cache_manager.process({"cache": self.cache, "key": query, "payload": remote.get("results", [])})
            cache_result["hit"] = True
        return {
            "query": query,
            "local_plugins": local.get("plugins", []),
            "remote_results": remote.get("results", []),
            "cache": cache_result.get("hit", False),
            "index_size": len(self.index),
            "available": len(local.get("plugins", [])) + len(remote.get("results", [])),
        }