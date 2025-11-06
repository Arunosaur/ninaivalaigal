#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Tests for WebSocket Authentication - SPEC-115

Tests for US#743 and US#792: WebSocket authentication with token validation.
"""

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket, WebSocketException

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    import jwt

    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    # Mock jwt for testing if not available
    jwt = MagicMock()

from lib.websocket_auth import (
    authenticate_websocket,
    extract_token_from_websocket,
    get_current_user_ws,
)


class TestExtractTokenFromWebSocket:
    """Tests for token extraction from WebSocket"""

    @pytest.mark.asyncio
    async def test_extract_token_from_query_param(self):
        """Test extracting token from query parameter"""
        websocket = MagicMock(spec=WebSocket)
        websocket.query_params = {"token": "test_token_123"}
        websocket.headers = {}

        token = await extract_token_from_websocket(websocket)
        assert token == "test_token_123"

    @pytest.mark.asyncio
    async def test_extract_token_from_authorization_header(self):
        """Test extracting token from Authorization header"""
        websocket = MagicMock(spec=WebSocket)
        websocket.query_params = {}
        websocket.headers = {"authorization": "Bearer test_token_456"}

        token = await extract_token_from_websocket(websocket)
        assert token == "test_token_456"

    @pytest.mark.asyncio
    async def test_extract_token_prefers_query_over_header(self):
        """Test that query parameter is preferred over header"""
        websocket = MagicMock(spec=WebSocket)
        websocket.query_params = {"token": "query_token"}
        websocket.headers = {"authorization": "Bearer header_token"}

        token = await extract_token_from_websocket(websocket)
        assert token == "query_token"

    @pytest.mark.asyncio
    async def test_extract_token_none_when_missing(self):
        """Test that None is returned when no token is provided"""
        websocket = MagicMock(spec=WebSocket)
        websocket.query_params = {}
        websocket.headers = {}

        token = await extract_token_from_websocket(websocket)
        assert token is None


class TestGetCurrentUserWS:
    """Tests for WebSocket user authentication"""

    @pytest.fixture
    def valid_token(self):
        """Create a valid JWT token for testing"""
        payload = {
            "user_id": "test_user_123",
            "email": "test@example.com",
            "role": "member",
            "account_type": "individual",
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        secret = "test_secret_key"
        return jwt.encode(payload, secret, algorithm="HS256")

    @pytest.fixture
    def expired_token(self):
        """Create an expired JWT token for testing"""
        if JWT_AVAILABLE:
            payload = {
                "user_id": "test_user_123",
                "email": "test@example.com",
                "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
            }
            secret = "test_secret_key"
            return jwt.encode(payload, secret, algorithm="HS256")
        else:
            # Return mock expired token if JWT not available
            return "mock_expired_token_123"

    @pytest.mark.asyncio
    async def test_get_current_user_ws_valid_token(self, valid_token):
        """Test authentication with valid token"""
        with patch.dict(os.environ, {"NINAIVALAIGAL_JWT_SECRET": "test_secret_key"}):
            user = await get_current_user_ws(valid_token)

            assert user["id"] == "test_user_123"
            assert user["email"] == "test@example.com"
            assert user["role"] == "member"
            assert user["account_type"] == "individual"

    @pytest.mark.asyncio
    async def test_get_current_user_ws_expired_token(self, expired_token):
        """Test authentication with expired token"""
        with patch.dict(os.environ, {"NINAIVALAIGAL_JWT_SECRET": "test_secret_key"}):
            with pytest.raises(WebSocketException) as exc_info:
                await get_current_user_ws(expired_token)

            assert exc_info.value.code == 1008
            assert "expired" in exc_info.value.reason.lower()

    @pytest.mark.asyncio
    async def test_get_current_user_ws_invalid_token(self):
        """Test authentication with invalid token"""
        with patch.dict(os.environ, {"NINAIVALAIGAL_JWT_SECRET": "test_secret_key"}):
            with pytest.raises(WebSocketException) as exc_info:
                await get_current_user_ws("invalid_token_string")

            assert exc_info.value.code == 1008
            assert "invalid" in exc_info.value.reason.lower()

    @pytest.mark.asyncio
    async def test_get_current_user_ws_no_token(self):
        """Test authentication without token"""
        with pytest.raises(WebSocketException) as exc_info:
            await get_current_user_ws(None)

        assert exc_info.value.code == 1008
        assert "no token" in exc_info.value.reason.lower()

    @pytest.mark.asyncio
    async def test_get_current_user_ws_token_without_user_id(self):
        """Test authentication with token missing user_id"""
        if JWT_AVAILABLE:
            payload = {
                "email": "test@example.com",
                "exp": datetime.utcnow() + timedelta(hours=1),
            }
            secret = "test_secret_key"
            token = jwt.encode(payload, secret, algorithm="HS256")
        else:
            token = "mock_token_without_user_id"

        with patch.dict(os.environ, {"NINAIVALAIGAL_JWT_SECRET": "test_secret_key"}):
            with pytest.raises(WebSocketException) as exc_info:
                await get_current_user_ws(token)

            assert exc_info.value.code == 1008
            if JWT_AVAILABLE:
                assert "invalid token payload" in exc_info.value.reason.lower()


class TestAuthenticateWebSocket:
    """Tests for full WebSocket authentication flow"""

    @pytest.fixture
    def valid_token(self):
        """Create a valid JWT token for testing"""
        payload = {
            "user_id": "test_user_123",
            "email": "test@example.com",
            "role": "member",
            "account_type": "individual",
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        secret = "test_secret_key"
        return jwt.encode(payload, secret, algorithm="HS256")

    @pytest.mark.asyncio
    async def test_authenticate_websocket_success(self, valid_token):
        """Test successful WebSocket authentication"""
        websocket = MagicMock(spec=WebSocket)
        websocket.query_params = {"token": valid_token}
        websocket.headers = {}

        with patch.dict(os.environ, {"NINAIVALAIGAL_JWT_SECRET": "test_secret_key"}):
            user = await authenticate_websocket(websocket)

            assert user["id"] == "test_user_123"
            assert user["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_websocket_no_token(self):
        """Test WebSocket authentication without token"""
        websocket = MagicMock(spec=WebSocket)
        websocket.query_params = {}
        websocket.headers = {}

        with pytest.raises(WebSocketException) as exc_info:
            await authenticate_websocket(websocket)

        assert exc_info.value.code == 1008

    @pytest.mark.asyncio
    async def test_authenticate_websocket_invalid_token(self):
        """Test WebSocket authentication with invalid token"""
        websocket = MagicMock(spec=WebSocket)
        websocket.query_params = {"token": "invalid_token"}
        websocket.headers = {}

        with patch.dict(os.environ, {"NINAIVALAIGAL_JWT_SECRET": "test_secret_key"}):
            with pytest.raises(WebSocketException) as exc_info:
                await authenticate_websocket(websocket)

            assert exc_info.value.code == 1008
