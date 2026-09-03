"""Prompt templates loader for AI extensions."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load prompt template text by name."""
    p = PROMPTS_DIR / f"{name}.txt"
    if not p.exists():
        raise FileNotFoundError(f"Prompt template {name} not found at {p}")
    return p.read_text(encoding="utf-8")
