"""conftest module."""

import pytest
from fastapi.testclient import TestClient

from server.main import app


@pytest.fixture(scope="module")
def client():
    """Pytest fixture providing FastAPI test client."""
    return TestClient(app)
