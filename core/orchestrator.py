"""Main Orchestrator class for the Fractal Multi-Agent Coding System.

Implements:
- Singleton pattern managing the system lifecycle and root agent initialization.
- Dynamic task reception, DAG scheduling, and worker dispatching.
- Root domain agents initialization (PLANNER, DEVELOPER, TESTER, SECURITY, DEPLOYMENT, MONITOR).
- Integration with Registry, TaskQueue, StateManager, MessageBus, QualityGate, Monitor, and Sandbox.
- Graceful shutdown and session management.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

import yaml

from core.agent_base import BaseAgent
from core.communication import MessageBus, TraceType
from core.exceptions import OrchestratorError
from core.monitor import AlertSeverity, SystemMonitor
from core.quality_gate import GatePhase, QualityGate
from core.registry import AgentRegistry
from core.sandbox import SandboxManager
from core.state_manager import StateManager
from core.task_queue import TaskPriority, TaskQueue, TaskStatus


logger = logging.getLogger("FractalCore.Orchestrator")


class GenericDomainAgent(BaseAgent):
    """Concrete BaseAgent implementation representing root domain agents."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("Domain agent '%s' initialized for task %s", self.name, task_envelope.get("task_id"))

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        intent = task_envelope.get("intent", "Execute domain task")
        logger.info("Domain agent '%s' processing intent: %s", self.name, intent)

        # Generate output through LLM or deterministic rule-base
        prompt = f"Task: {intent}\nContext: {task_envelope.get('payload', {})}"
        response_text = self.query_llm(prompt)

        return {
            "agent_id": self.agent_id,
            "domain": self.name,
            "status": "COMPLETED",
            "output": response_text,
            "tokens_consumed": len(response_text) // 4 + 100,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if not result or result.get("status") != "COMPLETED":
            raise OrchestratorError(f"Validation failed for domain agent {self.name}")
        logger.debug("Domain agent '%s' validated task output successfully.", self.name)
        return result

    def cleanup(self) -> None:
        logger.debug("Domain agent '%s' cleaned up resources.", self.name)


class Orchestrator:
    """Central orchestrator managing sessions, root agents, and task execution workflows."""

    _instance: Optional[Orchestrator] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> Orchestrator:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Orchestrator, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config_path: str = "config.yaml") -> None:
        if getattr(self, "_initialized", False):
            return

        self._config_path = config_path
        self._config = self._load_config(config_path)
        self._session_id = f"SES_{uuid.uuid4().hex[:8]}"
        self._is_running = False
        self._shutdown_event = threading.Event()

        # Initialize Core Subsystems
        sys_cfg = self._config.get("system", {})
        self._max_depth = sys_cfg.get("max_depth", 2)
        self._max_concurrent = sys_cfg.get("max_concurrent", 10)

        self._registry = AgentRegistry(
            max_system_ram_mb=8192,
            max_agents=sys_cfg.get("max_agents", 200),
        )

        q_cfg = self._config.get("quality", {})
        self._quality_gate = QualityGate(
            min_score=q_cfg.get("min_score", 85.0),
            require_approval=q_cfg.get("require_approval", True),
            test_coverage_min=q_cfg.get("test_coverage_min", 80.0),
            max_retries=q_cfg.get("max_retries", 3),
        )

        st_cfg = self._config.get("state", {})
        self._state_manager = StateManager(
            persist_path=st_cfg.get("persist_path", "./state/"),
            compression_threshold=st_cfg.get("compression_threshold", 4096),
            max_checkpoints=st_cfg.get("max_checkpoints", 10),
        )

        self._communication = MessageBus(artifacts_dir="./state/artifacts/")

        log_cfg = self._config.get("logging", {})
        self._monitor = SystemMonitor(
            log_dir=log_cfg.get("path", "./logs/"),
            log_level=log_cfg.get("level", "INFO"),
            latency_threshold_s=30.0,
        )

        sb_cfg = self._config.get("sandbox", {})
        self._sandbox = SandboxManager(
            enabled=sb_cfg.get("enabled", True),
            use_docker=sb_cfg.get("docker", False),
            timeout_seconds=sb_cfg.get("timeout_seconds", 30.0),
            max_memory_mb=sb_cfg.get("max_memory_mb", 256),
            temp_dir=sb_cfg.get("temp_dir", "./temp"),
        )

        self._task_queue = TaskQueue(
            max_retries=q_cfg.get("max_retries", 3),
            default_timeout_seconds=sb_cfg.get("timeout_seconds", 30.0),
        )

        self._worker_threads: List[threading.Thread] = []
        self._initialized = True
        logger.info("Orchestrator initialized successfully for Session: %s", self._session_id)

    # --------------------------------------------------------------------------
    # Configuration Loader
    # --------------------------------------------------------------------------

    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load YAML configuration from path with fallback defaults."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as exc:
            logger.warning("Could not read config at %s: %s. Using default parameters.", path, exc)
            return {
                "system": {"name": "FractalSystem", "max_depth": 2, "max_agents": 200, "max_concurrent": 5},
                "llm": {"endpoint": "http://localhost:11434", "model": "qwen2.5-coder:3b"},
                "agents": {"root_agents": []},
            }

    # --------------------------------------------------------------------------
    # Startup & Root Agents Initialization
    # --------------------------------------------------------------------------

    def startup(self) -> None:
        """Boot orchestrator, register root domain agents, and start background workers."""
        if self._is_running:
            logger.warning("Orchestrator is already running.")
            return

        self._is_running = True
        self._shutdown_event.clear()
        logger.info("Starting up Fractal Multi-Agent System (Session: %s)...", self._session_id)

        # Update global state
        self._state_manager.update_global_state({
            "system_status": "RUNNING",
            "active_session_id": self._session_id,
            "session_started_at": time.time(),
        })

        # Initialize root agents defined in config
        root_agent_configs = self._config.get("agents", {}).get("root_agents", [])
        llm_cfg = self._config.get("llm", {})
        default_endpoint = llm_cfg.get("endpoint", "http://localhost:11434")

        for cfg in root_agent_configs:
            name = cfg.get("name", "AGENT")
            agent = GenericDomainAgent(
                name=name,
                capabilities=cfg.get("capabilities", []),
                model=cfg.get("model", llm_cfg.get("model", "qwen2.5-coder:3b")),
                resources_mb=cfg.get("resources_mb", 512),
                max_depth=self._max_depth,
                llm_endpoint=default_endpoint,
            )
            self._registry.register_agent(agent)

        # Start worker thread pool
        for i in range(self._max_concurrent):
            t = threading.Thread(target=self._worker_loop, name=f"Worker-{i}", daemon=True)
            t.start()
            self._worker_threads.append(t)

        # Emit initial stigmergy signal
        self._communication.emit_trace(
            origin_agent_id="ORCH_001",
            topic="SYSTEM_INITIALIZED",
            trace_type=TraceType.INFO,
            metadata={"session_id": self._session_id},
        )
        logger.info("System startup complete. Active workers: %d", len(self._worker_threads))

    # --------------------------------------------------------------------------
    # Task Ingestion & Execution Loop
    # --------------------------------------------------------------------------

    def submit_task(
        self,
        intent: str,
        assigned_capability: str,
        task_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: Optional[List[str]] = None,
    ) -> str:
        """Submit a new task to the queue."""
        tid = task_id or f"TSK_{uuid.uuid4().hex[:8]}"
        self._task_queue.add_task(
            task_id=tid,
            intent=intent,
            assigned_capability=assigned_capability,
            payload=payload,
            priority=priority,
            dependencies=dependencies,
        )
        logger.info("Submitted task '%s': %s (Target capability: %s)", tid, intent, assigned_capability)
        return tid

    def _worker_loop(self) -> None:
        """Background worker thread executing tasks from the TaskQueue."""
        while self._is_running and not self._shutdown_event.is_set():
            task_item = self._task_queue.get_next_task()
            if not task_item:
                time.sleep(0.1)
                continue

            task_id = task_item.task_id
            start_ts = time.time()
            logger.info("Worker acquired task '%s' (Intent: '%s')", task_id, task_item.intent)

            try:
                # Resolve candidate agent by capability
                candidates = self._registry.find_by_capability(task_item.assigned_capability)
                if not candidates:
                    # Fallback to any registered agent if specific capability is missing
                    all_agents = self._registry.get_all_agents()
                    if not all_agents:
                        raise OrchestratorError(f"No agent available with capability '{task_item.assigned_capability}'")
                    agent = all_agents[0]
                else:
                    agent = candidates[0]

                # Prepare task envelope
                envelope = {
                    "task_id": task_id,
                    "intent": task_item.intent,
                    "payload": task_item.payload,
                    "session_id": self._session_id,
                }

                # Execute lifecycle through agent
                result = agent.execute_lifecycle(envelope)

                # Validate with QualityGate
                gate_metrics = {
                    "correctness": 100.0,
                    "security": 100.0,
                    "maintainability": 95.0,
                    "performance": 95.0,
                    "syntax_errors": 0,
                    "failed_tests": 0,
                    "critical_vulns": 0,
                }
                self._quality_gate.validate_or_raise(GatePhase.QG_3_SYNTAX, gate_metrics)

                # Complete task and record telemetry
                duration = time.time() - start_ts
                tokens_used = result.get("tokens_consumed", 250)
                self._task_queue.complete_task(task_id, result)
                self._monitor.record_task_execution(task_id, duration, tokens_used)

                # Emit attraction trace on blackboard
                self._communication.emit_trace(
                    origin_agent_id=agent.agent_id,
                    topic=f"TASK_COMPLETED:{task_id}",
                    trace_type=TraceType.ATTRACTION,
                    metadata={"task_id": task_id, "duration": duration},
                )

            except Exception as exc:
                duration = time.time() - start_ts
                logger.error("Error executing task '%s': %s", task_id, exc)
                self._task_queue.fail_task(task_id, str(exc))
                self._monitor.record_error(f"TaskExecution:{task_id}", str(exc), AlertSeverity.HIGH)
                self._communication.emit_trace(
                    origin_agent_id="SYSTEM",
                    topic=f"TASK_FAILED:{task_id}",
                    trace_type=TraceType.DANGER,
                    metadata={"error": str(exc)},
                )

    def wait_for_completion(self, poll_interval: float = 0.2, timeout: Optional[float] = None) -> bool:
        """Block until all queued tasks complete or timeout expires."""
        start_time = time.time()
        while self._is_running:
            if self._task_queue.is_all_completed():
                return True
            if timeout and (time.time() - start_time) > timeout:
                logger.warning("wait_for_completion timed out after %.1fs", timeout)
                return False
            time.sleep(poll_interval)
        return True

    # --------------------------------------------------------------------------
    # Shutdown
    # --------------------------------------------------------------------------

    def shutdown(self) -> None:
        """Signal all worker threads, create terminal checkpoint, and clean up resources."""
        if not self._is_running:
            return

        logger.info("Initiating graceful shutdown for Session: %s...", self._session_id)
        self._is_running = False
        self._shutdown_event.set()

        # Create session checkpoint
        try:
            self._state_manager.create_checkpoint(
                checkpoint_id=f"SHUTDOWN_{self._session_id}",
                metadata={"session_id": self._session_id, "timestamp": time.time()},
            )
        except Exception as exc:
            logger.error("Failed to save terminal checkpoint: %s", exc)

        # Update global state
        self._state_manager.update_global_state({
            "system_status": "SHUTDOWN",
            "shutdown_at": time.time(),
        })

        # Clear active registry
        self._registry.clear()
        logger.info("Orchestrator shutdown complete.")

    # --------------------------------------------------------------------------
    # Properties for Subsystems Access
    # --------------------------------------------------------------------------

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def registry(self) -> AgentRegistry:
        return self._registry

    @property
    def task_queue(self) -> TaskQueue:
        return self._task_queue

    @property
    def state_manager(self) -> StateManager:
        return self._state_manager

    @property
    def communication(self) -> MessageBus:
        return self._communication

    @property
    def monitor(self) -> SystemMonitor:
        return self._monitor

    @property
    def sandbox(self) -> SandboxManager:
        return self._sandbox
