"""Settings API routes for fetching and updating system and GUI configurations."""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/settings", tags=["Settings"])

CURRENT_SETTINGS = {
    "server": {"host": "0.0.0.0", "port": 8080, "debug": False, "workers": 4},
    "frontend": {"title": "Fractal Multi-Agent System", "theme": "dark", "auto_refresh_seconds": 5},
    "model": {"default_model": "qwen2.5-coder:3b", "temperature": 0.7, "max_tokens": 4096},
    "security": {"https_enabled": False, "rate_limit_requests": 100, "rate_limit_window_seconds": 60},
}


class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]


@router.get("")
def get_settings() -> Dict[str, Any]:
    """Get active system settings."""
    return {"status": "SUCCESS", "settings": CURRENT_SETTINGS}


@router.put("")
def update_settings(req: SettingsUpdateRequest) -> Dict[str, Any]:
    """Update system settings."""
    for k, v in req.settings.items():
        if k in CURRENT_SETTINGS and isinstance(v, dict):
            CURRENT_SETTINGS[k].update(v)
        else:
            CURRENT_SETTINGS[k] = v
    return {"status": "SUCCESS", "settings": CURRENT_SETTINGS}
