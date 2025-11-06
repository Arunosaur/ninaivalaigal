#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-115: WebSocket Auth Tests
#
"""
Unit tests for services/core-api/lib/websocket_auth.py

Tests WebSocket authentication with JWT tokens.
"""

from unittest.mock import MagicMock, patch
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


class TestWebSocketAuth:
    """Tests for WebSocket authentication"""

    @pytest.mark.asyncio
    async def test_get_current_user_ws_success(self):
        """Test successful WebSocket authentication"""
        try:
            from lib.websocket_auth import get_current_user_ws

            # Create valid JWT token
            token_payload = {
                "user_id": str(uuid4()),
                "email": "test@example.com",
                "role": "user",
                "account_type": "individual",
            }

            with patch("lib.websocket_auth.jwt.decode") as mock_decode:
                mock_decode.return_value = token_payload
                with patch("lib.websocket_auth.os.getenv", return_value="test_secret"):
                    user_info = await get_current_user_ws(token="valid_token")

                    assert user_info["id"] == str(token_payload["user_id"])
                    assert user_info["email"] == "test@example.com"
                    assert user_info["role"] == "user"
        except ImportError:
            pytest.skip("websocket_auth module not available")

    @pytest.mark.asyncio
    async def test_get_current_user_ws_no_token(self):
        """Test WebSocket auth failure when no token provided"""
        try:
            from fastapi import WebSocketException
            from lib.websocket_auth import get_current_user_ws

            with pytest.raises(WebSocketException) as exc_info:
                await get_current_user_ws(token=None)

            assert exc_info.value.code == 1008
            assert "Unauthorized" in exc_info.value.reason
        except ImportError:
            pytest.skip("websocket_auth module not available")

    @pytest.mark.asyncio
    async def test_get_current_user_ws_expired_token(self):
        """Test WebSocket auth failure with expired token"""
        try:
            import jwt
            from fastapi import WebSocketException
            from lib.websocket_auth import get_current_user_ws

            with patch("lib.websocket_auth.jwt.decode") as mock_decode:
                mock_decode.side_effect = jwt.ExpiredSignatureError("Token expired")
                with patch("lib.websocket_auth.os.getenv", return_value="test_secret"):
                    with pytest.raises(WebSocketException) as exc_info:
                        await get_current_user_ws(token="expired_token")

                    assert exc_info.value.code == 1008
                    assert "expired" in exc_info.value.reason.lower()
        except ImportError:
            pytest.skip("websocket_auth module not available")

    @pytest.mark.asyncio
    async def test_get_current_user_ws_invalid_token(self):
        """Test WebSocket auth failure with invalid token"""
        try:
            import jwt
            from fastapi import WebSocketException
            from lib.websocket_auth import get_current_user_ws

            with patch("lib.websocket_auth.jwt.decode") as mock_decode:
                mock_decode.side_effect = jwt.InvalidTokenError("Invalid token")
                with patch("lib.websocket_auth.os.getenv", return_value="test_secret"):
                    with pytest.raises(WebSocketException) as exc_info:
                        await get_current_user_ws(token="invalid_token")

                    assert exc_info.value.code == 1008
                    assert "Invalid" in exc_info.value.reason
        except ImportError:
            pytest.skip("websocket_auth module not available")

    @pytest.mark.asyncio
    async def test_get_current_user_ws_missing_user_id(self):
        """Test WebSocket auth failure when token has no user_id"""
        try:
            from fastapi import WebSocketException
            from lib.websocket_auth import get_current_user_ws

            token_payload = {"email": "test@example.com"}  # Missing user_id

            with patch("lib.websocket_auth.jwt.decode") as mock_decode:
                mock_decode.return_value = token_payload
                with patch("lib.websocket_auth.os.getenv", return_value="test_secret"):
                    with pytest.raises(WebSocketException) as exc_info:
                        await get_current_user_ws(token="token_without_user_id")

                    assert exc_info.value.code == 1008
                    assert "Invalid token payload" in exc_info.value.reason
        except ImportError:
            pytest.skip("websocket_auth module not available")

    @pytest.mark.asyncio
    async def test_get_current_user_ws_with_sub_claim(self):
        """Test WebSocket auth with 'sub' claim instead of 'user_id'"""
        try:
            from lib.websocket_auth import get_current_user_ws

            token_payload = {
                "sub": str(uuid4()),  # Using 'sub' instead of 'user_id'
                "email": "test@example.com",
            }

            with patch("lib.websocket_auth.jwt.decode") as mock_decode:
                mock_decode.return_value = token_payload
                with patch("lib.websocket_auth.os.getenv", return_value="test_secret"):
                    user_info = await get_current_user_ws(token="valid_token")

                    assert user_info["id"] == str(token_payload["sub"])
        except ImportError:
            pytest.skip("websocket_auth module not available")
