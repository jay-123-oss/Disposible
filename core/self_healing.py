"""Self-Healing Engine for Antigravity IDE.

Runs test harnesses, parses exceptions and traceback line numbers,
and automatically applies patches to failing code buffers.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple


class SelfHealingEngine:
    """Automates diagnosis and recovery for syntax errors and test failures."""

    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.history: List[Dict[str, Any]] = []

    def parse_error_traceback(self, stderr_output: str) -> Dict[str, Any]:
        """Extract file names, line numbers, and error descriptions from Python/Node tracebacks."""
        diagnosis = {
            "has_error": False,
            "failing_file": None,
            "failing_line": None,
            "error_type": "UnknownError",
            "message": "",
        }

        if not stderr_output or not stderr_output.strip():
            return diagnosis

        # Python traceback matching: File "...", line X
        py_match = re.search(r'File "([^"]+)", line (\d+)(?:, in .*)?\n(?:\s+.*\n)*\s*([A-Za-z0-9_]+Error|AssertionError):\s*(.*)', stderr_output)
        if py_match:
            diagnosis["has_error"] = True
            diagnosis["failing_file"] = py_match.group(1)
            diagnosis["failing_line"] = int(py_match.group(2))
            diagnosis["error_type"] = py_match.group(3)
            diagnosis["message"] = py_match.group(4)
            return diagnosis

        # JS/Node stack trace matching: at ... (file:line:col)
        js_match = re.search(r'([A-Za-z0-9_]+Error):\s*(.*)\n\s+at (?:.* \()?([^:\n]+):(\d+):(\d+)\)?', stderr_output)
        if js_match:
            diagnosis["has_error"] = True
            diagnosis["error_type"] = js_match.group(1)
            diagnosis["message"] = js_match.group(2)
            diagnosis["failing_file"] = js_match.group(3)
            diagnosis["failing_line"] = int(js_match.group(4))
            return diagnosis

        # General error fallback
        if "Error" in stderr_output or "FAIL" in stderr_output:
            diagnosis["has_error"] = True
            diagnosis["message"] = stderr_output.splitlines()[-1] if stderr_output.splitlines() else "Test failed"

        return diagnosis

    def run_tests(self, command: str, cwd: Optional[str] = None) -> Tuple[bool, str, str]:
        """Execute test harness and capture returncode, stdout, and stderr."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or os.getcwd(),
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            passed = result.returncode == 0
            return passed, result.stdout, result.stderr
        except Exception as err:
            return False, "", str(err)

    def execute_healing_loop(
        self,
        test_command: str,
        files_dict: Dict[str, str],
        fix_callback: Optional[Callable[[Dict[str, Any], Dict[str, str]], Dict[str, str]]] = None,
        cwd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run iterative test-fix cycle up to max_iterations."""
        iteration = 0
        current_files = dict(files_dict)

        while iteration < self.max_iterations:
            iteration += 1
            passed, stdout, stderr = self.run_tests(test_command, cwd=cwd)

            log_entry = {
                "iteration": iteration,
                "passed": passed,
                "stdout": stdout,
                "stderr": stderr,
            }
            self.history.append(log_entry)

            if passed:
                return {
                    "success": True,
                    "iterations": iteration,
                    "final_files": current_files,
                    "message": f"Tests passed successfully on iteration {iteration}!",
                }

            diagnosis = self.parse_error_traceback(stderr or stdout)
            if fix_callback and diagnosis["has_error"]:
                try:
                    current_files = fix_callback(diagnosis, current_files)
                except Exception as patch_err:
                    print(f"[SelfHealing] Patch callback failed: {patch_err}")

        return {
            "success": False,
            "iterations": iteration,
            "final_files": current_files,
            "message": f"Self-healing terminated after {self.max_iterations} iterations.",
        }
