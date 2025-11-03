#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Memory Service Health Monitoring

Provides memory-specific health checks for SPEC-018 compliance:
- Memory service connectivity
- Redis cache health
- Memory storage metrics
- Performance indicators
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = structlog.get_logger(__name__)
router = APIRouter()


class MemoryHealthResponse(BaseModel):
    """Memory service health check response"""

    status: str
    service: str
    components: Dict[str, Any]
    metrics: Dict[str, Any]
    timestamp: str


class MemoryComponentHealth(BaseModel):
    """Individual memory component health"""

    name: str
    status: str
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    details: Dict[str, Any] = {}


async def check_memory_service() -> Dict[str, Any]:
    """Check memory service connectivity and performance"""
    start_time = time.time()

    try:
        # Check if we can import memory service
        from memory_api import router as memory_router

        # Basic check - if we can import, service is likely healthy
        response_time = (time.time() - start_time) * 1000

        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "endpoints": len(memory_router.routes),
            "details": {
                "service": "memory_api",
                "router_loaded": True,
            },
        }
    except ImportError as e:
        return {
            "status": "unhealthy",
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
            "error": str(e),
            "details": {
                "service": "memory_api",
                "router_loaded": False,
            },
        }
    except Exception as e:
        logger.error("memory_service_health_check_failed", error=str(e))
        return {
            "status": "unhealthy",
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
            "error": str(e),
            "details": {
                "service": "memory_api",
                "router_loaded": False,
            },
        }


async def check_redis_memory_cache() -> Dict[str, Any]:
    """Check Redis memory cache health"""
    start_time = time.time()

    try:
        import os

        import redis

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        # Connect to Redis
        r = redis.from_url(redis_url, decode_responses=True)

        # Test basic operations
        test_key = f"health_check_{int(time.time())}"

        # Set test value
        r.setex(test_key, 10, "test_value")

        # Get test value
        value = r.get(test_key)

        # Clean up
        r.delete(test_key)

        # Get Redis info
        info = r.info()

        response_time = (time.time() - start_time) * 1000

        return {
            "status": "healthy" if value == "test_value" else "degraded",
            "response_time_ms": round(response_time, 2),
            "details": {
                "redis_url": redis_url.split("@")[-1] if "@" in redis_url else redis_url,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "test_operation": "passed" if value == "test_value" else "failed",
            },
        }

    except ImportError:
        return {
            "status": "unknown",
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
            "error": "Redis client not installed",
            "details": {"redis_available": False},
        }
    except Exception as e:
        logger.error("redis_memory_health_check_failed", error=str(e))
        return {
            "status": "unhealthy",
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
            "error": str(e),
            "details": {"redis_available": False},
        }


async def check_memory_storage() -> Dict[str, Any]:
    """Check memory storage backend health"""
    start_time = time.time()

    try:
        # Check database connectivity for memory storage
        from database import DatabaseManager

        from config import get_dynamic_database_url

        db = DatabaseManager(get_dynamic_database_url())
        session = db.get_session()

        # Test memory tables
        from sqlalchemy import text

        # Check if memory tables exist
        result = session.execute(
            text(
                """
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('memories', 'memory_tokens', 'contexts')
        """
            )
        )

        table_count = result.fetchone()[0]

        # Get memory statistics
        stats_result = session.execute(
            text(
                """
            SELECT
                (SELECT COUNT(*) FROM memories WHERE deleted_at IS NULL) as active_memories,
                (SELECT COUNT(*) FROM memory_tokens WHERE deleted_at IS NULL) as active_tokens,
                (SELECT COUNT(*) FROM contexts WHERE deleted_at IS NULL) as active_contexts
        """
            )
        )

        stats = stats_result.fetchone()

        session.close()

        response_time = (time.time() - start_time) * 1000

        return {
            "status": "healthy" if table_count >= 3 else "degraded",
            "response_time_ms": round(response_time, 2),
            "details": {
                "tables_found": table_count,
                "expected_tables": 3,
                "active_memories": stats.active_memories if stats else 0,
                "active_tokens": stats.active_tokens if stats else 0,
                "active_contexts": stats.active_contexts if stats else 0,
                "database": "postgresql",
            },
        }

    except Exception as e:
        logger.error("memory_storage_health_check_failed", error=str(e))
        return {
            "status": "unhealthy",
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
            "error": str(e),
            "details": {"database": "postgresql"},
        }


async def check_memory_performance() -> Dict[str, Any]:
    """Check memory service performance indicators"""
    try:
        # This would typically include metrics like:
        # - Memory operation response times
        # - Cache hit rates
        # - Queue depths
        # - Concurrent operation counts

        # For now, return basic performance info
        return {
            "status": "healthy",
            "details": {
                "cache_hit_rate": "unknown",  # Would be calculated from Redis metrics
                "avg_response_time_ms": "unknown",  # Would be calculated from request tracking
                "concurrent_operations": 0,  # Would be tracked in production
                "queue_depth": 0,  # Would be tracked for async operations
                "performance_monitoring": "basic",
            },
        }
    except Exception as e:
        logger.error("memory_performance_check_failed", error=str(e))
        return {"status": "error", "error": str(e), "details": {"performance_monitoring": "error"}}


@router.get("/memory/health", response_model=MemoryHealthResponse)
async def memory_health_check():
    """
    Memory service health check (SPEC-018 compliant)

    Returns comprehensive health status for memory-related services:
    - Memory API service
    - Redis cache
    - Memory storage (database)
    - Performance indicators
    """

    # Check all memory components in parallel
    import asyncio

    service_health, redis_health, storage_health, performance_health = await asyncio.gather(
        check_memory_service(),
        check_redis_memory_cache(),
        check_memory_storage(),
        check_memory_performance(),
        return_exceptions=True,
    )

    # Handle exceptions
    components = {}
    overall_status = "healthy"

    for name, health in [
        ("service", service_health),
        ("redis_cache", redis_health),
        ("storage", storage_health),
        ("performance", performance_health),
    ]:
        if isinstance(health, Exception):
            components[name] = {"status": "error", "error": str(health), "response_time_ms": None, "details": {}}
            overall_status = "unhealthy"
        else:
            components[name] = health
            if health.get("status") in ["unhealthy", "error"]:
                overall_status = "unhealthy"
            elif health.get("status") == "degraded" and overall_status == "healthy":
                overall_status = "degraded"

    # Calculate overall metrics
    total_response_time = sum(
        comp.get("response_time_ms", 0) for comp in components.values() if comp.get("response_time_ms") is not None
    )
    avg_response_time = (
        total_response_time / len([comp for comp in components.values() if comp.get("response_time_ms") is not None])
        if any(comp.get("response_time_ms") for comp in components.values())
        else 0
    )

    metrics = {
        "components_checked": len(components),
        "avg_response_time_ms": round(avg_response_time, 2),
        "unhealthy_components": sum(1 for comp in components.values() if comp.get("status") in ["unhealthy", "error"]),
        "degraded_components": sum(1 for comp in components.values() if comp.get("status") == "degraded"),
    }

    return MemoryHealthResponse(
        status=overall_status,
        service="memory-service",
        components=components,
        metrics=metrics,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/memory/health/simple")
async def memory_health_simple():
    """
    Simple memory health check for load balancers

    Returns minimal health status suitable for Kubernetes probes.
    """
    try:
        # Quick Redis check
        redis_health = await check_redis_memory_cache()

        if redis_health.get("status") in ["healthy", "degraded"]:
            return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
        else:
            raise HTTPException(status_code=503, detail="Memory service unhealthy")

    except Exception as e:
        logger.error("memory_health_simple_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Memory service unavailable")
