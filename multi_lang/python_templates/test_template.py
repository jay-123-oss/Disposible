"""Template: pytest unit tests (raw). Placeholders are substituted by PythonTestGenerator."""
import pytest
from fastapi.testclient import TestClient

from __MODULE_NAME__ import __MODULE_NAME__app as app


@pytest.fixture
def client():
    """Provide a FastAPI test client for the generated service."""
    with TestClient(app) as test_client:
        yield test_client


def test_healthz(client) -> None:
    """Verify the liveness probe returns 200 OK."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_items(client) -> None:
    """Verify the __MODULE_NAME__ listing endpoint responds."""
    response = client.get("/api/v1/__ROUTE__")
    assert response.status_code == 200