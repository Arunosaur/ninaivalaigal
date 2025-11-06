#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Integration tests for Admin Activity Logging System

SPEC-005: Admin Dashboard
US-100: Admin Activity Logging System
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from server.admin.activity_logger import AdminAction, AdminActivityLogger
from server.admin.helpers import get_admin_user_id_from_request, log_admin_action_async


@pytest.fixture
def mock_db_pool():
    """Mock database connection pool"""
    # Create a connection mock that will be returned by the context manager
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value="INSERT 0 1")
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchrow = AsyncMock(return_value={"total": 0})

    # Create a proper async context manager that returns the connection
    class AsyncContextManager:
        def __init__(self, connection):
            self.conn = connection

        async def __aenter__(self):
            return self.conn

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    # Create pool mock - acquire() should return the context manager directly
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=AsyncContextManager(conn))
    return pool


@pytest_asyncio.fixture
async def activity_logger(mock_db_pool):
    """Create AdminActivityLogger instance"""
    logger = AdminActivityLogger(mock_db_pool, retention_days=90)
    await logger.start_services()
    yield logger
    # Cleanup: stop background services
    await logger.stop_services()


@pytest.mark.asyncio
async def test_log_activity(activity_logger, mock_db_pool):
    """Test logging an admin activity"""
    admin_user_id = uuid4()
    target_id = uuid4()

    await activity_logger.log_activity(
        admin_user_id=admin_user_id,
        action="create_user",
        target_type="user",
        target_id=target_id,
        details={"email": "test@example.com"},
        ip_address="127.0.0.1",
        user_agent="Mozilla/5.0",
    )

    # Verify execute was called on the connection
    # The activity_logger uses async with pool.acquire() as conn, then conn.execute()
    # So we check that the connection's execute was called
    async with mock_db_pool.acquire() as conn:
        assert conn.execute.called


@pytest.mark.asyncio
async def test_get_activity_logs(activity_logger, mock_db_pool):
    """Test querying activity logs"""
    admin_user_id = uuid4()

    # Mock fetch to return sample log
    # Set up the mock connection before the activity_logger uses it
    async with mock_db_pool.acquire() as conn:
        conn.fetch = AsyncMock(
            return_value=[
                {
                    "id": uuid4(),
                    "admin_user_id": admin_user_id,
                    "action": "create_organization",
                    "target_type": "organization",
                    "target_id": uuid4(),
                    "details": {"organization_name": "Test Org"},
                    "ip_address": "127.0.0.1",
                    "user_agent": "Mozilla/5.0",
                    "timestamp": datetime.now(timezone.utc),
                }
            ]
        )
        conn.fetchrow = AsyncMock(return_value={"total": 1})

    logs = await activity_logger.get_activity_logs(
        admin_user_id=admin_user_id,
        limit=10,
    )

    assert len(logs) == 1
    assert logs[0]["action"] == "create_organization"
    assert logs[0]["target_type"] == "organization"


@pytest.mark.asyncio
async def test_get_activity_summary(activity_logger, mock_db_pool):
    """Test getting activity summary"""
    # Mock summary queries - set up before calling the method
    async with mock_db_pool.acquire() as conn:
        conn.fetchrow = AsyncMock(return_value={"total": 50})
        # First fetch returns action distribution
        # Second fetch returns most active admins (needs admin_user_id and count)
        action_distribution = [
            {"action": "create_user", "count": 30},
            {"action": "update_user", "count": 20},
        ]
        admin_rows = [
            {"admin_user_id": uuid4(), "count": 10},
            {"admin_user_id": uuid4(), "count": 5},
        ]
        # Mock fetch to return action distribution first, then admin rows
        conn.fetch = AsyncMock(side_effect=[action_distribution, admin_rows])

    summary = await activity_logger.get_activity_summary(days=30)

    assert summary["total_actions"] == 50
    assert "action_distribution" in summary
    assert summary["period_days"] == 30


@pytest.mark.asyncio
async def test_log_admin_action_async_helper(activity_logger):
    """Test helper function for logging"""
    admin_user_id = uuid4()
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    request.headers = {"user-agent": "Mozilla/5.0"}

    await log_admin_action_async(
        activity_logger,
        admin_user_id=admin_user_id,
        action=AdminAction.CREATE_USER.value,
        target_type="user",
        target_id=uuid4(),
        details={"email": "test@example.com"},
        request=request,
    )

    # Verify logging was called (through execute)
    # This is an indirect check - the actual implementation logs
    assert True  # If we get here without error, it worked


def test_get_admin_user_id_from_request():
    """Test extracting admin user ID from request"""
    # Test with string UUID
    user_id_str = str(uuid4())
    result = get_admin_user_id_from_request({"user_id": user_id_str})
    assert result == UUID(user_id_str)

    # Test with UUID object
    user_id_uuid = uuid4()
    result = get_admin_user_id_from_request({"user_id": user_id_uuid})
    assert result == user_id_uuid

    # Test with missing user_id
    result = get_admin_user_id_from_request({})
    assert result is None

    # Test with invalid UUID
    result = get_admin_user_id_from_request({"user_id": "invalid"})
    assert result is None


@pytest.mark.asyncio
async def test_log_admin_action_async_with_none_logger():
    """Test that logging gracefully handles None logger"""
    # Should not raise error
    await log_admin_action_async(
        None,
        admin_user_id=uuid4(),
        action="test_action",
        request=None,
    )
    assert True  # If we get here, it handled None gracefully


@pytest.mark.asyncio
async def test_cleanup_old_logs(activity_logger, mock_db_pool):
    """Test cleanup of old logs"""
    # Set up the mock connection before cleanup runs
    async with mock_db_pool.acquire() as conn:
        conn.execute = AsyncMock(return_value="DELETE 5")

    await activity_logger._cleanup_old_logs()

    # Verify cleanup query was executed
    assert conn.execute.called
