#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Test configuration and fixtures."""

import asyncio
import os
import time
from typing import Dict

import pytest

# Optional imports for integration tests
try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
except ImportError:
    create_engine = None
    sessionmaker = None
    StaticPool = None

# Import SPEC-056 fixtures
try:
    from .fixtures import *  # noqa: F401, F403
except ImportError:
    # Fallback for when running from different contexts
    import sys

    sys.path.append(os.path.dirname(__file__))
    from fixtures import *  # noqa: F401, F403


# ========================================
# CENTRALIZED TEST CONFIGURATION
# Single source of truth for API endpoints
# ========================================


@pytest.fixture(scope="session")
def api_config() -> Dict:
    """
    Centralized API configuration for all tests.

    Uses environment variables with sensible defaults:
    - TEST_API_BASE_URL: Backend API URL (default: http://localhost:13390)
    - TEST_API_TIMEOUT: Request timeout in seconds (default: 30)
    - TEST_CONCURRENT_LIMIT: Max concurrent requests (default: 50)
    """
    return {
        "base_url": os.getenv("TEST_API_BASE_URL", "http://localhost:13390"),
        "concurrent_limit": int(os.getenv("TEST_CONCURRENT_LIMIT", "50")),
        "test_timeout": int(os.getenv("TEST_API_TIMEOUT", "30")),
        "rate_limit_threshold": 100,
        "session_timeout_minutes": 30,
    }


# Test database setup (only if SQLAlchemy available)
if create_engine is not None:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    TestingSessionLocal = None


# Note: event_loop fixture override is deprecated in pytest-asyncio
# Using fixture_loop_scope instead
@pytest.fixture(scope="session")
def asyncio_event_loop_policy():
    """Set the event loop policy for the test session."""
    return asyncio.get_event_loop_policy()


@pytest.fixture
def db_session():
    """Create a test database session."""
    if engine is None:
        pytest.skip("SQLAlchemy not available")

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
    if TestClient is None:
        pytest.skip("FastAPI not available")

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
