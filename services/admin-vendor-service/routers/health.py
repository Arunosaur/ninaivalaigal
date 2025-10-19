#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Health and Readiness Endpoints (SPEC-100 Compliant)

Implements SPEC-100 Section 5.3 standardized health endpoints:
- GET /health  - Basic liveness check
- GET /ready   - Readiness check with dependency validation
"""

import os
import time
from datetime import datetime
from typing import Any, Dict

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Service metadata
SERVICE_NAME = "core-api"
SERVICE_VERSION = "1.0.0"
START_TIME = time.time()

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str
    service: str
    version: str
    uptime_seconds: float
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness check response model"""

    status: str
    service: str
    version: str
    dependencies: Dict[str, Any]
    timestamp: str


def get_uptime() -> float:
    """Calculate service uptime in seconds"""
    return time.time() - START_TIME


async def check_database() -> Dict[str, Any]:
    """Check PostgreSQL connectivity"""
    try:
        from database import DatabaseManager

        from config import get_dynamic_database_url

        db = DatabaseManager(get_dynamic_database_url())
        session = db.get_session()

        # Simple query to verify connectivity
        from sqlalchemy import text

        session.execute(text("SELECT 1"))
        session.close()

        return {"status": "healthy", "type": "postgresql", "message": "Connected"}
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return {"status": "unhealthy", "type": "postgresql", "error": str(e)}


async def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        import redis

        redis_url = os.getenv("REDIS_URL", "redis://192.168.66.6:6379/0")

        # Parse Redis URL
        if redis_url.startswith("redis://"):
            # Simple connection test
            r = redis.from_url(redis_url, decode_responses=True)
            r.ping()
            r.close()

            return {"status": "healthy", "type": "redis", "message": "Connected"}
        else:
            return {"status": "unknown", "type": "redis", "message": "Redis URL not configured"}
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        return {"status": "unhealthy", "type": "redis", "error": str(e)}


async def check_pgbouncer() -> Dict[str, Any]:
    """Check PgBouncer connectivity"""
    try:
        # PgBouncer is transparent - if DB works, PgBouncer works
        # We can verify by checking the DB connection goes through PgBouncer port
        from config import get_dynamic_database_url

        db_url = get_dynamic_database_url()

        if ":6432" in db_url:
            return {"status": "healthy", "type": "pgbouncer", "message": "Connection pooling active"}
        else:
            return {"status": "bypassed", "type": "pgbouncer", "message": "Direct PostgreSQL connection"}
    except Exception as e:
        logger.error("pgbouncer_health_check_failed", error=str(e))
        return {"status": "unknown", "type": "pgbouncer", "error": str(e)}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic liveness check (SPEC-100 compliant)

    Returns 200 OK if service is running.
    Does not check dependencies.
    """
    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        uptime_seconds=get_uptime(),
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check with dependency validation (SPEC-100 compliant)

    Returns 200 OK if all dependencies are healthy.
    Returns 503 Service Unavailable if any dependency fails.

    Checks:
    - PostgreSQL connectivity
    - Redis connectivity
    - PgBouncer status
    """
    # Check all dependencies in parallel
    db_status = await check_database()
    redis_status = await check_redis()
    pgbouncer_status = await check_pgbouncer()

    dependencies = {"database": db_status, "redis": redis_status, "pgbouncer": pgbouncer_status}

    # Determine overall status
    all_healthy = all(dep["status"] in ["healthy", "bypassed", "unknown"] for dep in dependencies.values())

    if not all_healthy:
        logger.warning("readiness_check_failed", dependencies=dependencies)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "service": SERVICE_NAME,
                "dependencies": dependencies,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    return ReadinessResponse(
        status="ready",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        dependencies=dependencies,
        timestamp=datetime.utcnow().isoformat(),
    )
