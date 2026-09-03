"""Template: FastAPI service skeleton (raw). Placeholders are substituted by PythonApiGenerator."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

__MODULE_NAME__app = FastAPI(title="__MODULE_NAME__")


class __MODEL_NAME__Request(BaseModel):
    __FIELDS__


@app.get("/api/v1/__ROUTE__")
def list_items() -> dict:
    """Return a stub listing for the __MODULE_NAME__ resource."""
    return {"service": "__MODULE_NAME__", "items": []}


@app.get("/healthz")
def healthz() -> dict:
    """Liveness probe used by the orchestrator and Kubernetes."""
    return {"status": "ok"}