"""Application initialization and system lifecycle harness for the Fractal Multi-Agent System."""

from __future__ import annotations

import logging
import os
import signal
import sys
from typing import Any, Dict, List, Optional

# Ensure project root is prioritized over test subpackages with identical names
_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if _ROOT_DIR in sys.path:
    sys.path.remove(_ROOT_DIR)
sys.path.insert(0, _ROOT_DIR)

from core import Orchestrator, TaskPriority, __version__
from integration import register_all_integration_agents


logger = logging.getLogger("FractalCore.App")


class Application:
    """Core application wrapper managing system bootstrap, execution dispatch, and shutdown."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        self.config_path = config_path
        self.orchestrator: Optional[Orchestrator] = None
        self._is_running = False

    def initialize(self) -> None:
        """Initialize orchestrator, register core signal hooks, and setup domain handlers."""
        logger.info("Initializing Fractal Multi-Agent Coding System v%s...", __version__)
        self.orchestrator = Orchestrator(config_path=self.config_path)
        self.orchestrator.startup()

        # Wire integration agents
        register_all_integration_agents(self.orchestrator.registry)

        self._is_running = True
        self._setup_signals()

    def _setup_signals(self) -> None:
        """Trap termination signals for graceful teardown."""
        def _handler(signum: int, frame: Any) -> None:
            logger.info("Termination signal received (%s). Triggering graceful application shutdown...", signum)
            self.shutdown()
            sys.exit(0)

        signal.signal(signal.SIGINT, _handler)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, _handler)

    def run_task(
        self,
        intent: str,
        capability: str = "planning",
        priority: TaskPriority = TaskPriority.HIGH,
        timeout: float = 60.0,
    ) -> Dict[str, Any]:
        """Submit a single task and block until completion or timeout."""
        if not self.orchestrator or not self._is_running:
            raise RuntimeError("Application is not running. Call initialize() first.")

        logger.info("Dispatching task: '%s' (Capability: %s)", intent, capability)
        task_id = self.orchestrator.submit_task(
            intent=intent,
            assigned_capability=capability,
            priority=priority,
        )

        self.orchestrator.wait_for_completion(timeout=timeout)
        task_item = self.orchestrator.task_queue.get_task(task_id)

        if task_item and task_item.status.value == "COMPLETED":
            return {
                "success": True,
                "task_id": task_id,
                "output": task_item.result.get("output", "") if task_item.result else "",
                "details": task_item.result,
            }
        else:
            err = task_item.error_message if task_item else "Task execution timed out"
            return {
                "success": False,
                "task_id": task_id,
                "error": err,
            }

    def run_batch(self, tasks: List[Dict[str, Any]], timeout_per_task: float = 45.0) -> List[Dict[str, Any]]:
        """Process a sequence of tasks in batch mode."""
        results = []
        for item in tasks:
            intent = item.get("intent", "unspecified task")
            capability = item.get("capability", "planning")
            res = self.run_task(intent=intent, capability=capability, timeout=timeout_per_task)
            results.append(res)
        return results

    def get_status(self) -> Dict[str, Any]:
        """Fetch current runtime diagnostic snapshot."""
        if not self.orchestrator:
            return {"status": "STOPPED"}

        dag = self.orchestrator.task_queue.get_dag_summary()
        telemetry = self.orchestrator.monitor.get_summary()
        agents = self.orchestrator.registry.get_all_agents()

        return {
            "session_id": self.orchestrator.session_id,
            "running": self._is_running,
            "registered_agents_count": len(agents),
            "dag_summary": dag,
            "telemetry": telemetry,
        }

    def shutdown(self) -> None:
        """Teardown system components and release all held resources."""
        if self.orchestrator and self._is_running:
            logger.info("Shutting down application...")
            self.orchestrator.shutdown()
            self._is_running = False


def create_app(config_path: str = "config.yaml") -> Application:
    """Factory helper creating and initializing an Application instance."""
    app = Application(config_path=config_path)
    app.initialize()
    return app


if __name__ == "__main__":
    app = create_app()
    print("[+] Application initialized successfully. Session ID:", app.orchestrator.session_id if app.orchestrator else "N/A")
    app.shutdown()
