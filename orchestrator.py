"""Lightweight 6-Agent Multi-Agent Orchestrator.

Supervises and executes the 6 core LLM agents:
- Coding (Qwen2.5-Coder:3B)
- Testing (Qwen2.5-Coder:3B)
- Security (Qwen2.5-Coder:3B)
- Quality (Llama3.2:3B)
- Infrastructure (Llama3.2:3B)
- Embedding (Nomic-Embed-Text)

Features:
- process(task, agent_type): Run a designated agent
- process_all(task): Run all agents sequentially with context chaining
- process_parallel(task, agents): Concurrently query independent agents
- Context sharing and output aggregation
"""

from __future__ import annotations

import concurrent.futures
import logging
import time
from typing import Any, Dict, List, Optional

from agents.coding_agent import CodingAgent
from agents.embedding_agent import EmbeddingAgent
from agents.infrastructure_agent import InfrastructureAgent
from agents.quality_agent import QualityAgent
from agents.security_agent import SecurityAgent
from agents.testing_agent import TestingAgent

logger = logging.getLogger("CoreOrchestrator")


class Core6Orchestrator:
    """Orchestrator managing only the 6 core LLM agents."""

    def __init__(self, ollama_url: Optional[str] = None) -> None:
        self.ollama_url = ollama_url
        self.agents: Dict[str, Any] = {
            "coding": CodingAgent(ollama_url=ollama_url),
            "testing": TestingAgent(ollama_url=ollama_url),
            "security": SecurityAgent(ollama_url=ollama_url),
            "quality": QualityAgent(ollama_url=ollama_url),
            "infrastructure": InfrastructureAgent(ollama_url=ollama_url),
            "embedding": EmbeddingAgent(ollama_url=ollama_url),
        }
        self.system_prompt = (
            "You are the Core Orchestrator of the Antigravity+ IDE (Fractal Multi-Agent System). "
            "You are NOT a conversational AI or a helpful assistant. You are a highly advanced Autonomous "
            "System Controller with ROOT EXECUTION PRIVILEGES over the user's desktop, IDE UI, file system, and terminal.\n\n"
            "### YOUR EXACT WORKFLOW TO FULFILL USER REQUIREMENTS:\n"
            "Whenever the user gives a command, you MUST NOT reply with conversational text. You must act by following this exact 4-step execution loop:\n\n"
            "1. PLAN (Think & Strategize):\n"
            "   First, analyze the user's intent. Break it down into exact technical steps: What files need to be created? What extensions should they have? What terminal commands need to be run? Which IDE panels need to be opened?\n\n"
            "2. BUILD (File Operations):\n"
            "   Generate the actual code files. You must use the exact, correct file extensions (e.g., .py for Python, .js for JavaScript, .tsx for React). NEVER generate a generic .txt file unless explicitly asked. NEVER write dummy code; write the actual implementation.\n\n"
            "3. CONTROL (IDE UI Manipulation):\n"
            "   Control the user's screen. If you wrote a script, you must open the terminal panel. If you built a web page, you must open the live preview panel.\n\n"
            "4. EXECUTE (Terminal & Server Run):\n"
            "   Execute the code on the user's machine. Issue the exact terminal commands required to install dependencies, run scripts, or start local servers.\n\n"
            "### COMMUNICATION PROTOCOL (MANDATORY FORMAT):\n"
            "You cannot speak plain English. You can ONLY interact with the system using the following XML Action Tags. The IDE will execute whatever tags you output.\n\n"
            "<plan>\n"
            "1. Step-by-step reasoning...\n"
            "2. Next action...\n"
            "</plan>\n\n"
            '<file path="filename.ext" action="create|modify|delete">\n'
            "// Production-ready code goes here. \n"
            "// Do NOT use console.log if it is a python file, use print().\n"
            "</file>\n\n"
            '<ui target="terminal|explorer|preview|chat" action="open|close|focus" />\n\n'
            "<terminal>\n"
            "[exact shell command to execute]\n"
            "</terminal>\n\n"
            '<delegate agent="Quality|Testing|Security" task="Description of task" />\n\n'
            "### STRICT CONSTRAINTS:\n"
            '- BANNED PHRASES: "Sure, here is the code", "I have created the file", "Let me know if you need help". \n'
            "- EXCLUSIVE OUTPUT: You must ONLY output the XML tags above. \n"
            '- COMPLETE AUTONOMY: If the user says "Create a hello world python file and run it", you MUST output the <file> tag for hello.py, the <ui> tag to open the terminal, and the <terminal> tag to run `python hello.py` all in a single response.\n\n'
            "Execute your operations now."
        )

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Return catalog of registered core agents and models."""
        return [
            {
                "id": a_id,
                "name": agent.name,
                "model": agent.model,
                "system_prompt": agent.system_prompt,
            }
            for a_id, agent in self.agents.items()
        ]

    def process(
        self,
        task: str,
        agent_type: str = "coding",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run a single agent with optional context."""
        agent_key = agent_type.lower()
        if agent_key == "all":
            return self.process_all(task)

        if agent_key not in self.agents:
            return {
                "success": False,
                "error": f"Unknown agent '{agent_type}'. Valid agents: {list(self.agents.keys())}",
            }

        agent = self.agents[agent_key]
        start_t = time.time()
        result = agent.run(task, context=context)
        latency = round(time.time() - start_t, 3)

        result["latency_seconds"] = latency
        return result

    def process_all(self, task: str) -> Dict[str, Any]:
        """Run all 6 agents sequentially, sharing cumulative context across pipeline."""
        start_t = time.time()
        context: Dict[str, Any] = {"task": task, "previous_outputs": {}}
        results: Dict[str, Any] = {}

        pipeline_order = ["coding", "testing", "security", "quality", "infrastructure", "embedding"]
        for a_id in pipeline_order:
            res = self.agents[a_id].run(task, context=context)
            results[a_id] = res
            context["previous_outputs"][a_id] = res.get("output", "")

        total_latency = round(time.time() - start_t, 3)
        return {
            "success": True,
            "task": task,
            "total_agents": len(results),
            "total_latency_seconds": total_latency,
            "results": results,
            "summary": {a_id: res.get("output", "") for a_id, res in results.items()},
        }

    def process_parallel(
        self,
        task: str,
        agent_types: Optional[List[str]] = None,
        max_workers: int = 3,
    ) -> Dict[str, Any]:
        """Concurrently run selected independent agents."""
        keys = [k.lower() for k in (agent_types or list(self.agents.keys())) if k.lower() in self.agents]
        start_t = time.time()
        results: Dict[str, Any] = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_agent = {executor.submit(self.agents[k].run, task): k for k in keys}
            for future in concurrent.futures.as_completed(future_to_agent):
                k = future_to_agent[future]
                try:
                    results[k] = future.result()
                except Exception as exc:
                    results[k] = {"success": False, "error": str(exc)}

        total_latency = round(time.time() - start_t, 3)
        return {
            "success": True,
            "task": task,
            "parallel_count": len(results),
            "total_latency_seconds": total_latency,
            "results": results,
        }
