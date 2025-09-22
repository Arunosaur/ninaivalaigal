import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create a test client for functional tests."""
    try:
        from server.main import app

        return TestClient(app)
    except ImportError:
        pytest.skip("Server main module not available for functional testing")
