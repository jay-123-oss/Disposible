"""Dashboards package for Production Monitoring & Support."""

import json
from pathlib import Path
from typing import Any, Dict


def load_dashboard(name: str) -> Dict[str, Any]:
    """Load JSON dashboard definition by file name."""
    dashboard_path = Path(__file__).parent / f"{name}.json"
    if not dashboard_path.exists():
        dashboard_path = Path(__file__).parent / name
    with open(dashboard_path, "r", encoding="utf-8") as f:
        return json.load(f)
