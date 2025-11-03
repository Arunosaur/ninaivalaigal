#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Integration tests for Context Sharing Audit Trail (US-94)

Tests audit logging for context sharing operations.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.contexts.audit_logger import ContextSharingAuditLogger, SharingAction


@pytest.fixture
async def mock_db_pool():
    """Mock database connection pool"""
    pool = AsyncMock()
    conn = AsyncMock()
    pool.acquire = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn), __aexit__=AsyncMock()))
    conn.execute = AsyncMock(return_value="INSERT 0 1")
    conn.fetch = AsyncMock(return_value=[])
    return pool


@pytest.fixture
async def audit_logger(mock_db_pool):
    """Create audit logger instance"""
    logger = ContextSharingAuditLogger(mock_db_pool, retention_days=90)
    return logger


@pytest.mark.asyncio
async def test_log_share(audit_logger, mock_db_pool):
    """Test logging context share event"""
    await audit_logger.log_share(
        context_id=1,
        actor_user_id=10,
        target_user_id=20,
        permission_level="read",
        ip_address="192.168.1.1",
        user_agent="test-agent",
    )

    # Verify database call was made
    assert mock_db_pool.acquire.called


@pytest.mark.asyncio
async def test_log_unshare(audit_logger, mock_db_pool):
    """Test logging context unshare event"""
    await audit_logger.log_unshare(
        context_id=1,
        actor_user_id=10,
        target_user_id=20,
        ip_address="192.168.1.1",
    )

    assert mock_db_pool.acquire.called


@pytest.mark.asyncio
async def test_log_permission_change(audit_logger, mock_db_pool):
    """Test logging permission change event"""
    await audit_logger.log_permission_change(
        context_id=1,
        actor_user_id=10,
        target_user_id=20,
        old_permission="read",
        new_permission="write",
        ip_address="192.168.1.1",
    )

    assert mock_db_pool.acquire.called


@pytest.mark.asyncio
async def test_log_access_attempt_granted(audit_logger, mock_db_pool):
    """Test logging granted access attempt"""
    await audit_logger.log_access_attempt(
        context_id=1,
        user_id=10,
        granted=True,
        ip_address="192.168.1.1",
        user_agent="test-agent",
    )

    assert mock_db_pool.acquire.called


@pytest.mark.asyncio
async def test_log_access_attempt_denied(audit_logger, mock_db_pool):
    """Test logging denied access attempt"""
    await audit_logger.log_access_attempt(
        context_id=1,
        user_id=10,
        granted=False,
        ip_address="192.168.1.1",
        error_message="Permission denied",
    )

    assert mock_db_pool.acquire.called


@pytest.mark.asyncio
async def test_get_audit_logs(audit_logger, mock_db_pool):
    """Test querying audit logs"""
    # Mock database response
    mock_rows = [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "context_id": 1,
            "action": "shared",
            "actor_user_id": 10,
            "target_user_id": 20,
            "target_team_id": None,
            "target_organization_id": None,
            "old_permission": None,
            "new_permission": "read",
            "timestamp": datetime.now(timezone.utc),
            "ip_address": "192.168.1.1",
            "user_agent": "test-agent",
            "success": True,
            "error_message": None,
            "metadata": {},
        }
    ]

    async def mock_fetch(query, *params):
        return mock_rows

    conn = await mock_db_pool.acquire().__aenter__()
    conn.fetch = AsyncMock(side_effect=mock_fetch)

    logs = await audit_logger.get_audit_logs(
        context_id=1,
        limit=10,
    )

    assert len(logs) > 0
    assert logs[0]["action"] == "shared"


@pytest.mark.asyncio
async def test_cleanup_old_logs(audit_logger, mock_db_pool):
    """Test cleanup of old audit logs"""
    conn = await mock_db_pool.acquire().__aenter__()
    conn.execute = AsyncMock(return_value="DELETE 5")

    await audit_logger._cleanup_old_logs()

    assert conn.execute.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
