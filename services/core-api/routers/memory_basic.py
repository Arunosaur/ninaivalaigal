#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Basic Memory Endpoints - Stub for Auth Testing

These endpoints exist primarily to test authentication middleware.
Full memory functionality is in other routers (memory_health_api, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user

router = APIRouter(prefix="/memory", tags=["memory"])


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


@router.get("/{memory_id}")
async def get_memory(memory_id: str, current_user=Depends(get_current_user)):
    """
    Get memory by ID - Protected endpoint

    This is a stub for auth testing. Full memory retrieval is in Rust service.
    """
    # Check if user has access to this memory
    # In real implementation, this would check ownership/permissions

    return {
        "id": memory_id,
        "user_id": getattr(current_user, "id", None),
        "message": "Memory stub - full implementation in Rust service",
        "note": "This endpoint exists for auth testing",
    }


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, current_user=Depends(get_current_user)):
    """
    Delete memory by ID - Protected endpoint

    This is a stub for auth testing.
    """
    return {
        "message": f"Memory {memory_id} deletion stub",
        "user_id": getattr(current_user, "id", None),
        "note": "This endpoint exists for auth testing",
    }
