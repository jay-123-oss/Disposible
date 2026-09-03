"""CLI utility to query and display status of the distributed cluster.

Usage:
    python -m distributed.status
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Dict

from distributed.distributed_orchestrator import DistributedOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ClusterStatus")


def get_status() -> Dict[str, Any]:
    """Retrieve diagnostic state snapshot from DistributedOrchestrator."""
    orch = DistributedOrchestrator(agent_id="CLI_STATUS_ORCH", auto_spawn_subagents=True)
    orch.run_cluster_lifecycle()
    return orch.get_cluster_status()


def main() -> int:
    parser = argparse.ArgumentParser(description="Display Fractal cluster operational status")
    args = parser.parse_args()

    status = get_status()
    print(json.dumps(status, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
