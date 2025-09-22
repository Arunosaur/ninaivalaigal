import pytest


@pytest.fixture
def mock_user():
    return {"id": 1, "name": "Test User"}
