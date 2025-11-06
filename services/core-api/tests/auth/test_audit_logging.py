# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""Unit tests for authentication audit logging (SPEC-114)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from lib.auth_audit import (
    log_auth_event,
    log_login_attempt,
    log_logout,
    log_rate_limit_exceeded,
    log_signup_attempt,
    log_token_refresh,
)


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request object."""
    request = MagicMock()
    request.headers = {
        "X-Forwarded-For": "192.168.1.1",
        "User-Agent": "Mozilla/5.0",
    }
    request.client = MagicMock()
    request.client.host = "192.168.1.1"
    return request


@pytest.mark.asyncio
class TestAuthAuditLogging:
    """Test authentication audit logging functions."""

    async def test_log_auth_event_success(self, mock_request):
        """Test logging a successful auth event."""
        with patch("lib.auth_audit.logger") as mock_logger:
            await log_auth_event(
                request=mock_request,
                user_id="user123",
                action="login",
                success=True,
                details={"email": "test@example.com"},
            )

            # Verify logger.info was called
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "AUTH_AUDIT: login" in call_args[0][0]
            assert call_args[1]["user_id"] == "user123"
            assert call_args[1]["success"] is True
            assert call_args[1]["ip_address"] == "192.168.1.1"
            assert call_args[1]["user_agent"] == "Mozilla/5.0"

    async def test_log_auth_event_failure(self, mock_request):
        """Test logging a failed auth event."""
        with patch("lib.auth_audit.logger") as mock_logger:
            await log_auth_event(
                request=mock_request,
                user_id=None,
                action="login",
                success=False,
                details={"error_reason": "invalid_password"},
            )

            # Verify logger.warning was called for failed events
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert "AUTH_AUDIT: login failed" in call_args[0][0]
            assert call_args[1]["success"] is False

    async def test_log_login_attempt_success(self, mock_request):
        """Test logging a successful login attempt."""
        with patch("lib.auth_audit.log_auth_event") as mock_log:
            await log_login_attempt(
                request=mock_request,
                email="test@example.com",
                success=True,
                user_id="user123",
            )

            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs["action"] == "login"
            assert call_kwargs["success"] is True
            assert call_kwargs["user_id"] == "user123"
            assert call_kwargs["details"]["email"] == "test@example.com"

    async def test_log_login_attempt_failure(self, mock_request):
        """Test logging a failed login attempt."""
        with patch("lib.auth_audit.log_auth_event") as mock_log:
            await log_login_attempt(
                request=mock_request,
                email="test@example.com",
                success=False,
                error_reason="invalid_password",
            )

            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs["action"] == "login"
            assert call_kwargs["success"] is False
            assert call_kwargs["details"]["error_reason"] == "invalid_password"

    async def test_log_signup_attempt_success(self, mock_request):
        """Test logging a successful signup attempt."""
        with patch("lib.auth_audit.log_auth_event") as mock_log:
            await log_signup_attempt(
                request=mock_request,
                email="new@example.com",
                success=True,
                user_id="user456",
            )

            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs["action"] == "signup"
            assert call_kwargs["success"] is True
            assert call_kwargs["user_id"] == "user456"

    async def test_log_signup_attempt_failure(self, mock_request):
        """Test logging a failed signup attempt."""
        with patch("lib.auth_audit.log_auth_event") as mock_log:
            await log_signup_attempt(
                request=mock_request,
                email="existing@example.com",
                success=False,
                error_reason="user_already_exists",
            )

            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs["action"] == "signup"
            assert call_kwargs["success"] is False

    async def test_log_logout(self, mock_request):
        """Test logging a logout event."""
        with patch("lib.auth_audit.log_auth_event") as mock_log:
            await log_logout(
                request=mock_request,
                user_id="user123",
                success=True,
            )

            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs["action"] == "logout"
            assert call_kwargs["success"] is True
            assert call_kwargs["user_id"] == "user123"

    async def test_log_token_refresh(self, mock_request):
        """Test logging a token refresh event."""
        with patch("lib.auth_audit.log_auth_event") as mock_log:
            await log_token_refresh(
                request=mock_request,
                user_id="user123",
                success=True,
            )

            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs["action"] == "token_refresh"
            assert call_kwargs["success"] is True

    async def test_log_rate_limit_exceeded(self, mock_request):
        """Test logging a rate limit exceeded event."""
        with patch("lib.auth_audit.log_auth_event") as mock_log:
            await log_rate_limit_exceeded(
                request=mock_request,
                endpoint="login",
                identifier="192.168.1.1:test@example.com",
            )

            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs["action"] == "rate_limit_exceeded"
            assert call_kwargs["success"] is False
            assert call_kwargs["user_id"] is None
            assert call_kwargs["details"]["endpoint"] == "login"
            assert call_kwargs["details"]["identifier"] == "192.168.1.1:test@example.com"

    async def test_ip_extraction_from_headers(self):
        """Test IP extraction from various header sources."""
        # Test X-Forwarded-For
        request1 = MagicMock()
        request1.headers = {"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}
        request1.client = None

        with patch("lib.auth_audit.logger") as mock_logger:
            await log_auth_event(
                request=request1,
                user_id="user123",
                action="test",
                success=True,
            )

            call_args = mock_logger.info.call_args[1]
            assert call_args["ip_address"] == "10.0.0.1"  # First IP from X-Forwarded-For

        # Test X-Real-IP
        request2 = MagicMock()
        request2.headers = {"X-Real-IP": "192.168.1.2"}
        request2.client = None

        with patch("lib.auth_audit.logger") as mock_logger:
            await log_auth_event(
                request=request2,
                user_id="user123",
                action="test",
                success=True,
            )

            call_args = mock_logger.info.call_args[1]
            assert call_args["ip_address"] == "192.168.1.2"

        # Test fallback to client.host
        request3 = MagicMock()
        request3.headers = {}
        request3.client = MagicMock()
        request3.client.host = "192.168.1.3"

        with patch("lib.auth_audit.logger") as mock_logger:
            await log_auth_event(
                request=request3,
                user_id="user123",
                action="test",
                success=True,
            )

            call_args = mock_logger.info.call_args[1]
            assert call_args["ip_address"] == "192.168.1.3"

    async def test_audit_logging_does_not_fail_request(self, mock_request):
        """Test that audit logging failures don't break the request."""
        with patch("lib.auth_audit.logger") as mock_logger:
            # Make logger.info raise an exception
            mock_logger.info.side_effect = Exception("Logging failed")

            # Should not raise exception
            await log_auth_event(
                request=mock_request,
                user_id="user123",
                action="test",
                success=True,
            )

            # Should log the error instead
            mock_logger.error.assert_called_once()
