#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Authentication Audit Logging Module

SPEC-114: Implement audit logging for all authentication events.
Logs all login, logout, signup, and token refresh events for compliance and security.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import structlog

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

logger = structlog.get_logger(__name__)


async def log_auth_event(
    request: Any,
    user_id: Optional[str],
    action: str,
    success: bool,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """
    Log authentication events for audit trail.

    SPEC-114 requirement: All authentication events must be logged with:
    - Timestamp
    - User ID (if available)
    - Action (login, logout, signup, refresh, etc.)
    - Success status
    - IP address
    - User agent
    - Additional details

    Args:
        request: FastAPI Request object
        user_id: User ID (None for anonymous/unauthenticated events)
        action: Action type (login, logout, signup, refresh, token_revoke, etc.)
        success: Whether the action was successful
        details: Additional details about the event
    """
    try:
        # Extract IP address
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP", "")
            or (request.client.host if request.client else "unknown")
        )

        # Extract user agent
        user_agent = request.headers.get("User-Agent", "unknown")

        # Build audit entry
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "success": success,
            "ip_address": client_ip,
            "user_agent": user_agent,
            "details": details or {},
        }

        # Log to structured logger
        if success:
            logger.info(f"AUTH_AUDIT: {action}", **audit_entry)
        else:
            logger.warning(f"AUTH_AUDIT: {action} failed", **audit_entry)

        # TODO: Store in database for compliance (future enhancement)
        # This would require a database connection and audit_logs table
        # await store_audit_log(audit_entry)

    except Exception as e:
        # Don't fail the request if audit logging fails
        logger.error(f"Failed to log auth event: {e}", action=action, user_id=user_id)


async def log_login_attempt(
    request: Any,
    email: str,
    success: bool,
    user_id: Optional[str] = None,
    error_reason: Optional[str] = None,
) -> None:
    """Log login attempt event."""
    details = {"email": email}
    if error_reason:
        details["error_reason"] = error_reason

    await log_auth_event(
        request=request,
        user_id=user_id,
        action="login",
        success=success,
        details=details,
    )


async def log_signup_attempt(
    request: Any,
    email: str,
    success: bool,
    user_id: Optional[str] = None,
    error_reason: Optional[str] = None,
) -> None:
    """Log signup attempt event."""
    details = {"email": email}
    if error_reason:
        details["error_reason"] = error_reason

    await log_auth_event(
        request=request,
        user_id=user_id,
        action="signup",
        success=success,
        details=details,
    )


async def log_logout(
    request: Any,
    user_id: str,
    success: bool = True,
) -> None:
    """Log logout event."""
    await log_auth_event(
        request=request,
        user_id=user_id,
        action="logout",
        success=success,
    )


async def log_token_refresh(
    request: Any,
    user_id: str,
    success: bool = True,
    error_reason: Optional[str] = None,
) -> None:
    """Log token refresh event."""
    details = {}
    if error_reason:
        details["error_reason"] = error_reason

    await log_auth_event(
        request=request,
        user_id=user_id,
        action="token_refresh",
        success=success,
        details=details,
    )


async def log_rate_limit_exceeded(
    request: Any,
    endpoint: str,
    identifier: str,
) -> None:
    """Log rate limit exceeded event."""
    await log_auth_event(
        request=request,
        user_id=None,
        action="rate_limit_exceeded",
        success=False,
        details={
            "endpoint": endpoint,
            "identifier": identifier,
        },
    )
