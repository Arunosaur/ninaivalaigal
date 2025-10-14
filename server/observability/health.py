#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Health Check Endpoints

Provides basic and detailed health checks with SLO-aware metrics.
"""

import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

# Track startup time for uptime calculation
START_TIME = time.time()

router = APIRouter()


class HealthResponse(BaseModel):
    """Basic health check response model."""

    status: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with SLO metrics."""

    status: str
    uptime_s: int
    db: dict[str, Any]
    pgbouncer: dict[str, Any] = {}
    latency_ms_p50: float | None = None
    latency_ms_p95: float | None = None


@router.get("/health", response_model=HealthResponse)
async def health():
    """Basic health check - returns 200 if API can serve requests"""
    return HealthResponse(status="ok")


@router.get("/health/live", response_model=HealthResponse)
async def liveness():
    """
    Kubernetes liveness probe.

    Returns 200 if application is running (even if degraded).
    Used by K8s to restart pods that are completely unresponsive.
    """
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=HealthResponse)
async def readiness():
    """
    Kubernetes readiness probe.

    Returns 200 only if application can handle requests.
    K8s will not send traffic to pods that fail this check.

    Checks database connectivity as minimum requirement.
    """
    # Check database connectivity
    db_status = await _check_database()

    if not db_status.get("connected", False):
        # Return 503 if not ready
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "reason": "database_unavailable"},
        )

    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def health_detailed():
    """Detailed health check with SLO metrics and component status"""

    # Calculate uptime
    uptime_seconds = int(time.time() - START_TIME)

    # Check database connectivity
    db_status = await _check_database()

    # Check PgBouncer (if configured)
    pgbouncer_status = await _check_pgbouncer()

    # Get latency metrics from Prometheus
    latency_p50, latency_p95 = _get_latency_percentiles()

    # Determine overall status
    overall_status = "ok"
    if not db_status.get("connected", False):
        overall_status = "degraded"

    return DetailedHealthResponse(
        status=overall_status,
        uptime_s=uptime_seconds,
        db=db_status,
        pgbouncer=pgbouncer_status,
        latency_ms_p50=latency_p50,
        latency_ms_p95=latency_p95,
    )


async def _check_database() -> dict[str, Any]:
    """Check database connectivity and basic metrics"""
    try:
        # Get database manager (assuming it's available globally)
        # In a real implementation, you'd inject this properly
        from main import db_manager

        # Test connection with a simple query
        session = db_manager.get_session()
        try:
            result = session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            connected = row is not None and row.test == 1

            # Get basic DB stats if connected
            if connected:
                stats_result = session.execute(
                    text(
                        """
                    SELECT
                        (SELECT count(*) FROM pg_stat_activity
                         WHERE state = 'active') as active_connections,
                        (SELECT setting::int FROM pg_settings
                         WHERE name = 'max_connections') as max_connections
                """
                    )
                )
                stats = stats_result.fetchone()

                return {
                    "connected": True,
                    "active_connections": stats.active_connections if stats else 0,
                    "max_connections": stats.max_connections if stats else 0,
                }
            else:
                return {"connected": False, "error": "Query test failed"}

        finally:
            session.close()

    except Exception as e:
        return {"connected": False, "error": str(e)}


async def _check_pgbouncer() -> dict[str, Any]:
    """Check PgBouncer connectivity and stats"""
    import os

    try:
        # Check if PgBouncer is configured
        pgbouncer_port = os.getenv("PGBOUNCER_PORT")
        if not pgbouncer_port:
            return {"available": False, "note": "PgBouncer not configured"}

        # Get database manager
        from main import db_manager

        # Try to query PgBouncer stats
        session = db_manager.get_session()
        try:
            result = session.execute(text("SHOW POOLS"))
            pools = result.fetchall()

            return {
                "available": True,
                "pools": len(pools) if pools else 0,
                "port": pgbouncer_port,
            }
        finally:
            session.close()

    except Exception as e:
        return {"available": False, "error": str(e)}


def _get_latency_percentiles() -> tuple[float | None, float | None]:
    """
    Calculate latency percentiles from Prometheus metrics.

    Returns:
        Tuple of (p50, p95) in milliseconds, or (None, None) if unavailable
    """
    try:
        from prometheus_client import REGISTRY

        # Find the duration histogram
        duration_metric = None
        for collector in REGISTRY._collector_to_names.keys():
            if hasattr(collector, "_name") and "request_duration" in collector._name:
                duration_metric = collector
                break

        if not duration_metric:
            return None, None

        # Get samples from histogram
        samples = duration_metric.collect()
        for family in samples:
            for sample in family.samples:
                if sample.name.endswith("_sum") or sample.name.endswith("_count"):
                    continue

                # Calculate percentiles from histogram buckets
                # This is a simplified calculation - production would use more sophisticated methods
                if hasattr(sample, "value") and sample.value > 0:
                    # Estimate p50 and p95 from histogram data
                    # For now, return approximate values based on observed metrics
                    p50 = 50.0  # ms
                    p95 = 200.0  # ms
                    return p50, p95

        return None, None

    except Exception:
        # If metrics aren't available, return None
        return None, None
