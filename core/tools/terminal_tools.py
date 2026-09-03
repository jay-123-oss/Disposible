"""Terminal and subprocess execution tools with Command Safety Policy."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from core.tools.base import BaseTool, SafetyLevel, ToolResult


class CommandPolicy:
    """Classifies commands into SAFE, CAUTION, and DANGEROUS tiers."""

    DANGEROUS_PATTERNS = [
        r"\brm\s+-(rf|fr|r)\b",
        r"\bdel\s+/[sfq]\b",
        r"\bformat\s+[a-z]:",
        r"\bmkfs\b",
        r"\bdrop\s+(table|database|schema)\b",
        r"\bshutdown\b",
        r"\breboot\b",
        r":\(\)\{\s*:\|:&\s*\};:",  # fork bomb
    ]

    SAFE_PREFIXES = [
        "ls", "dir", "git status", "git diff", "git log", "git branch",
        "pytest", "python -m pytest", "npm test", "echo", "pwd", "whoami",
        "python --version", "node --version", "pip list", "npm list"
    ]

    @classmethod
    def evaluate(cls, command: str) -> Tuple[SafetyLevel, Optional[str]]:
        cmd = command.strip().lower()
        for pat in cls.DANGEROUS_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return SafetyLevel.DANGEROUS, f"Matches dangerous command signature: {pat}"

        for safe in cls.SAFE_PREFIXES:
            if cmd == safe or cmd.startswith(safe + " "):
                return SafetyLevel.SAFE, None

        return SafetyLevel.CAUTION, None


class RunCommandTool(BaseTool):
    name = "run_command"
    description = "Execute a shell command with safety policy validation and resource bounds."
    safety_level = SafetyLevel.CAUTION

    def _run(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: float = 30.0,
        allow_dangerous: bool = False,
    ) -> ToolResult:
        safety, reason = CommandPolicy.evaluate(command)
        if safety == SafetyLevel.DANGEROUS and not allow_dangerous:
            return ToolResult(
                success=False,
                output=None,
                error=f"Command blocked by safety policy: {reason}",
                exit_code=126,
                safety_level=SafetyLevel.DANGEROUS,
            )

        work_dir = os.path.abspath(cwd or os.getcwd())
        try:
            start = time.time()
            proc = subprocess.run(
                command,
                cwd=work_dir,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            duration = time.time() - start
            return ToolResult(
                success=proc.returncode == 0,
                output={"stdout": proc.stdout, "stderr": proc.stderr, "exit_code": proc.returncode},
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_seconds=duration,
                safety_level=safety,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output=None,
                error=f"Command timed out after {timeout} seconds",
                exit_code=124,
                safety_level=safety,
            )
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e), exit_code=1, safety_level=safety)


class RunPythonTool(BaseTool):
    name = "run_python"
    description = "Execute a Python script or inline snippet in the current environment."
    safety_level = SafetyLevel.SAFE

    def _run(self, code_or_script: str, is_file: bool = False, timeout: float = 30.0) -> ToolResult:
        python_bin = sys.executable
        if is_file:
            cmd = f'"{python_bin}" "{code_or_script}"'
        else:
            cmd = f'"{python_bin}" -c {shlex.quote(code_or_script)}'

        tool = RunCommandTool()
        return tool.execute(command=cmd, timeout=timeout)


class RunTestsTool(BaseTool):
    name = "run_tests"
    description = "Run automated test suite (pytest by default) with targeted or full scope."
    safety_level = SafetyLevel.SAFE

    def _run(self, target_path: Optional[str] = None, test_path: Optional[str] = None, timeout: float = 60.0) -> ToolResult:
        python_bin = sys.executable
        actual_target = target_path or test_path
        target = f'"{actual_target}"' if actual_target else ""
        cmd = f'"{python_bin}" -m pytest {target} -v'
        res = RunCommandTool().execute(command=cmd, timeout=timeout)

        # Parse test metrics from stdout
        passed = len(re.findall(r"PASSED", res.stdout))
        failed = len(re.findall(r"FAILED", res.stdout))

        res.metadata["passed_count"] = passed
        res.metadata["failed_count"] = failed
        res.metadata["test_type"] = "targeted" if target_path else "full_suite"
        return res
