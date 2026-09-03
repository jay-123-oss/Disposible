#!/usr/bin/env python3
"""Shortcut CLI to deploy 6 LLM agents to both Kaggle and Google Colab."""

from __future__ import annotations

import argparse
import sys
from utils.colab_utils import ColabDeployer
from utils.kaggle_utils import KaggleDeployer

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass



def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy 6 LLM Agents to both Kaggle and Google Colab")
    parser.add_argument("--open", action="store_true", help="Open notebooks in browser upon deployment")
    args = parser.parse_args()

    k_deployer = KaggleDeployer()
    c_deployer = ColabDeployer()

    print("=" * 70)
    print("🚀 Auto-Deploying 6 LLM Agents to BOTH Platforms...")
    print("=" * 70)
    res_k = k_deployer.deploy(open_browser=args.open)
    print("-" * 70)
    res_c = c_deployer.deploy(open_browser=args.open)
    print("=" * 70)
    print("🎉 Both deployments configured successfully!")
    print("=" * 70)

    return 0 if (res_k.get("success") and res_c.get("success")) else 1


if __name__ == "__main__":
    sys.exit(main())
