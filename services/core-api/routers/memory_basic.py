#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Basic Memory Endpoints - Stub for Auth Testing

These endpoints exist primarily to test authentication middleware.
Full memory functionality is in other routers (memory_health_api, etc.)
"""

from database import DatabaseManager, User
from fastapi import APIRouter, Depends

from auth import get_current_user


# Database manager dependency
def get_db():
    """Get database manager with dynamic configuration"""
    from config import get_dynamic_database_url

    return DatabaseManager(get_dynamic_database_url())


router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


@router.get("/health")
async def memory_health(current_user=Depends(get_current_user)):
    """
    Memory service health check - Protected endpoint

    This endpoint requires authentication. Used by tests to verify:
    - Valid tokens return 200
    - Invalid tokens return 401
    - Missing tokens return 401
    """
    return {
        "status": "healthy",
        "service": "memory",
        "user_id": getattr(current_user, "id", None),
        "message": "Memory service operational",
    }


# NOTE: /{memory_id} routes removed - they conflict with /memories from memory_browser_api
# These were stubs for auth testing only. Real memory operations are in memory_browser_api.py
