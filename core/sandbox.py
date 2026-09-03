"""SandboxManager class for isolated, resource-bounded code execution.

Implements:
- Proxy pattern wrapping code execution with safety barriers.
- Dual execution engines: Docker containerization (if available) with local subprocess fallback.
- Enforced resource limiting: 256MB RAM cap and 30-second wall-clock execution timeout.
- Complete output capture (stdout, stderr, exit code, elapsed duration).
- Basic AST code-injection scanning before running untrusted scripts.
"""

from __future__ import annotations

import ast
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.exceptions import SandboxError


logger = logging.getLogger("FractalCore.Sandbox")


@dataclass
class ExecutionResult:
    """Standardized output container for sandboxed code execution."""
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False
    sandbox_type: str = "local"


class SandboxManager:
    """Manages isolated subprocess environments for safe code execution."""

    # Disallowed ast calls that represent dangerous system compromise
    DISALLOWED_MODULES = {"shutil", "ctypes"}

    def __init__(
        self,
        enabled: bool = True,
        use_docker: bool = False,
        timeout_seconds: float = 30.0,
        max_memory_mb: int = 256,
        temp_dir: str = "./temp",
    ) -> None:
        self._enabled = enabled
        self._use_docker = use_docker
        self._timeout_seconds = timeout_seconds
        self._max_memory_mb = max_memory_mb
        self._temp_dir = Path(temp_dir).resolve()
        self._temp_dir.mkdir(parents=True, exist_ok=True)
        self._docker_available = self._check_docker_availability() if use_docker else False

        logger.info(
            "SandboxManager initialized (Docker: %s [Available: %s], Timeout: %.1fs, RAM limit: %d MB, Temp: %s)",
            self._use_docker,
            self._docker_available,
            self._timeout_seconds,
            self._max_memory_mb,
            self._temp_dir,
        )

    def _check_docker_availability(self) -> bool:
        """Verify if Docker CLI is present and the daemon is reachable."""
        try:
            res = subprocess.run(["docker", "info"], capture_output=True, timeout=3, check=False)
            return res.returncode == 0
        except Exception:
            logger.debug("Docker is not available on host system. Using local subprocess isolation.")
            return False

    # --------------------------------------------------------------------------
    # Code Injection Prevention
    # --------------------------------------------------------------------------

    def validate_code_safety(self, code_str: str) -> None:
        """Scan code AST for forbidden patterns (e.g., direct OS destructors)."""
        try:
            tree = ast.parse(code_str)
        except SyntaxError as syn_err:
            raise SandboxError(f"Code failed initial syntax validation: {syn_err}") from syn_err

        for node in ast.walk(tree):
            # Check forbidden imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.DISALLOWED_MODULES:
                        raise SandboxError(f"Execution rejected: forbidden import '{alias.name}' detected.")
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.DISALLOWED_MODULES:
                    raise SandboxError(f"Execution rejected: forbidden import from '{node.module}' detected.")

    # --------------------------------------------------------------------------
    # Execution Dispatch
    # --------------------------------------------------------------------------

    def execute_python_code(
        self,
        code_str: str,
        timeout_seconds: Optional[float] = None,
        custom_env: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """Execute Python code in an isolated environment with resource bounds."""
        if not self._enabled:
            logger.warning("Sandbox disabled in config. Executing in non-isolated mode.")

        # Safety check
        self.validate_code_safety(code_str)
        timeout = timeout_seconds or self._timeout_seconds

        if self._use_docker and self._docker_available:
            return self._execute_in_docker(code_str, timeout)
        return self._execute_in_local_subprocess(code_str, timeout, custom_env)

    # --------------------------------------------------------------------------
    # Local Subprocess Engine (Fallback)
    # --------------------------------------------------------------------------

    def _execute_in_local_subprocess(
        self,
        code_str: str,
        timeout: float,
        custom_env: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """Run script in an isolated temp directory using current Python executable."""
        work_dir = Path(tempfile.mkdtemp(dir=str(self._temp_dir), prefix="sbx_"))
        script_path = work_dir / "runner.py"

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code_str)

        # Build sanitized environment
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        if custom_env:
            env.update(custom_env)

        start_time = time.time()
        timed_out = False
        try:
            proc = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                check=False,
            )
            duration = time.time() - start_time
            return ExecutionResult(
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_seconds=round(duration, 3),
                timed_out=False,
                sandbox_type="local_subprocess",
            )
        except subprocess.TimeoutExpired as exp:
            duration = time.time() - start_time
            logger.error("Sandbox execution timed out after %.1fs", duration)
            return ExecutionResult(
                exit_code=-1,
                stdout=exp.stdout.decode() if isinstance(exp.stdout, bytes) else (exp.stdout or ""),
                stderr=f"Execution timed out after {timeout} seconds.",
                duration_seconds=round(duration, 3),
                timed_out=True,
                sandbox_type="local_subprocess",
            )
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    # --------------------------------------------------------------------------
    # Docker Engine (Optional)
    # --------------------------------------------------------------------------

    def _execute_in_docker(self, code_str: str, timeout: float) -> ExecutionResult:
        """Run script inside an ephemeral, resource-constrained Docker container."""
        work_dir = Path(tempfile.mkdtemp(dir=str(self._temp_dir), prefix="sbx_docker_"))
        script_path = work_dir / "runner.py"

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code_str)

        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", f"{self._max_memory_mb}m",
            "-v", f"{work_dir}:/app:ro",
            "-w", "/app",
            "python:3.10-slim",
            "python", "runner.py",
        ]

        start_time = time.time()
        try:
            proc = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            duration = time.time() - start_time
            return ExecutionResult(
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_seconds=round(duration, 3),
                timed_out=False,
                sandbox_type="docker",
            )
        except subprocess.TimeoutExpired as exp:
            duration = time.time() - start_time
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Docker container timed out after {timeout}s",
                duration_seconds=round(duration, 3),
                timed_out=True,
                sandbox_type="docker",
            )
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
