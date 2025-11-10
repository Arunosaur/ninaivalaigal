#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""Health and readiness endpoints for the Graph/AI service."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict

import structlog
from fastapi import APIRouter, HTTPException
from lib.graph.age_client import get_age_client
from pydantic import BaseModel
from redis import asyncio as aioredis

from config import get_config

CONFIG = get_config()
SERVICE_NAME = CONFIG.service_name
SERVICE_VERSION = "1.0.0"
START_TIME = time.time()

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Basic health response payload."""

    status: str
    service: str
    version: str
    uptime_seconds: float
    timestamp: str
    details: Dict[str, Any]


class ReadinessResponse(BaseModel):
    """Detailed readiness payload including dependency status."""

    status: str
    service: str
    version: str
    dependencies: Dict[str, Any]
    timestamp: str


def get_uptime() -> float:
    """Return service uptime in seconds."""

    return time.time() - START_TIME


async def check_database() -> Dict[str, Any]:
    """Validate PgBouncer connection and Apache AGE extension."""

    try:
        client = await get_age_client(use_cache=False)
        return await client.health_check()
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.error("graphops_health_check_failed", error=str(exc))
        return {
            "status": "unhealthy",
            "type": "postgresql+age",
            "database": CONFIG.db_name,
            "error": str(exc),
        }


async def check_redis() -> Dict[str, Any]:
    """Ping Redis if a URL is configured; otherwise bypass the check."""

    if not CONFIG.redis_url:
        return {
            "status": "bypassed",
            "type": "redis",
            "message": "REDIS_URL not configured for graph service",
        }

    try:
        client = aioredis.from_url(CONFIG.redis_url)
        try:
            await client.ping()
        finally:
            await client.close()

        return {
            "status": "healthy",
            "type": "redis",
            "url": CONFIG.redis_url,
        }
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.error("graph_redis_health_check_failed", error=str(exc))
        return {
            "status": "unhealthy",
            "type": "redis",
            "url": CONFIG.redis_url,
            "error": str(exc),
        }


async def check_graphops() -> Dict[str, Any]:
    """Provide informational status for the external GraphOps service."""

    return {
        "status": "bypassed",
        "type": "graphops-service",
        "message": "External GraphOps service is optional for readiness",
        "port": CONFIG.service_port,
    }


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return liveness information backed by real AGE verification."""

    age_status = await check_database()
    overall_status = "healthy" if age_status["status"] == "healthy" else "unhealthy"

    if overall_status != "healthy":  # pragma: no cover - defensive logging path
        logger.warning("health_check_unhealthy", age_status=age_status)

    details = {
        "apache_age": {
            "status": age_status["status"],
            "database": age_status.get("database"),
            "age_extension": age_status.get("age_extension") or age_status.get("type"),
            "graphs_available": len(age_status.get("graphs", [])),
        }
    }

    return HealthResponse(
        status=overall_status,
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        uptime_seconds=get_uptime(),
        timestamp=datetime.utcnow().isoformat(),
        details=details,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """Run dependency checks to determine readiness."""

    age_check = await check_database()
    graph_redis_check = await check_redis()
    graphops_check = await check_graphops()

    dependencies = {
        "apache-age": age_check,
        "graph-redis": graph_redis_check,
        "graphops": graphops_check,
    }

    all_healthy = all(dep["status"] in {"healthy", "bypassed", "unknown"} for dep in dependencies.values())

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
