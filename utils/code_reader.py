"""CodeReader utility: reads local Python files and prepares embeddable source code for notebooks."""

from __future__ import annotations

import os
from typing import Dict


def read_file_content(relative_path: str) -> str:
    """Read source code from relative file path or fallback to embedded template."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    full_path = os.path.join(root_dir, relative_path)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    return f"# File not found: {relative_path}\n"


def get_all_agents_code() -> Dict[str, str]:
    """Read all 6 agent implementation files."""
    agent_files = {
        "coding": "agents/coding_agent.py",
        "testing": "agents/testing_agent.py",
        "security": "agents/security_agent.py",
        "quality": "agents/quality_agent.py",
        "infrastructure": "agents/infrastructure_agent.py",
        "embedding": "agents/embedding_agent.py",
    }
    return {k: read_file_content(path) for k, path in agent_files.items()}


def get_orchestrator_code() -> str:
    """Read orchestrator.py code."""
    return read_file_content("orchestrator.py")


def get_server_code() -> str:
    """Read server.py code."""
    return read_file_content("server.py")
