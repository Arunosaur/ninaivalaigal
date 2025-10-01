"""Test configuration and fixtures."""

import asyncio
import time
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import SPEC-056 fixtures
try:
    from .fixtures import *
except ImportError:
    # Fallback for when running from different contexts
    import os
    import sys

    sys.path.append(os.path.dirname(__file__))
    from fixtures import *

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def db_session():
    """Create a test database session."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create a test client."""
    from server.database import get_db
    from server.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    return {"Authorization": "Bearer test_token"}  # pragma: allowlist secret


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",  # pragma: allowlist secret
        "account_type": "individual",
    }


@pytest.fixture
def test_memory_data():
    """Test memory data."""
    return {
        "content": "Test memory content",
        "context": "test_context",
        "tags": ["test", "memory"],
        "metadata": {"source": "test"},
    }


@pytest.fixture(autouse=True, scope="function")
def paced_tests():
    """
    Add 300ms delay between smoke tests to prevent overwhelming single-worker API.
    This simulates real colleague usage instead of hammer testing.
    Only applies to smoke tests.
    """
    import os

    # Only apply pacing to smoke tests
    if "smoke" in os.environ.get("PYTEST_CURRENT_TEST", ""):
        time.sleep(0.3)
    yield
