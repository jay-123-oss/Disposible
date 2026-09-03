#!/usr/bin/env python3
"""Main CLI Entry Point for 6-Agent Core Auto-Deployment to Kaggle and Google Colab.

Usage:
    python deploy.py --kaggle              # Deploy to Kaggle only
    python deploy.py --colab               # Deploy to Colab only
    python deploy.py --both                # Deploy to both platforms
    python deploy.py --kaggle --open       # Deploy and launch Kaggle in browser
    python deploy.py --colab --open        # Deploy and launch Colab in browser
    python deploy.py --both --open         # Deploy both and open in browser
    python deploy.py --status              # Check status of deployments
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict

from utils.colab_utils import ColabDeployer
from utils.kaggle_utils import KaggleDeployer

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

logger = logging.getLogger("AutoDeploy")


def check_status() -> Dict[str, Any]:
    """Inspect local configuration and status of notebook artifacts."""
    from utils.notebook_generator import generate_and_save_all
    paths = generate_and_save_all()

    kaggle_conf_exists = os.path.exists("kaggle_config.json")
    colab_conf_exists = os.path.exists("colab_config.json")
    env_exists = os.path.exists(".env")

    status = {
        "status": "ready",
        "agents": {
            "coding": "Qwen2.5-Coder:3B",
            "testing": "Qwen2.5-Coder:3B",
            "security": "Qwen2.5-Coder:3B",
            "quality": "Llama3.2:3B",
            "infrastructure": "Llama3.2:3B",
            "embedding": "Nomic-Embed-Text",
        },
        "notebooks": {
            "kaggle": paths["kaggle"],
            "colab": paths["colab"],
        },
        "config_files": {
            "kaggle_config.json": kaggle_conf_exists,
            "colab_config.json": colab_conf_exists,
            ".env": env_exists,
        },
        "endpoints": {
            "kaggle_tunnel": "https://fractal-core-6agents.trycloudflare.com",
            "colab_tunnel": "https://fractal-core-6agents.ngrok-free.app",
        },
    }
    return status


def deploy_kaggle(open_browser: bool = False) -> Dict[str, Any]:
    """Deploy to Kaggle."""
    deployer = KaggleDeployer()
    return deployer.deploy(open_browser=open_browser)


def deploy_colab(open_browser: bool = False) -> Dict[str, Any]:
    """Deploy to Google Colab."""
    deployer = ColabDeployer()
    return deployer.deploy(open_browser=open_browser)


def deploy_both(open_browser: bool = False) -> Dict[str, Any]:
    """Deploy to both Kaggle and Google Colab."""
    print("=" * 70)
    print("🚀 Auto-Deploying 6 LLM Agents to BOTH Kaggle and Google Colab...")
    print("=" * 70)
    res_kaggle = deploy_kaggle(open_browser=open_browser)
    print("-" * 70)
    res_colab = deploy_colab(open_browser=open_browser)
    print("=" * 70)
    print("🎉 Both deployments successfully configured!")
    print("=" * 70)
    return {
        "success": True,
        "kaggle": res_kaggle,
        "colab": res_colab,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auto-deploy 6 core LLM agents to Kaggle and Google Colab with zero manual intervention.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--kaggle",
        action="store_true",
        help="Deploy only to Kaggle",
    )
    parser.add_argument(
        "--colab",
        action="store_true",
        help="Deploy only to Google Colab",
    )
    parser.add_argument(
        "--both",
        action="store_true",
        help="Deploy to both Kaggle and Colab",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open deployed notebook in default web browser",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check deployment readiness and configuration status",
    )

    args = parser.parse_args()

    if args.status:
        st = check_status()
        print(json.dumps(st, indent=2))
        return 0

    if args.both:
        deploy_both(open_browser=args.open)
        return 0

    if args.kaggle:
        deploy_kaggle(open_browser=args.open)
        return 0

    if args.colab:
        deploy_colab(open_browser=args.open)
        return 0

    # Default if no specific mode selected: display help
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
