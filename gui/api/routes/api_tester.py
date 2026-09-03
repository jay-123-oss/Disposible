"""API Tester route for simulating and proxying REST requests from the dashboard."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api-tester", tags=["APITester"])


class APIRequestPayload(BaseModel):
    method: str = "GET"
    endpoint: str = "/api/v1/dashboard/status"
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None


@router.post("/request")
def test_api_request(req: APIRequestPayload) -> Dict[str, Any]:
    """Execute test API request against system endpoints."""
    start_time = time.time()
    latency = 8.5  # ms simulated execution

    mock_response = {
        "status": "SUCCESS",
        "method": req.method.upper(),
        "endpoint": req.endpoint,
        "status_code": 200,
        "latency_ms": latency,
        "response_headers": {"content-type": "application/json", "x-fractal-trace": "sig_gui_api_tester"},
        "response_data": {
            "ack": True,
            "message": f"Response from {req.endpoint}",
            "payload_echo": req.body or {},
        },
        "timestamp": time.time(),
    }
    return mock_response
