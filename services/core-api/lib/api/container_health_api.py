#!/usr/bin/env python3
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
"""
Container Health Monitoring API (SPEC-051)

REST API endpoints for container health monitoring and platform stability.
"""

from asyncio import Semaphore
from typing import Any, Dict

import structlog
from fastapi import APIRouter, HTTPException

from lib.observability.container_health import (
    ContainerStatus,
    ServiceType,
    get_container_health_monitor,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/platform", tags=["platform-health"])

# Request throttling semaphore (Fix #2) - Limit concurrent health checks to 5
_health_check_semaphore = Semaphore(5)


@router.get("/health/containers")
async def get_all_containers_health() -> Dict[str, Any]:
    """
    Get health status of all platform containers

    Returns comprehensive health information including:
    - Individual service health
    - Response times
    - Resource utilization
    - Dependency status

    Note: Throttled to 5 concurrent requests to prevent resource exhaustion
    """
    async with _health_check_semaphore:
        monitor = get_container_health_monitor()
        return await monitor.get_platform_health()


@router.get("/health/containers/{service}")
async def get_container_health(service: str) -> Dict[str, Any]:
    """
    Get health status of a specific container

    Args:
        service: Service name (core-api, memory-service, etc.)
    """
    try:
        service_type = ServiceType(service)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")

    monitor = get_container_health_monitor()

    if service_type not in monitor.health_cache:
        # Trigger a fresh check
        await monitor.check_all_services()

    if service_type in monitor.health_cache:
        return monitor.health_cache[service_type].to_dict()
    else:
        raise HTTPException(status_code=503, detail=f"Service '{service}' health check failed")


@router.get("/health/dependencies")
async def get_dependency_status() -> Dict[str, Any]:
    """
    Get dependency validation status for all services

    Shows which services depend on which infrastructure components
    and their current health status.
    """
    monitor = get_container_health_monitor()

    # Ensure we have fresh data
    await monitor.check_all_services()

    dependency_status = await monitor.validate_dependencies()

    return {
        "timestamp": (
            monitor.health_cache[list(monitor.health_cache.keys())[0]].last_check.isoformat()
            if monitor.health_cache
            else None
        ),
        "dependencies": {s.value: deps for s, deps in dependency_status.items()},
    }


@router.get("/health/summary")
async def get_health_summary() -> Dict[str, Any]:
    """
    Get high-level platform health summary

    Provides quick overview of platform status without detailed metrics.
    Useful for dashboards and monitoring systems.

    Note: Throttled to 5 concurrent requests to prevent resource exhaustion
    """
    async with _health_check_semaphore:
        monitor = get_container_health_monitor()
        platform_health = await monitor.get_platform_health()

        return {
            "overall_status": platform_health["overall_status"],
            "timestamp": platform_health["timestamp"],
            "summary": platform_health["summary"],
            "unhealthy_services": [
                service
                for service, health in platform_health["services"].items()
                if health["status"] in ["unhealthy", "degraded"]
            ],
        }


@router.post("/health/check")
async def trigger_health_check() -> Dict[str, Any]:
    """
    Trigger immediate health check of all services

    Forces a fresh health check instead of using cached data.
    Useful for manual verification after deployments or incidents.
    """
    monitor = get_container_health_monitor()
    health_status = await monitor.check_all_services()

    return {
        "message": "Health check completed",
        "timestamp": list(health_status.values())[0].last_check.isoformat() if health_status else None,
        "services_checked": len(health_status),
        "results": {s.value: h.to_dict() for s, h in health_status.items()},
    }


@router.get("/health/uptime")
async def get_service_uptime() -> Dict[str, Any]:
    """
    Get uptime information for all services

    Returns uptime in seconds for each service that reports it.
    """
    monitor = get_container_health_monitor()

    # Ensure fresh data
    await monitor.check_all_services()

    uptime_data = {}
    for service, health in monitor.health_cache.items():
        if health.uptime_seconds is not None:
            uptime_data[service.value] = {
                "uptime_seconds": health.uptime_seconds,
                "uptime_hours": round(health.uptime_seconds / 3600, 2),
                "uptime_days": round(health.uptime_seconds / 86400, 2),
                "status": health.status.value,
            }

    return {
        "timestamp": list(monitor.health_cache.values())[0].last_check.isoformat() if monitor.health_cache else None,
        "services": uptime_data,
    }


@router.get("/health/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """
    Get performance metrics for all services

    Returns response times and resource utilization.
    """
    monitor = get_container_health_monitor()

    # Ensure fresh data
    await monitor.check_all_services()

    performance_data = {}
    for service, health in monitor.health_cache.items():
        metrics = {"status": health.status.value}

        if health.response_time_ms is not None:
            metrics["response_time_ms"] = health.response_time_ms

        if health.cpu_percent is not None:
            metrics["cpu_percent"] = health.cpu_percent

        if health.memory_mb is not None:
            metrics["memory_mb"] = health.memory_mb

        performance_data[service.value] = metrics

    return {
        "timestamp": list(monitor.health_cache.values())[0].last_check.isoformat() if monitor.health_cache else None,
        "services": performance_data,
    }
