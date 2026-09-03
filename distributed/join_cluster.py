"""CLI utility to join an existing Fractal cluster.

Usage:
    python -m distributed.join_cluster --node-id node-4 --cluster fractal-cluster
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Dict

from distributed.cluster_coordinator import ClusterCoordinator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("JoinCluster")


def join_cluster(node_id: str, cluster_name: str = "fractal-cluster") -> Dict[str, Any]:
    """Join node into specified cluster."""
    coord = ClusterCoordinator(cluster_name=cluster_name, agent_id="CLI_JOIN_COORD")
    res = coord.join_cluster(node_id=node_id)
    logger.info("Node %s joined cluster '%s' at epoch %d", node_id, cluster_name, res.get("epoch", 1))
    return res


def main() -> int:
    parser = argparse.ArgumentParser(description="Join node to a Fractal cluster")
    parser.add_argument("--node-id", type=str, required=True, help="Joining node identifier")
    parser.add_argument("--cluster", type=str, default="fractal-cluster", help="Target cluster name")
    args = parser.parse_args()

    res = join_cluster(node_id=args.node_id, cluster_name=args.cluster)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
