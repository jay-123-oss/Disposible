"""CLI utility to gracefully leave an active Fractal cluster.

Usage:
    python -m distributed.leave_cluster --node-id node-4 --cluster fractal-cluster
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Dict

from distributed.cluster_coordinator import ClusterCoordinator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LeaveCluster")


def leave_cluster(node_id: str, cluster_name: str = "fractal-cluster", reason: str = "graceful_exit") -> Dict[str, Any]:
    """Gracefully remove node from specified cluster."""
    coord = ClusterCoordinator(cluster_name=cluster_name, agent_id="CLI_LEAVE_COORD")
    coord.join_cluster(node_id)  # ensure membership present for departure
    res = coord.leave_cluster(node_id=node_id, reason=reason)
    logger.info("Node %s left cluster '%s': %s", node_id, cluster_name, res)
    return res


def main() -> int:
    parser = argparse.ArgumentParser(description="Leave a Fractal cluster")
    parser.add_argument("--node-id", type=str, required=True, help="Departing node identifier")
    parser.add_argument("--cluster", type=str, default="fractal-cluster", help="Cluster name")
    parser.add_argument("--reason", type=str, default="manual", help="Departure reason")
    args = parser.parse_args()

    res = leave_cluster(node_id=args.node_id, cluster_name=args.cluster, reason=args.reason)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
