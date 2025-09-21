"""
Health Check Endpoints

Provides basic and detailed health checks with SLO-aware metrics.
"""

import time
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

# Track startup time for uptime calculation
START_TIME = time.time()

router = APIRouter()

class HealthResponse(BaseModel):
    status: str

class DetailedHealthResponse(BaseModel):
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

@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def health_detailed():
    """Detailed health check with SLO metrics and component status"""

    # Calculate uptime
    uptime_seconds = int(time.time() - START_TIME)

    # Check database connectivity
    db_status = await _check_database()

    # Check PgBouncer (if configured)
    pgbouncer_status = await _check_pgbouncer()

    # Determine overall status
    overall_status = "ok"
    if not db_status.get("connected", False):
        overall_status = "degraded"

    return DetailedHealthResponse(
        status=overall_status,
        uptime_s=uptime_seconds,
        db=db_status,
        pgbouncer=pgbouncer_status,
        # TODO: Add latency percentiles from metrics
        latency_ms_p50=None,
        latency_ms_p95=None
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
                stats_result = session.execute(text("""
                    SELECT 
                        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                        (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
                """))
                stats = stats_result.fetchone()

                return {
                    "connected": True,
                    "active_connections": stats.active_connections if stats else 0,
                    "max_connections": stats.max_connections if stats else 0
                }
            else:
                return {"connected": False, "error": "Query test failed"}

        finally:
            session.close()

    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }

async def _check_pgbouncer() -> dict[str, Any]:
    """Check PgBouncer connectivity and stats"""
    try:
        # This would connect to PgBouncer's admin interface
        # For now, return a placeholder
        return {
            "available": False,
            "note": "PgBouncer health check not implemented yet"
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }
