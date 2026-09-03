"""Rich CLI command structure and command execution dispatcher for the Fractal System."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, List, Optional

from app import create_app
from core import __version__


def create_cli_parser() -> argparse.ArgumentParser:
    """Construct multi-command CLI parser."""
    parser = argparse.ArgumentParser(
        prog="fractal",
        description="Fractal Multi-Agent Autonomous Coding System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to YAML configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Fractal Multi-Agent System v{__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: run
    run_p = subparsers.add_parser("run", help="Execute a single task")
    run_p.add_argument("task", type=str, help="Task intent description")
    run_p.add_argument("--capability", type=str, default="planning", help="Target agent capability")
    run_p.add_argument("--timeout", type=float, default=60.0, help="Task timeout in seconds")

    # Command: batch
    batch_p = subparsers.add_parser("batch", help="Execute batch task manifest")
    batch_p.add_argument("manifest", type=str, help="Path to JSON or YAML task manifest")
    batch_p.add_argument("--timeout", type=float, default=45.0, help="Timeout per task in seconds")

    # Command: status
    subparsers.add_parser("status", help="Inspect runtime system status and active agents")

    # Command: health
    subparsers.add_parser("health", help="Run comprehensive cluster health check")

    # Command: interactive
    subparsers.add_parser("interactive", help="Start interactive task prompt REPL")

    # Command: dashboard
    subparsers.add_parser("dashboard", help="Launch interactive web GUI dashboard in browser")

    return parser



def handle_run_command(app: Any, task: str, capability: str, timeout: float) -> int:
    """Execute 'run' command."""
    print(f"[*] Dispatching task: '{task}' (Capability: {capability})...")
    res = app.run_task(intent=task, capability=capability, timeout=timeout)
    if res["success"]:
        print(f"\n[+] Task Completed Successfully [{res['task_id']}]:")
        print("-" * 60)
        print(res.get("output", ""))
        print("-" * 60)
        return 0
    else:
        print(f"\n[-] Task Failed [{res['task_id']}]: {res.get('error')}")
        return 1


def handle_batch_command(app: Any, manifest_path: str, timeout: float) -> int:
    """Execute 'batch' command."""
    if not os.path.exists(manifest_path):
        print(f"[-] Manifest file not found: {manifest_path}")
        return 1

    tasks = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        if manifest_path.endswith(".json"):
            tasks = json.load(f)
        else:
            import yaml
            tasks = yaml.safe_load(f) or []

    print(f"[*] Loaded {len(tasks)} tasks from {manifest_path}. Executing batch...")
    results = app.run_batch(tasks=tasks, timeout_per_task=timeout)

    succeeded = sum(1 for r in results if r["success"])
    print(f"\n[+] Batch Finished: {succeeded}/{len(results)} tasks succeeded.")
    return 0 if succeeded == len(results) else 1


def handle_status_command(app: Any) -> int:
    """Execute 'status' command."""
    status = app.get_status()
    print("\n[+] --- Fractal System Runtime Status ---")
    print(f"  Session ID: {status.get('session_id')}")
    print(f"  Registered Agents: {status.get('registered_agents_count')}")
    print(f"  DAG Summary: {status.get('dag_summary')}")
    print(f"  Telemetry: {status.get('telemetry')}")
    return 0


def handle_health_command(app: Any) -> int:
    """Execute 'health' command."""
    print("[*] Running system health audit...")
    from agents.monitoring import HealthChecker
    hc = HealthChecker(auto_spawn_subagents=True)
    res = hc.check_health()

    status_str = "HEALTHY" if res.get("overall_healthy", True) else "DEGRADED"
    print(f"\n[+] Overall Cluster Health: {status_str}")
    print(f"  System: {res.get('system', {}).get('healthy')}")
    print(f"  Agents: {res.get('agents', {}).get('healthy')}")
    print(f"  Services: {res.get('services', {}).get('healthy')}")
    return 0 if res.get("overall_healthy", True) else 1


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = create_cli_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    app = create_app(config_path=args.config)

    try:
        if args.command == "run":
            return handle_run_command(app, args.task, args.capability, args.timeout)
        elif args.command == "batch":
            return handle_batch_command(app, args.manifest, args.timeout)
        elif args.command == "status":
            return handle_status_command(app)
        elif args.command == "health":
            return handle_health_command(app)
        elif args.command == "interactive":
            from main import run_interactive_mode
            if app.orchestrator:
                run_interactive_mode(app.orchestrator)
            return 0
        elif args.command == "dashboard":
            import subprocess
            return subprocess.run([sys.executable, "dashboard.py"]).returncode
        else:
            parser.print_help()

            return 0
    finally:
        app.shutdown()


if __name__ == "__main__":
    sys.exit(main())
