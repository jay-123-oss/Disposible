"""Agents package initialization for the Fractal Multi-Agent System.

Exports the 6 Core Lightweight Agents for Auto-Deployment:
- CodingAgent
- TestingAgent
- SecurityAgent
- QualityAgent
- InfrastructureAgent
- EmbeddingAgent
"""

from __future__ import annotations

from agents.coding_agent import CodingAgent
from agents.testing_agent import TestingAgent
from agents.security_agent import SecurityAgent
from agents.quality_agent import QualityAgent
from agents.infrastructure_agent import InfrastructureAgent
from agents.embedding_agent import EmbeddingAgent

__all__ = [
    "CodingAgent",
    "TestingAgent",
    "SecurityAgent",
    "QualityAgent",
    "InfrastructureAgent",
    "EmbeddingAgent",
]
