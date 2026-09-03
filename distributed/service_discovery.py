"""ServiceDiscovery agent managing registration, discovery, caching, and TTL health for microservices.

Implements the complete Service Discovery hierarchy (D5):
- L4 ServiceDiscovery coordinator
- L5 atomic workers: ServiceRegistrar, ServiceFinder, ServiceHealthChecker, ServiceCache
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from core.agent_base import BaseAgent
from distributed.exceptions import ServiceDiscoveryError

logger = logging.getLogger("FractalCore.Distributed.ServiceDiscovery")


# ==============================================================================
# L5 Atomic Service Discovery Subagents
# ==============================================================================

class ServiceRegistrar(BaseAgent):
    """L5 agent registering service instances and metadata into the catalog."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ServiceRegistrar %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        service_name = task_envelope.get("service_name", "")
        endpoint = task_envelope.get("endpoint", "")
        ttl = task_envelope.get("ttl", 15)
        record = {
            "service_name": service_name,
            "endpoint": endpoint,
            "ttl": ttl,
            "registered_at": time.time(),
            "expires_at": time.time() + ttl,
            "metadata": task_envelope.get("metadata", {}),
        }
        return {"status": "COMPLETED", "service_name": service_name, "record": record}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ServiceRegistrar %s cleaned up.", self.agent_id)


class ServiceFinder(BaseAgent):
    """L5 agent querying available healthy instances of a service."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ServiceFinder %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        service_name = task_envelope.get("service_name", "")
        catalog = task_envelope.get("catalog", {})
        now = time.time()
        instances = [
            rec for rec in catalog.get(service_name, [])
            if rec.get("expires_at", 0) > now
        ]
        return {
            "status": "COMPLETED",
            "service_name": service_name,
            "instances": instances,
            "instance_count": len(instances),
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ServiceFinder %s cleaned up.", self.agent_id)


class ServiceHealthChecker(BaseAgent):
    """L5 agent purging expired service registrations based on TTL expiration."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ServiceHealthChecker %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        catalog = task_envelope.get("catalog", {})
        now = time.time()
        active_count = 0
        expired_count = 0
        new_catalog: Dict[str, List[Dict[str, Any]]] = {}

        for svc, records in catalog.items():
            valid = [r for r in records if r.get("expires_at", 0) > now]
            new_catalog[svc] = valid
            active_count += len(valid)
            expired_count += (len(records) - len(valid))

        return {
            "status": "COMPLETED",
            "catalog": new_catalog,
            "active_count": active_count,
            "expired_count": expired_count,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ServiceHealthChecker %s cleaned up.", self.agent_id)


class ServiceCache(BaseAgent):
    """L5 agent caching service endpoints locally to minimize lookup overhead."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ServiceCache %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        cache = task_envelope.get("cache", {})
        key = task_envelope.get("key", "")
        val = task_envelope.get("value")
        if val is not None:
            cache[key] = val
        return {"status": "COMPLETED", "value": cache.get(key), "cache_size": len(cache)}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ServiceCache %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 ServiceDiscovery Agent
# ==============================================================================

class ServiceDiscovery(BaseAgent):
    """L4 coordinator providing service registry, TTL heartbeats, lookup, and client-side caching."""

    def __init__(
        self,
        name: str = "ServiceDiscovery",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 64,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
        ttl_seconds: int = 15,
    ) -> None:
        default_caps = capabilities or [
            "service_discovery",
            "service_registrar",
            "service_finder",
            "service_health_checker",
            "service_cache",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "D5_SERVICE_DISCOVERY",
        )
        self.ttl_seconds = ttl_seconds
        self.catalog: Dict[str, List[Dict[str, Any]]] = {}
        self.local_cache: Dict[str, Any] = {}

        self.registrar: Optional[ServiceRegistrar] = None
        self.finder: Optional[ServiceFinder] = None
        self.health_checker: Optional[ServiceHealthChecker] = None
        self.cache: Optional[ServiceCache] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("register_service", self.register_service)
        self.register_tool("discover_service", self.discover_service)
        self.register_tool("prune_expired", self.prune_expired)

    def _spawn_subagents(self) -> None:
        """Spawn atomic service discovery subagents (Rule 1 & Rule 5)."""
        logger.info("ServiceDiscovery %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.registrar = self.spawn_subagent(ServiceRegistrar, name="ServiceRegistrar", max_depth=child_depth, resources_mb=32)
        self.finder = self.spawn_subagent(ServiceFinder, name="ServiceFinder", max_depth=child_depth, resources_mb=32)
        self.health_checker = self.spawn_subagent(ServiceHealthChecker, name="ServiceHealthChecker", max_depth=child_depth, resources_mb=32)
        self.cache = self.spawn_subagent(ServiceCache, name="ServiceCache", max_depth=child_depth, resources_mb=32)

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("ServiceDiscovery %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        action = task_envelope.get("action", "discover")
        if action == "register":
            return self.register_service(
                task_envelope.get("service_name", ""),
                task_envelope.get("endpoint", ""),
                task_envelope.get("ttl", self.ttl_seconds),
            )
        return {"status": "COMPLETED", "instances": self.discover_service(task_envelope.get("service_name", ""))}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("ServiceDiscovery %s cleaned up.", self.agent_id)

    def register_service(self, service_name: str, endpoint: str, ttl: Optional[int] = None) -> Dict[str, Any]:
        """Register a service endpoint into the catalog."""
        res = self.registrar.process({
            "service_name": service_name,
            "endpoint": endpoint,
            "ttl": ttl or self.ttl_seconds,
        }) if self.registrar else {
            "record": {"service_name": service_name, "endpoint": endpoint, "expires_at": time.time() + (ttl or self.ttl_seconds)}
        }
        if service_name not in self.catalog:
            self.catalog[service_name] = []
        # Replace if endpoint exists, else append
        self.catalog[service_name] = [r for r in self.catalog[service_name] if r.get("endpoint") != endpoint]
        self.catalog[service_name].append(res["record"])
        if self.cache:
            self.cache.process({"cache": self.local_cache, "key": service_name, "value": [endpoint]})
        return {"registered": True, "service_name": service_name, "endpoint": endpoint}

    def discover_service(self, service_name: str) -> List[Dict[str, Any]]:
        """Retrieve all active, healthy instances for a service."""
        res = self.finder.process({"service_name": service_name, "catalog": self.catalog}) if self.finder else {
            "instances": [r for r in self.catalog.get(service_name, []) if r.get("expires_at", 0) > time.time()]
        }
        return res.get("instances", [])

    def prune_expired(self) -> Dict[str, Any]:
        """Purge all expired service leases from the registry."""
        if self.health_checker:
            res = self.health_checker.process({"catalog": self.catalog})
            self.catalog = res.get("catalog", self.catalog)
            return {"active_count": res.get("active_count", 0), "expired_count": res.get("expired_count", 0)}
        return {"active_count": len(self.catalog), "expired_count": 0}
