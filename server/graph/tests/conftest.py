import pytest
from fastapi.testclient import TestClient

from server.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)
