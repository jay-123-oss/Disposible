"""Base classes and safety classifications for the Central Tool System.

Enforces:
- Command policies: SAFE, CAUTION, DANGEROUS
- Standardized observation and execution results
- Tool invocation logging and duration tracking
"""

from __future__ import annotations

import abc
import enum
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AIhenge.ToolSystem")


class SafetyLevel(str, enum.Enum):
    """Safety classification for tool invocations."""
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    DANGEROUS = "DANGEROUS"


@dataclass
class ToolResult:
    """Standardized result and observation returned by all tools."""
    success: bool
    output: Any
    error: Optional[str] = None
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    safety_level: SafetyLevel = SafetyLevel.SAFE
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_observation(self) -> Dict[str, Any]:
        """Convert result into closed-loop agent observation payload."""
        return {
            "status": "success" if self.success else "failed",
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": round(self.duration_seconds, 3),
            "safety_level": self.safety_level.value,
            "metadata": self.metadata,
        }


class BaseTool(abc.ABC):
    """Abstract base class for all engineering tools."""

    name: str = "base_tool"
    description: str = ""
    safety_level: SafetyLevel = SafetyLevel.SAFE

    def execute(self, **kwargs: Any) -> ToolResult:
        """Wrapped execution with duration tracking and observation logging."""
        start_time = time.time()
        logger.info("Invoking tool '%s' with args: %s", self.name, {k: str(v)[:100] for k, v in kwargs.items()})
        try:
            result = self._run(**kwargs)
            result.duration_seconds = time.time() - start_time
            return result
        except Exception as ex:
            duration = time.time() - start_time
            logger.error("Tool '%s' failed after %.2fs: %s", self.name, duration, ex)
            return ToolResult(
                success=False,
                output=None,
                error=str(ex),
                exit_code=1,
                stderr=str(ex),
                duration_seconds=duration,
                safety_level=self.safety_level,
            )

    @abc.abstractmethod
    def _run(self, **kwargs: Any) -> ToolResult:
        """Subclasses implement specific tool logic here."""
        raise NotImplementedError
