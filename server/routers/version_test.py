#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Version Test Router

Simple test endpoints to verify API versioning middleware is working.

Related: SPEC-088 API Versioning Strategy
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

# Create test router (unversioned for now)
router = APIRouter(tags=["version-test"])


@router.get("/version-test")
async def version_test_unversioned(request: Request):
    """
    Test endpoint (unversioned).

    This endpoint is not under /api/v1/ and should work without version headers.
    """
    return {"message": "Unversioned endpoint working", "path": str(request.url.path), "version": "unversioned"}


# Create v1 test router
from lib.routing.version_router import create_v1_router

v1_router = create_v1_router(tags=["v1", "version-test"])


@v1_router.get("/test")
async def version_test_v1(request: Request):
    """
    Test endpoint (v1).

    This endpoint is under /api/v1/ and should include version headers.
    """
    # Get version from request state (set by middleware)
    api_version = getattr(request.state, "api_version", "unknown")

    return {
        "message": "V1 endpoint working",
        "path": str(request.url.path),
        "version": f"v{api_version}",
        "middleware_working": api_version == "1",
    }


@v1_router.get("/headers")
async def version_headers_test(request: Request):
    """
    Test endpoint to inspect version headers.

    Returns all request headers and version information.
    """
    api_version = getattr(request.state, "api_version", "unknown")

    return {
        "message": "Version headers test",
        "api_version": f"v{api_version}",
        "headers": dict(request.headers),
        "path": str(request.url.path),
    }
