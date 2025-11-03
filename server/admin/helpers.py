#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-005: Admin Dashboard
US-100: Admin Activity Logging System

Helper functions for automatically logging admin actions
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Request

from .activity_logger import AdminActivityLogger

logger = logging.getLogger(__name__)


async def log_admin_action_async(
    activity_logger: Optional[AdminActivityLogger],
    admin_user_id: UUID,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    """
    Helper function to log admin actions asynchronously

    Args:
        activity_logger: AdminActivityLogger instance (can be None - will skip logging)
        admin_user_id: UUID of the admin user performing the action
        action: Action name (e.g., 'create_user', 'update_team')
        target_type: Type of target resource (e.g., 'user', 'team', 'organization')
        target_id: UUID of the target resource
        details: Additional details to log (dict)
        request: FastAPI Request object (for extracting IP address and user agent)
    """
    if not activity_logger:
        return

    try:
        ip_address = None
        user_agent = None

        if request:
            # Extract IP address
            if request.client:
                ip_address = request.client.host
            elif "x-forwarded-for" in request.headers:
                ip_address = request.headers["x-forwarded-for"].split(",")[0].strip()
            elif "x-real-ip" in request.headers:
                ip_address = request.headers["x-real-ip"]

            # Extract user agent
            user_agent = request.headers.get("user-agent")

        await activity_logger.log_activity(
            admin_user_id=admin_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as e:
        logger.error(f"Failed to log admin action: {e}", exc_info=True)
        # Don't raise - logging should not break the main operation


def get_admin_user_id_from_request(current_user: Dict[str, Any]) -> Optional[UUID]:
    """
    Extract admin user ID from current_user dict

    Args:
        current_user: Dict with user information from get_current_user

    Returns:
        UUID of the admin user, or None if not found
    """
    try:
        user_id = current_user.get("user_id")
        if user_id:
            # Handle both string and UUID
            if isinstance(user_id, str):
                return UUID(user_id)
            elif isinstance(user_id, UUID):
                return user_id
        return None
    except (ValueError, AttributeError):
        logger.warning(f"Could not extract admin user ID from: {current_user}")
        return None
