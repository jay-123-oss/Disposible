"""Request distribution and load balancing algorithms (round-robin, least-connections, IP hash)."""

from __future__ import annotations

import itertools
from typing import Any, Dict, List, Optional


class RequestDistributorUtil:
    """Multi-algorithm request balancer."""

    def __init__(self, backends: Optional[List[str]] = None, algorithm: str = "round_robin") -> None:
        self.backends = backends or ["node-1:8000", "node-2:8000", "node-3:8000"]
        self.algorithm = algorithm
        self._cycle = itertools.cycle(self.backends)
        self.connections: Dict[str, int] = {b: 0 for b in self.backends}

    def get_next_backend(self, client_ip: Optional[str] = None) -> str:
        """Route request to appropriate backend node."""
        if not self.backends:
            raise RuntimeError("No available healthy backends")

        if self.algorithm == "least_connections":
            selected = min(self.backends, key=lambda b: self.connections.get(b, 0))
            self.connections[selected] += 1
            return selected
        elif self.algorithm == "ip_hash" and client_ip:
            idx = abs(hash(client_ip)) % len(self.backends)
            return self.backends[idx]

        # Default: round_robin
        return next(self._cycle)

    def release_connection(self, backend: str) -> None:
        """Decrement active connection count."""
        if backend in self.connections and self.connections[backend] > 0:
            self.connections[backend] -= 1
