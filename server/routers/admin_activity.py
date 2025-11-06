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

API endpoints for querying admin activity logs
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, Request

try:
    from ..auth_utils import get_current_user
except ImportError:
    # Fallback for test environments or different import paths
    try:
        from auth_utils import get_current_user
    except ImportError:
        from auth import get_current_user
from server.config import get_dynamic_database_url

try:
    from ..admin.activity_logger import AdminActivityLogger
except ImportError:
    from admin.activity_logger import AdminActivityLogger

# Export get_activity_logger for use in other routers
__all__ = ["router", "get_activity_logger"]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/activity", tags=["admin"])


# Global database pool for asyncpg operations
_db_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Get or create asyncpg database connection pool"""
    global _db_pool
    if _db_pool is None:
        database_url = get_dynamic_database_url()
        _db_pool = await asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            command_timeout=30,
            statement_cache_size=0,
        )
        logger.info("Database connection pool created for admin activity logging")
    return _db_pool


# Dependency to get admin activity logger
_activity_logger: Optional[AdminActivityLogger] = None


async def get_activity_logger() -> Optional[AdminActivityLogger]:
    """Get or create admin activity logger instance"""
    global _activity_logger
    if _activity_logger is None:
        try:
            pool = await get_db_pool()
            _activity_logger = AdminActivityLogger(pool)
            await _activity_logger.start_services()
        except Exception as e:
            logger.warning(f"Failed to initialize admin activity logger: {e}")
            return None
    return _activity_logger


# Admin check helper
def require_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify user is an admin (system admin or admin role)"""
    # Check if user is system admin
    if current_user.get("is_system_admin", False):
        return current_user

    # Check if user has admin role
    role = current_user.get("role", "")
    if role in ["admin", "system_admin", "ADMIN"]:
        return current_user

    # Check RBAC roles
    rbac_roles = current_user.get("rbac_roles", {})
    if isinstance(rbac_roles, dict) and any(role in ["admin", "system_admin", "ADMIN"] for role in rbac_roles.keys()):
        return current_user

    raise HTTPException(status_code=403, detail="Admin access required")


@router.get("", summary="Get admin activity logs")
async def get_admin_activity_logs(
    request: Request,
    admin_user_id: Optional[str] = Query(None, description="Filter by admin user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    target_type: Optional[str] = Query(None, description="Filter by target type (user, team, organization, etc.)"),
    target_id: Optional[str] = Query(None, description="Filter by target ID"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict = Depends(require_admin_user),
    activity_logger: Optional[AdminActivityLogger] = Depends(get_activity_logger),
):
    """Get admin activity logs with various filters (admin only)"""
    try:
        if not activity_logger:
            raise HTTPException(status_code=503, detail="Activity logging not available")

        # Parse UUIDs if provided
        admin_uuid = None
        if admin_user_id:
            try:
                admin_uuid = UUID(admin_user_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid admin_user_id: {admin_user_id}")

        target_uuid = None
        if target_id:
            try:
                target_uuid = UUID(target_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid target_id: {target_id}")

        logs = await activity_logger.get_activity_logs(
            admin_user_id=admin_uuid,
            action=action,
            target_type=target_type,
            target_id=target_uuid,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        return {
            "logs": logs,
            "total": len(logs),
            "limit": limit,
            "offset": offset,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving admin activity logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve admin activity logs")


@router.get("/summary", summary="Get admin activity summary")
async def get_admin_activity_summary(
    request: Request,
    admin_user_id: Optional[str] = Query(None, description="Filter by admin user ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include in summary"),
    current_user: dict = Depends(require_admin_user),
    activity_logger: Optional[AdminActivityLogger] = Depends(get_activity_logger),
):
    """Get summary statistics of admin activity (admin only)"""
    try:
        if not activity_logger:
            raise HTTPException(status_code=503, detail="Activity logging not available")

        # Parse UUID if provided
        admin_uuid = None
        if admin_user_id:
            try:
                admin_uuid = UUID(admin_user_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid admin_user_id: {admin_user_id}")

        summary = await activity_logger.get_activity_summary(
            admin_user_id=admin_uuid,
            days=days,
        )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving admin activity summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve admin activity summary")
