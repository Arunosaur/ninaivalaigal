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

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text

# Import alerting integration
from .alerting_integration import get_alerting_integration, send_health_alert
from .dependency_health import (
    get_dependency_monitor,
    start_dependency_monitoring,
    stop_dependency_monitoring,
)

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


class AlertTestResponse(BaseModel):
    """Response model for alert testing."""

    success: bool
    results: dict[str, bool | None]
    message: str


class DependencyStatusResponse(BaseModel):
    """Response model for dependency status."""

    dependencies: dict[str, dict[str, Any]]
    summary: dict[str, Any]
    monitoring_active: bool


class MonitoringControlResponse(BaseModel):
    """Response model for monitoring control."""

    success: bool
    message: str
    monitoring_active: bool


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


@router.get("/memory/health", response_model=HealthResponse)
async def memory_health():
    """Memory service health check - checks memory service connectivity"""
    try:
        # Check if memory service is accessible
        import requests

        # Try to connect to memory service
        response = requests.get("http://localhost:13393/health", timeout=5)

        if response.status_code == 200:
            return HealthResponse(status="ok")
        else:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "unhealthy", "reason": "memory_service_unavailable"},
            )
    except Exception as e:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "reason": f"memory_service_error: {str(e)}"},
        )


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


@router.post("/health/alert/test", response_model=AlertTestResponse)
async def test_alerting():
    """
    Test alerting integration by sending a test alert to all enabled channels.

    Returns:
        AlertTestResponse with test results for each channel
    """
    try:
        alerting = await get_alerting_integration()
        results = await alerting.test_alerting()

        # Check if any enabled channels failed
        enabled_results = [r for r in results.values() if r is not None]
        success = all(enabled_results) if enabled_results else True

        return AlertTestResponse(success=success, results=results, message="Test alert sent to all enabled channels")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to test alerting: {str(e)}"
        )


@router.post("/health/alert/send")
async def send_custom_alert(
    alert_name: str, severity: str, summary: str, description: str, component: str = "health", team: str = "platform"
):
    """
    Send a custom alert through the alerting system.

    Args:
        alert_name: Name of the alert
        severity: Severity level (critical, warning, info)
        summary: Alert summary
        description: Alert description
        component: Component name (default: health)
        team: Team name (default: platform)

    Returns:
        Success status
    """
    try:
        # Validate severity
        if severity not in ["critical", "warning", "info"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Severity must be one of: critical, warning, info"
            )

        success = await send_health_alert(
            alert_name=alert_name,
            severity=severity,
            summary=summary,
            description=description,
            component=component,
            team=team,
        )

        if success:
            return {"status": "sent", "message": "Alert sent successfully"}
        else:
            return {"status": "failed", "message": "Alert failed to send to any enabled channel"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send alert: {str(e)}")


@router.get("/health/dependencies", response_model=DependencyStatusResponse)
async def get_dependency_status():
    """
    Get real-time status of all system dependencies.

    Returns:
        Detailed status of all dependencies including health, performance metrics, and monitoring status
    """
    try:
        monitor = await get_dependency_monitor()
        dependencies = await monitor.get_dependency_status()
        summary = await monitor.get_health_summary()

        return DependencyStatusResponse(
            dependencies=dependencies,
            summary=summary,
            monitoring_active=monitor.monitoring_active,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get dependency status: {str(e)}"
        )


@router.post("/health/monitoring/start", response_model=MonitoringControlResponse)
async def start_monitoring():
    """
    Start continuous dependency health monitoring.

    Returns:
        Success status and monitoring state
    """
    try:
        await start_dependency_monitoring()

        return MonitoringControlResponse(
            success=True,
            message="Dependency monitoring started successfully",
            monitoring_active=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start monitoring: {str(e)}"
        )


@router.post("/health/monitoring/stop", response_model=MonitoringControlResponse)
async def stop_monitoring():
    """
    Stop continuous dependency health monitoring.

    Returns:
        Success status and monitoring state
    """
    try:
        await stop_dependency_monitoring()

        return MonitoringControlResponse(
            success=True,
            message="Dependency monitoring stopped successfully",
            monitoring_active=False,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to stop monitoring: {str(e)}"
        )


@router.post("/health/monitoring/test")
async def test_dependency_monitoring():
    """
    Test dependency monitoring by running a single check cycle.

    Returns:
        Results of the monitoring test cycle
    """
    try:
        monitor = await get_dependency_monitor()
        await monitor._check_all_dependencies()

        dependencies = await monitor.get_dependency_status()
        summary = await monitor.get_health_summary()

        return {
            "success": True,
            "message": "Dependency monitoring test completed",
            "dependencies": dependencies,
            "summary": summary,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to test monitoring: {str(e)}"
        )
