#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
WebSocket Authentication Module - SPEC-115

Implements token-based authentication for WebSocket connections.
Used by US#743 and US#792: WebSocket authentication with token validation.
"""

import os
import sys
from typing import Any, Dict, Optional

import jwt
from fastapi import WebSocket, WebSocketException

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

logger = None
try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


async def get_current_user_ws(token: Optional[str] = None) -> Dict[str, Any]:
    """
    Authenticate WebSocket connection using JWT token.

    SPEC-115: WebSocket authentication with token validation

    Token can be provided via:
    1. Query parameter: ?token=JWT_TOKEN
    2. Header: Authorization: Bearer JWT_TOKEN
    3. WebSocket subprotocol (future enhancement)

    Args:
        token: JWT token string (optional, can be extracted from query/headers)

    Returns:
        Dictionary containing user information:
        {
            "id": user_id,
            "email": user_email,
            "role": user_role,
            "account_type": account_type
        }

    Raises:
        WebSocketException: If token is invalid or missing
    """
    if not token:
        logger.warning("WebSocket authentication failed: No token provided")
        raise WebSocketException(code=1008, reason="Unauthorized: No token provided")

    try:
        # Get JWT secret from environment
        jwt_secret = (
            os.getenv("NINAIVALAIGAL_JWT_SECRET")
            or os.getenv("NINA_JWT_SECRET")
            or "dev_jwt_secret_change_in_production"
        )
        jwt_algorithm = "HS256"

        # Decode and validate JWT token
        try:
            payload = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
        except jwt.ExpiredSignatureError:
            logger.warning("WebSocket authentication failed: Token expired")
            raise WebSocketException(code=1008, reason="Unauthorized: Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"WebSocket authentication failed: Invalid token - {e}")
            raise WebSocketException(code=1008, reason="Unauthorized: Invalid token")

        # Extract user information from token payload
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            logger.warning("WebSocket authentication failed: No user_id in token")
            raise WebSocketException(code=1008, reason="Unauthorized: Invalid token payload")

        user_info = {
            "id": str(user_id),
            "email": payload.get("email", ""),
            "role": payload.get("role", "member"),
            "account_type": payload.get("account_type", "individual"),
        }

        logger.info(f"WebSocket authentication successful: user_id={user_id}")
        return user_info

    except WebSocketException:
        # Re-raise WebSocket exceptions
        raise
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        raise WebSocketException(code=1011, reason=f"Internal server error: {str(e)}")


async def extract_token_from_websocket(websocket: WebSocket) -> Optional[str]:
    """
    Extract JWT token from WebSocket connection.

    Tries multiple sources:
    1. Query parameter: ?token=...
    2. Headers: Authorization: Bearer ...
    3. Subprotocol (future)

    Args:
        websocket: FastAPI WebSocket object

    Returns:
        JWT token string or None if not found
    """
    # Try query parameter first (most common for WebSocket)
    if websocket.query_params:
        token = websocket.query_params.get("token")
        if token:
            return token

    # Try Authorization header
    if websocket.headers:
        auth_header = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix

    # Try subprotocol (future enhancement)
    # WebSocket subprotocols can carry auth tokens

    return None


async def authenticate_websocket(websocket: WebSocket) -> Dict[str, Any]:
    """
    Authenticate WebSocket connection and return user info.

    Convenience function that combines token extraction and validation.

    Args:
        websocket: FastAPI WebSocket object

    Returns:
        User information dictionary

    Raises:
        WebSocketException: If authentication fails
    """
    token = await extract_token_from_websocket(websocket)
    return await get_current_user_ws(token)




