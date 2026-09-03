#!/usr/bin/env python3
"""Shortcut CLI to deploy 6 LLM agents exclusively to Google Colab."""

from __future__ import annotations

import argparse
import sys
from utils.colab_utils import ColabDeployer

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass



def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy 6 LLM Agents to Google Colab")
    parser.add_argument("--open", action="store_true", help="Open notebook in browser upon deployment")
    args = parser.parse_args()

    deployer = ColabDeployer()
    res = deployer.deploy(open_browser=args.open)
    return 0 if res.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
