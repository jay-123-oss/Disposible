"""Main FastAPI application for the Web-Based GUI Dashboard Layer."""

from __future__ import annotations

import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from gui.api.routes.agents import router as agents_router
from gui.api.routes.api_tester import router as api_tester_router
from gui.api.routes.code import router as code_router
from gui.api.routes.dashboard import router as dashboard_router
from gui.api.routes.logs import router as logs_router
from gui.api.routes.performance import router as performance_router
from gui.api.routes.reports import router as reports_router
from gui.api.routes.security import router as security_router
from gui.api.routes.settings import router as settings_router
from gui.api.routes.tasks import router as tasks_router
from gui.api.routes.tests import router as tests_router
from gui.api.routes.users import router as users_router
from gui.api.websocket import ws_manager

logger = logging.getLogger("FractalCore.GUI.API")

app = FastAPI(
    title="Fractal Multi-Agent System Dashboard API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all 12 API Routers under /api/v1
API_V1_PREFIX = "/api/v1"
app.include_router(dashboard_router, prefix=API_V1_PREFIX)
app.include_router(agents_router, prefix=API_V1_PREFIX)
app.include_router(tasks_router, prefix=API_V1_PREFIX)
app.include_router(code_router, prefix=API_V1_PREFIX)
app.include_router(tests_router, prefix=API_V1_PREFIX)
app.include_router(security_router, prefix=API_V1_PREFIX)
app.include_router(performance_router, prefix=API_V1_PREFIX)
app.include_router(logs_router, prefix=API_V1_PREFIX)
app.include_router(settings_router, prefix=API_V1_PREFIX)
app.include_router(users_router, prefix=API_V1_PREFIX)
app.include_router(reports_router, prefix=API_V1_PREFIX)
app.include_router(api_tester_router, prefix=API_V1_PREFIX)

# Integrate Core Orchestrator for direct dashboard task executions
from orchestrator import Core6Orchestrator
from pydantic import BaseModel

_orchestrator = Core6Orchestrator()

class TaskReq(BaseModel):
    task: str
    agent: str = "coding"

@app.post("/run")
def run_task(req: TaskReq):
    return _orchestrator.process(task=req.task, agent_type=req.agent)

@app.post("/run-all")
def run_all_tasks(req: TaskReq):
    return _orchestrator.process_all(task=req.task)



# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time bidirectional WebSocket telemetry connection."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo heartbeat or client event
            await websocket.send_json({"type": "PONG", "received": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# Frontend static files mounting
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def get_root_index():
    """Serve frontend index HTML."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Fractal Multi-Agent System GUI Dashboard API is Online."}
