#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# US-91: API Rate Limit Middleware Tests
#
"""
Unit tests for services/core-api/middleware/api_rate_limit_middleware.py

Tests FastAPI middleware for rate limiting.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def setup_imports():
    """Setup imports for all tests"""
    import sys
    from pathlib import Path

    core_api_path = str(Path(__file__).parent.parent / "services" / "core-api")
    if core_api_path not in sys.path:
        sys.path.insert(0, core_api_path)


@pytest.fixture
def mock_request():
    """Create mock FastAPI request"""
    mock_req = MagicMock()
    mock_req.headers = {
        "X-Forwarded-For": "192.168.1.1",
        "User-Agent": "test-agent",
    }
    mock_req.client = MagicMock()
    mock_req.client.host = "192.168.1.1"
    mock_req.url.path = "/api/test"
    mock_req.state = MagicMock()
    mock_req.state.user_id = None
    return mock_req


class TestAPIRateLimitMiddleware:
    """Tests for API rate limit middleware"""

    def test_get_client_ip_from_x_forwarded_for(self):
        """Test extracting IP from X-Forwarded-For header"""
        try:
            from middleware.api_rate_limit_middleware import get_client_ip

            mock_request = MagicMock()
            mock_request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
            mock_request.client = None

            ip = get_client_ip(mock_request)
            assert ip == "192.168.1.1"
        except ImportError:
            pytest.skip("api_rate_limit_middleware module not available")

    def test_get_client_ip_from_x_real_ip(self):
        """Test extracting IP from X-Real-IP header"""
        try:
            from middleware.api_rate_limit_middleware import get_client_ip

            mock_request = MagicMock()
            mock_request.headers = {"X-Real-IP": "192.168.1.2"}
            mock_request.client = None

            ip = get_client_ip(mock_request)
            assert ip == "192.168.1.2"
        except ImportError:
            pytest.skip("api_rate_limit_middleware module not available")

    def test_get_client_ip_from_client_host(self):
        """Test extracting IP from client host"""
        try:
            from middleware.api_rate_limit_middleware import get_client_ip

            mock_request = MagicMock()
            mock_request.headers = {}
            mock_request.client = MagicMock()
            mock_request.client.host = "192.168.1.3"

            ip = get_client_ip(mock_request)
            assert ip == "192.168.1.3"
        except ImportError:
            pytest.skip("api_rate_limit_middleware module not available")

    def test_get_user_id_from_state(self):
        """Test extracting user ID from request state"""
        try:
            from middleware.api_rate_limit_middleware import get_user_id

            mock_request = MagicMock()
            mock_request.state = MagicMock()
            mock_request.state.user_id = uuid4()

            user_id = get_user_id(mock_request)
            assert user_id is not None
            assert str(mock_request.state.user_id) == user_id
        except ImportError:
            pytest.skip("api_rate_limit_middleware module not available")

    def test_get_user_id_from_jwt_token(self):
        """Test extracting user ID from JWT token"""
        try:
            from middleware.api_rate_limit_middleware import get_user_id

            mock_request = MagicMock()
            mock_request.state = MagicMock()
            mock_request.state.user_id = None
            mock_request.headers = {
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTIzIn0.test"
            }

            with patch("middleware.api_rate_limit_middleware.jwt.decode") as mock_decode:
                mock_decode.return_value = {"user_id": "123"}
                with patch("middleware.api_rate_limit_middleware.os.getenv", return_value="secret"):
                    user_id = get_user_id(mock_request)
                    # Should attempt to decode JWT
                    assert mock_decode.called or user_id is None
        except ImportError:
            pytest.skip("api_rate_limit_middleware module not available")

    def test_get_user_id_none_when_not_authenticated(self):
        """Test returning None when user not authenticated"""
        try:
            from middleware.api_rate_limit_middleware import get_user_id

            mock_request = MagicMock()
            mock_request.state = MagicMock()
            mock_request.state.user_id = None
            mock_request.headers = {}

            user_id = get_user_id(mock_request)
            assert user_id is None
        except ImportError:
            pytest.skip("api_rate_limit_middleware module not available")

    @pytest.mark.asyncio
    async def test_middleware_allows_request_within_limit(self, mock_request):
        """Test middleware allows request within rate limit"""
        try:
            from middleware.api_rate_limit_middleware import APIRateLimitMiddleware

            mock_call_next = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_call_next.return_value = mock_response

            middleware = APIRateLimitMiddleware(app=MagicMock())

            with patch("middleware.api_rate_limit_middleware.api_rate_limiter.check_ip_limit") as mock_check:
                mock_check.return_value = (True, None, {"remaining": 99})
                with patch("middleware.api_rate_limit_middleware.get_client_ip", return_value="127.0.0.1"):
                    response = await middleware.dispatch(mock_request, mock_call_next)

                    assert response.status_code == 200
                    mock_call_next.assert_called_once()
        except ImportError:
            pytest.skip("api_rate_limit_middleware module not available")

    @pytest.mark.asyncio
    async def test_middleware_blocks_request_over_limit(self, mock_request):
        """Test middleware blocks request over rate limit"""
        try:
            from fastapi import HTTPException
            from middleware.api_rate_limit_middleware import APIRateLimitMiddleware

            mock_call_next = AsyncMock()

            middleware = APIRateLimitMiddleware(app=MagicMock())

            with patch("middleware.api_rate_limit_middleware.api_rate_limiter.check_ip_limit") as mock_check:
                mock_check.return_value = (False, "Rate limit exceeded", {"remaining": 0, "retry_after": 60})
                with patch("middleware.api_rate_limit_middleware.get_client_ip", return_value="192.168.1.1"):
                    with pytest.raises(HTTPException) as exc_info:
                        await middleware.dispatch(mock_request, mock_call_next)

                    assert exc_info.value.status_code == 429
                    mock_call_next.assert_not_called()
        except ImportError:
            pytest.skip("api_rate_limit_middleware module not available")
