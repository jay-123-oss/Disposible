"""CLI utility to deploy and provision a new distributed cluster node.

Usage:
    python -m distributed.deploy_node --id node-4 --host 127.0.0.1 --port 8004 --role follower
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Dict

from distributed.node_manager import NodeManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DeployNode")


def deploy_node(node_id: str, host: str = "127.0.0.1", port: int = 8000, role: str = "follower") -> Dict[str, Any]:
    """Deploy and register a cluster node."""
    mgr = NodeManager(agent_id="CLI_DEPLOY_NODE_MGR")
    node_spec = {
        "id": node_id,
        "host": host,
        "port": port,
        "role": role,
    }
    result = mgr.register_node(node_spec)
    logger.info("Deployed node %s on %s:%d (role: %s)", node_id, host, port, role)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy a new Fractal cluster node")
    parser.add_argument("--id", type=str, default="node-local", help="Node identifier")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Node hostname/IP")
    parser.add_argument("--port", type=int, default=8000, help="Node listen port")
    parser.add_argument("--role", type=str, default="follower", choices=["leader", "follower"], help="Raft initial role")
    args = parser.parse_args()

    res = deploy_node(node_id=args.id, host=args.host, port=args.port, role=args.role)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
