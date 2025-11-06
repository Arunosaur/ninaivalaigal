#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-114: Auth Audit Tests
#
"""
Unit tests for services/core-api/lib/auth_audit.py

Tests authentication audit logging functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_request():
    """Create mock FastAPI request"""
    mock_req = MagicMock()
    mock_req.headers = {
        "X-Forwarded-For": "192.168.1.1",
        "User-Agent": "Mozilla/5.0",
    }
    mock_req.client = MagicMock()
    mock_req.client.host = "192.168.1.1"
    return mock_req


class TestAuthAuditLogging:
    """Tests for auth audit logging"""

    @pytest.mark.asyncio
    async def test_log_auth_event_login_success(self, mock_request):
        """Test logging successful login event"""
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "core-api"))
        from lib.auth_audit import log_auth_event

        user_id = str(uuid4())

        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "core-api"))
        with patch("lib.auth_audit.logger") as mock_logger:
            await log_auth_event(
                request=mock_request,
                user_id=user_id,
                action="login",
                success=True,
            )

            # Verify logger was called
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "AUTH_AUDIT" in str(call_args)
            assert "login" in str(call_args)

    @pytest.mark.asyncio
    async def test_log_auth_event_login_failure(self, mock_request):
        """Test logging failed login event"""
        try:
            from lib.auth_audit import log_auth_event
        except ImportError:
            pytest.skip("auth_audit module not available")

        with patch("lib.auth_audit.logger") as mock_logger:
            await log_auth_event(
                request=mock_request,
                user_id=None,
                action="login",
                success=False,
                details={"reason": "invalid_credentials"},
            )

            # Verify logger was called with warning
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert "AUTH_AUDIT" in str(call_args)
            assert "login" in str(call_args)

    @pytest.mark.asyncio
    async def test_log_auth_event_with_ip_address(self, mock_request):
        """Test logging with IP address extraction"""
        try:
            from lib.auth_audit import log_auth_event
        except ImportError:
            pytest.skip("auth_audit module not available")

        user_id = str(uuid4())

        with patch("lib.auth_audit.logger") as mock_logger:
            await log_auth_event(
                request=mock_request,
                user_id=user_id,
                action="logout",
                success=True,
            )

            # Verify IP address was extracted
            call_args = mock_logger.info.call_args
            assert "ip_address" in str(call_args) or "192.168.1.1" in str(call_args)

    @pytest.mark.asyncio
    async def test_log_auth_event_with_user_agent(self, mock_request):
        """Test logging with user agent"""
        try:
            from lib.auth_audit import log_auth_event
        except ImportError:
            pytest.skip("auth_audit module not available")

        user_id = str(uuid4())

        with patch("lib.auth_audit.logger") as mock_logger:
            await log_auth_event(
                request=mock_request,
                user_id=user_id,
                action="signup",
                success=True,
            )

            # Verify user agent was logged
            call_args = mock_logger.info.call_args
            assert "user_agent" in str(call_args) or "Mozilla" in str(call_args)

    @pytest.mark.asyncio
    async def test_log_auth_event_with_details(self, mock_request):
        """Test logging with additional details"""
        try:
            from lib.auth_audit import log_auth_event
        except ImportError:
            pytest.skip("auth_audit module not available")

        user_id = str(uuid4())
        details = {"method": "oauth", "provider": "google"}

        with patch("lib.auth_audit.logger") as mock_logger:
            await log_auth_event(
                request=mock_request,
                user_id=user_id,
                action="login",
                success=True,
                details=details,
            )

            # Verify details were included
            call_args = mock_logger.info.call_args
            assert "details" in str(call_args) or "oauth" in str(call_args)

    @pytest.mark.asyncio
    async def test_log_auth_event_all_actions(self, mock_request):
        """Test logging for all supported actions"""
        try:
            from lib.auth_audit import log_auth_event
        except ImportError:
            pytest.skip("auth_audit module not available")

        user_id = str(uuid4())
        actions = ["login", "logout", "signup", "refresh", "token_revoke"]

        with patch("lib.auth_audit.logger") as mock_logger:
            for action in actions:
                await log_auth_event(
                    request=mock_request,
                    user_id=user_id,
                    action=action,
                    success=True,
                )

            # Should log each action
            assert mock_logger.info.call_count == len(actions)

    @pytest.mark.asyncio
    async def test_log_auth_event_without_client(self, mock_request):
        """Test logging when request.client is None"""
        try:
            from lib.auth_audit import log_auth_event
        except ImportError:
            pytest.skip("auth_audit module not available")

        mock_request.client = None

        with patch("lib.auth_audit.logger") as mock_logger:
            await log_auth_event(
                request=mock_request,
                user_id=None,
                action="login",
                success=False,
            )

            # Should still log successfully
            mock_logger.warning.assert_called_once()
