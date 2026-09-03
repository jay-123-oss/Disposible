"""Main CLI entry point for the Fractal Multi-Agent Coding System.

Supports:
- Interactive session mode.
- Single-task execution mode with immediate results and quality verification.
- System status inspection.
- POSIX/Windows signal trapping for graceful termination.
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from typing import Any

from core import (
    Orchestrator,
    TaskPriority,
    __version__,
)


logger = logging.getLogger("FractalCore.CLI")


def signal_handler(signum: int, frame: Any) -> None:
    """Intercept OS termination signals and trigger orderly shutdown."""
    print("\n[!] Termination signal received. Performing graceful shutdown...")
    orchestrator = Orchestrator()
    orchestrator.shutdown()
    sys.exit(0)


def run_single_task(orchestrator: Orchestrator, intent: str, capability: str) -> int:
    """Execute a single atomic or root task and print results."""
    # Ensure domain agents are registered for targeted capabilities
    if capability in ("planning", "intent", "requirements", "tech_stack", "architecture"):
        try:
            from agents.planning import register_all_planning_agents
            register_all_planning_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("backend_development", "api_design", "database", "coding", "api_route_generation"):
        try:
            from agents.coding import register_all_coding_agents
            register_all_coding_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("testing", "test_coordination", "unit_test_generation", "integration_test_generation"):
        try:
            from agents.testing import register_all_testing_agents
            register_all_testing_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("security", "security_orchestration", "security_audit", "vulnerability_assessment", "auth_audit"):
        try:
            from agents.security import register_all_security_agents
            register_all_security_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("quality", "quality_orchestration", "code_review", "formatting", "complexity_analysis", "quality_audit"):
        try:
            from agents.quality import register_all_quality_agents
            register_all_quality_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("infrastructure", "infrastructure_orchestration", "cloud_deployment", "docker_setup", "kubernetes", "terraform"):
        try:
            from agents.infrastructure import register_all_infrastructure_agents
            register_all_infrastructure_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("commstate", "communication_orchestration", "state_orchestration", "task_store", "mailbox"):
        try:
            from agents.commstate import register_all_commstate_agents
            register_all_commstate_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("monitoring", "observability", "metrics", "health_check", "live_debugger", "alert_management"):
        try:
            from agents.monitoring import register_all_monitoring_agents
            register_all_monitoring_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("integration", "system_assembly", "workflow", "bootstrap", "integration_orchestration"):
        try:
            from integration import register_all_integration_agents
            register_all_integration_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("testing_validation", "system_tests", "validation_engine", "test_orchestration"):
        try:
            from tests import register_all_testing_validation_agents
            register_all_testing_validation_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("documentation", "docs", "documentation_orchestration", "api_docs", "user_guide"):
        try:
            from agents.documentation import register_all_documentation_agents
            register_all_documentation_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("deployment", "distribution", "deployment_orchestration", "release_management", "k8s_deployer", "docker_deployer"):
        try:
            from agents.deployment import register_all_deployment_agents
            register_all_deployment_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("production", "production_optimization", "production_orchestration", "performance_optimizer", "memory_optimizer", "load_balancer"):
        try:
            from production import register_all_production_agents
            register_all_production_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("performance", "performance_testing", "load_testing", "stress_testing", "performance_orchestration", "benchmark_runner"):
        try:
            from performance import register_all_performance_agents
            register_all_performance_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("uat", "user_acceptance_testing", "uat_orchestration", "end_to_end_testing", "acceptance_criteria_checker"):
        try:
            from uat import register_all_uat_agents
            register_all_uat_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("final_integration", "final_integration_orchestration", "system_assembly", "deploy", "go_live", "smoke_test"):
        try:
            from final_integration import register_all_final_integration_agents
            register_all_final_integration_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("monitoring_support", "production_monitoring", "production_monitoring_orchestrator", "real_time_monitor", "incident_detector", "incident_responder"):
        try:
            from monitoring_support import register_all_monitoring_support_agents
            register_all_monitoring_support_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("closure", "final_closure", "project_closure", "final_closure_orchestrator", "documentation_reviewer", "quality_auditor"):
        try:
            from closure import register_all_closure_agents
            register_all_closure_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("ai_extensions", "ai_extensions_orchestrator", "model_selector", "cost_optimizer", "code_generator", "semantic_search", "code_review_ai"):
        try:
            from ai_extensions import register_all_ai_extensions_agents
            register_all_ai_extensions_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("multi_lang", "multi_language", "multi_language_orchestrator", "python_generator", "node_generator", "go_generator", "rust_generator", "java_generator", "language_detector", "language_translator"):
        try:
            from multi_lang import register_all_multi_lang_agents
            register_all_multi_lang_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("plugins", "plugin_system", "plugin_orchestrator", "plugin_manager", "plugin_loader", "plugin_store", "plugin_installer", "plugin_marketplace"):
        try:
            from plugins import register_all_plugin_agents
            register_all_plugin_agents(orchestrator.registry)
        except Exception as exc:
            pass
    elif capability in ("distributed", "distributed_architecture", "distributed_orchestrator", "node_manager", "cluster_coordinator", "load_balancer", "service_discovery", "raft", "consensus"):
        try:
            from distributed import register_all_distributed_agents
            register_all_distributed_agents(orchestrator.registry)
        except Exception as exc:
            pass


    print(f"\n[*] Submitting single task: '{intent}' (Target capability: {capability})...")
    task_id = orchestrator.submit_task(
        intent=intent,
        assigned_capability=capability,
        priority=TaskPriority.HIGH,
    )
    print(f"[*] Task enqueued with ID: {task_id}. Waiting for execution...")

    success = orchestrator.wait_for_completion(timeout=60.0)
    task_item = orchestrator.task_queue.get_task(task_id)

    if task_item and task_item.status.value == "COMPLETED":
        print(f"\n[+] SUCCESS: Task '{task_id}' finished successfully!")
        print("-" * 60)
        output = task_item.result.get("output", "") if task_item.result else ""
        print(f"Output:\n{output}")
        print("-" * 60)
        return 0
    else:
        err = task_item.error_message if task_item else "Unknown execution timeout"
        print(f"\n[-] FAILED: Task '{task_id}' failed: {err}")
        return 1


def run_interactive_mode(orchestrator: Orchestrator) -> None:
    """Launch the interactive REPL prompt for issuing multiple tasks."""
    print("=" * 70)
    print(f"  FRACTAL MULTI-AGENT CODING SYSTEM v{__version__} - INTERACTIVE MODE")
    print(f"  Session ID: {orchestrator.session_id}")
    print("  Type 'exit', 'quit', or press Ctrl+C to terminate.")
    print("  Type 'status' to view active agent registry and queue summary.")
    print("=" * 70)

    while True:
        try:
            user_input = input("\nfractal-agent> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print("[*] Exiting interactive mode...")
                break
            if user_input.lower() == "status":
                summary = orchestrator.task_queue.get_dag_summary()
                telemetry = orchestrator.monitor.get_summary()
                print("\n[+] --- System Status ---")
                print(f"  Total Tasks: {summary['total_tasks']} (Completed: {summary['completed_count']})")
                print(f"  Pending Queue: {summary['pending_queue_size']}")
                print(f"  Avg Latency: {telemetry['average_latency_s']}s | Tokens: {telemetry['total_tokens_consumed']}")
                continue

            # Standard task submission
            print(f"[*] Dispatching task to PLANNER domain: '{user_input}'...")
            task_id = orchestrator.submit_task(
                intent=user_input,
                assigned_capability="intent",
                priority=TaskPriority.MEDIUM,
            )
            orchestrator.wait_for_completion(timeout=45.0)
            task_item = orchestrator.task_queue.get_task(task_id)
            if task_item and task_item.status.value == "COMPLETED":
                print(f"[+] Task {task_id} Completed:\n{task_item.result.get('output', '')}")
            else:
                err = task_item.error_message if task_item else "Timeout"
                print(f"[-] Task {task_id} Failed: {err}")

        except (KeyboardInterrupt, EOFError):
            print("\n[*] Exiting...")
            break


def main() -> int:
    """Entry point for command-line execution."""
    parser = argparse.ArgumentParser(
        description="Fractal Multi-Agent Autonomous Coding System Core CLI",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to YAML configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--task",
        type=str,
        help="Single task intent to execute",
    )
    parser.add_argument(
        "--capability",
        type=str,
        default="planning",
        help="Target capability for single task mode (default: planning)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive REPL mode",
    )
    parser.add_argument(
        "--batch",
        type=str,
        help="Path to JSON or YAML batch task manifest",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Display current system state and exit",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Launch the interactive Web GUI Dashboard and open in browser",
    )
    args = parser.parse_args()

    if args.dashboard:
        import subprocess
        return subprocess.run([sys.executable, "dashboard.py"]).returncode


    # Register OS signals
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)

    # Boot Orchestrator
    orchestrator = Orchestrator(config_path=args.config)
    orchestrator.startup()

    try:
        if args.status:
            summary = orchestrator.task_queue.get_dag_summary()
            agents = orchestrator.registry.get_all_agents()
            print("\n[+] --- Fractal Multi-Agent System Snapshot ---")
            print(f"  Session ID: {orchestrator.session_id}")
            print(f"  Registered Root Agents ({len(agents)}):")
            for a in agents:
                print(f"    - {a.name} [{a.agent_id}] (Depth: {a.depth}, Model: {a._model}, RAM: {a._resources_mb}MB)")
            print(f"  Task Queue Summary: {summary}")
            return 0

        if args.batch:
            import json
            import os
            import yaml
            if not os.path.exists(args.batch):
                print(f"[-] Batch manifest file not found: {args.batch}")
                return 1
            with open(args.batch, "r", encoding="utf-8") as f:
                tasks = json.load(f) if args.batch.endswith(".json") else (yaml.safe_load(f) or [])
            print(f"[*] Processing batch of {len(tasks)} tasks...")
            failures = 0
            for t in tasks:
                ret = run_single_task(orchestrator, t.get("intent", ""), t.get("capability", "planning"))
                if ret != 0:
                    failures += 1
            print(f"\n[+] Batch complete: {len(tasks) - failures}/{len(tasks)} succeeded.")
            return 0 if failures == 0 else 1

        if args.task:
            return run_single_task(orchestrator, args.task, args.capability)

        if args.interactive or len(sys.argv) == 1:
            run_interactive_mode(orchestrator)
            return 0

        parser.print_help()
        return 0

    finally:
        orchestrator.shutdown()


if __name__ == "__main__":
    sys.exit(main())
