"""PerformanceTester coordinating concurrency load testing and stress breakpoint discovery."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.testing.exceptions import PerformanceTestError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.Testing.PerformanceTester")


# ==============================================================================
# L5 Specialized Performance Agents
# ==============================================================================

class LoadTester(BaseAgent):
    """L5 agent generating concurrent async load testing harnesses."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("LoadTester %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        endpoint = payload.get("endpoint", "http://localhost:8000/api/v1/users")
        concurrency = payload.get("concurrency", 50)
        code = self.build_load_harness(endpoint, concurrency)
        return {"status": "COMPLETED", "code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result:
            raise PerformanceTestError("LoadTester produced empty harness code.")
        return result

    def cleanup(self) -> None:
        logger.debug("LoadTester %s cleaned up.", self.agent_id)

    def build_load_harness(self, endpoint: str, concurrency: int) -> str:
        """Generate aiohttp concurrent load tester class."""
        return (
            f"class AsyncLoadTester:\n"
            f"    def __init__(self, url='{endpoint}', concurrency={concurrency}, total_requests={concurrency * 4}):\n"
            f"        self.url = url\n"
            f"        self.concurrency = concurrency\n"
            f"        self.total_requests = total_requests\n"
            f"        self.latencies = []\n\n"
            f"    async def fetch(self, session, sem):\n"
            f"        async with sem:\n"
            f"            start = time.perf_counter()\n"
            f"            try:\n"
            f"                async with session.get(self.url) as resp:\n"
            f"                    elapsed = (time.perf_counter() - start) * 1000\n"
            f"                    self.latencies.append((resp.status, elapsed))\n"
            f"            except Exception:\n"
            f"                self.latencies.append((500, (time.perf_counter() - start) * 1000))\n\n"
            f"    async def execute(self):\n"
            f"        sem = asyncio.Semaphore(self.concurrency)\n"
            f"        async with aiohttp.ClientSession() as session:\n"
            f"            tasks = [self.fetch(session, sem) for _ in range(self.total_requests)]\n"
            f"            await asyncio.gather(*tasks)\n"
        )


class StressTester(BaseAgent):
    """L5 agent finding service saturation breakpoints and memory exhaustion limits."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("StressTester %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        endpoint = payload.get("endpoint", "http://localhost:8000/api/v1/users")
        code = self.build_stress_harness(endpoint)
        return {"status": "COMPLETED", "code": code}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "code" not in result:
            raise PerformanceTestError("StressTester produced empty harness code.")
        return result

    def cleanup(self) -> None:
        logger.debug("StressTester %s cleaned up.", self.agent_id)

    def build_stress_harness(self, endpoint: str) -> str:
        """Generate ramp-up step load harness to discover breaking points."""
        return (
            f"async def run_stress_breakpoint_discovery(url='{endpoint}'):\n"
            f"    concurrency_steps = [10, 50, 100, 250, 500]\n"
            f"    breakpoint = None\n"
            f"    for c in concurrency_steps:\n"
            f"        tester = AsyncLoadTester(url=url, concurrency=c, total_requests=c * 2)\n"
            f"        await tester.execute()\n"
            f"        error_rate = sum(1 for status, _ in tester.latencies if status >= 400) / len(tester.latencies)\n"
            f"        if error_rate > 0.05:\n"
            f"            breakpoint = c\n"
            f"            break\n"
            f"    return {{'breakpoint_concurrency': breakpoint}}\n"
        )


# ==============================================================================
# L4 PerformanceTester Agent
# ==============================================================================

class PerformanceTester(BaseAgent):
    """L4 coordinator for load, stress, and throughput benchmarking."""

    def __init__(
        self,
        name: str = "PerformanceTester",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 192,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "performance_testing",
            "load_testing",
            "stress_testing",
            "latency_profiling",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "T13_PERFORMANCE_TESTER",
        )

        self.load_tester: Optional[LoadTester] = None
        self.stress_tester: Optional[StressTester] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("run_load_tests", self.run_load_tests)
        self.register_tool("run_stress_tests", self.run_stress_tests)

    def _spawn_subagents(self) -> None:
        """Spawn LoadTester and StressTester (Rule 1 & Rule 5)."""
        logger.info("PerformanceTester %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.load_tester = self.spawn_subagent(
            LoadTester,
            name="LoadTester",
            max_depth=child_depth,
            resources_mb=128,
        )
        self.stress_tester = self.spawn_subagent(
            StressTester,
            name="StressTester",
            max_depth=child_depth,
            resources_mb=128,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("PerformanceTester %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        endpoint = payload.get("endpoint", "http://localhost:8000/api/v1/users")
        concurrency = payload.get("concurrency", 50)
        harness = self.run_load_tests(endpoint, concurrency)
        return {
            "status": "COMPLETED",
            "agent_id": self.agent_id,
            "performance_harness": harness,
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        harness = result.get("performance_harness")
        if not harness or not harness.get("full_code"):
            raise PerformanceTestError("PerformanceTester produced empty harness bundle.")
        return result

    def cleanup(self) -> None:
        logger.debug("PerformanceTester %s cleanup complete.", self.agent_id)

    def run_load_tests(self, endpoint: str, concurrency: int = 50) -> Dict[str, Any]:
        """Generate benchmark code for load execution."""
        blocks: List[str] = [
            "import time",
            "import asyncio",
            "import aiohttp",
            "",
        ]

        if self.load_tester:
            load_res = self.load_tester.process({"payload": {"endpoint": endpoint, "concurrency": concurrency}})
            blocks.append(load_res["code"])

        if self.stress_tester:
            stress_res = self.stress_tester.process({"payload": {"endpoint": endpoint}})
            blocks.append(stress_res["code"])

        full_code = "\n\n".join(blocks)
        return {
            "endpoint": endpoint,
            "concurrency": concurrency,
            "full_code": full_code,
        }

    def run_stress_tests(self, endpoint: str) -> str:
        """Generate stress breakpoint tests."""
        if self.stress_tester:
            res = self.stress_tester.process({"payload": {"endpoint": endpoint}})
            return res["code"]
        return "# Stress test placeholder"
