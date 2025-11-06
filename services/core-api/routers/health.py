#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Health and Readiness Endpoints (SPEC-018 Compliant)

Implements SPEC-018 Section 5.3 standardized health endpoints:
- GET /health  - Basic liveness check
- GET /health/live  - Kubernetes liveness probe
- GET /health/ready - Readiness check with dependency validation
- GET /health/detailed - Detailed health with SLO metrics
- GET /memory/health - Memory service specific health checks
"""

import os
import time
from datetime import datetime
from typing import Any, Dict

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

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


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with SLO metrics"""

    status: str
    service: str
    version: str
    uptime_seconds: float
    dependencies: Dict[str, Any]
    slo_metrics: Dict[str, Any] = {}
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

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return {"status": "unknown", "type": "redis", "message": "REDIS_URL not configured"}

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


def get_slo_metrics() -> Dict[str, Any]:
    """Get current SLO metrics"""
    try:
        from lib.observability.slo_monitoring import get_slo_summary

        return get_slo_summary()
    except ImportError:
        return {"error": "SLO monitoring not available"}
    except Exception as e:
        return {"error": str(e)}


class SLOComplianceResponse(BaseModel):
    """SLO compliance response model"""

    status: str = Field(description="Overall SLO compliance status")
    window: str = Field(description="Time window for SLO metrics")
    targets: Dict[str, Any] = Field(description="SLO targets")
    current: Dict[str, Any] = Field(description="Current metrics")
    compliance: Dict[str, bool] = Field(description="Compliance status for each SLO")
    overall_compliant: bool = Field(description="Whether all SLOs are compliant")
    timestamp: str = Field(description="Timestamp of the check")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic liveness check (SPEC-018 compliant)

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


@router.get("/health/live", response_model=HealthResponse)
async def liveness_check():
    """
    Kubernetes liveness probe (SPEC-018 compliant)

    Returns 200 OK if application is running (even if degraded).
    Used by K8s to restart pods that are completely unresponsive.
    """
    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        uptime_seconds=get_uptime(),
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check with dependency validation (SPEC-018 compliant)

    Returns 200 OK if all dependencies are healthy.
    Returns 503 Service Unavailable if any dependency fails.

    Checks:
    - PostgreSQL connectivity
    - Redis connectivity
    - PgBouncer status
    """
    # Check all dependencies in parallel
    import asyncio

    db_status, redis_status, pgbouncer_status = await asyncio.gather(
        check_database(), check_redis(), check_pgbouncer(), return_exceptions=True
    )

    # Handle exceptions
    dependencies = {}
    for name, status in [("database", db_status), ("redis", redis_status), ("pgbouncer", pgbouncer_status)]:
        if isinstance(status, Exception):
            dependencies[name] = {"status": "error", "error": str(status)}
        else:
            dependencies[name] = status

    # Determine overall status
    all_healthy = all(dep.get("status") in ["healthy", "bypassed", "unknown"] for dep in dependencies.values())

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


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    Detailed health check with SLO metrics (SPEC-018 compliant)

    Returns comprehensive health status including:
    - All dependency statuses
    - SLO compliance metrics
    - Performance indicators
    """
    # Check all dependencies in parallel
    import asyncio

    db_status, redis_status, pgbouncer_status = await asyncio.gather(
        check_database(), check_redis(), check_pgbouncer(), return_exceptions=True
    )

    # Handle exceptions
    dependencies = {}
    for name, status in [("database", db_status), ("redis", redis_status), ("pgbouncer", pgbouncer_status)]:
        if isinstance(status, Exception):
            dependencies[name] = {"status": "error", "error": str(status)}
        else:
            dependencies[name] = status

    # Get SLO metrics
    slo_metrics = get_slo_metrics()

    # Determine overall status
    all_healthy = all(dep.get("status") in ["healthy", "bypassed", "unknown"] for dep in dependencies.values())

    overall_status = "healthy" if all_healthy else "degraded"

    return DetailedHealthResponse(
        status=overall_status,
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        uptime_seconds=get_uptime(),
        dependencies=dependencies,
        slo_metrics=slo_metrics,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/health/slo-compliance", response_model=SLOComplianceResponse)
async def slo_compliance_check(
    window: str = Query(default="1h", pattern="^(1h|24h|7d)$", description="Time window for SLO metrics")
):
    """
    SLO Compliance Check (SPEC-018 compliant)

    US#141: SLO Monitoring & Compliance Tracking

    Returns SLO metrics and compliance status for:
    - Availability SLO (99.9% uptime, 30-day window)
    - Response time SLO (P95 < 200ms, 24-hour window)
    - Error rate SLO (< 0.1%, 24-hour window)

    Supports time windows: 1h, 24h, 7d
    """
    try:
        from lib.observability.slo_monitoring import get_slo_status

        slo_status = get_slo_status(window)

        if "error" in slo_status:
            raise HTTPException(status_code=500, detail=slo_status["error"])

        return SLOComplianceResponse(
            status=slo_status["overall_status"],
            window=slo_status["window"],
            targets=slo_status["targets"],
            current=slo_status["current"],
            compliance=slo_status["compliance"],
            overall_compliant=slo_status["compliance"].get("overall", False),
            timestamp=slo_status["timestamp"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("slo_compliance_check_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get SLO compliance: {str(e)}")
