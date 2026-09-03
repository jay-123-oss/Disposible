"""UAT test case definitions and scenario suites."""

import json
from pathlib import Path
from typing import Any, Dict

CASE_DIR = Path(__file__).parent


def load_test_cases(filename: str) -> Dict[str, Any]:
    """Load JSON test case suite from test_cases directory."""
    with open(CASE_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


__all__ = ["load_test_cases"]
