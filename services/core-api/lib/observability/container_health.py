#!/usr/bin/env python3
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
"""
Container Health Monitoring System (SPEC-051)

Monitors health of all platform containers:
- Core API
- Memory Service (Rust)
- Graph Service
- Business Service
- Upload API
- Redis Cache

Implements:
- Health check endpoints
- Dependency validation
- Resource utilization monitoring
- Automated failure detection
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
import psutil
import structlog

logger = structlog.get_logger(__name__)


class ContainerStatus(str, Enum):
    """Container health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceType(str, Enum):
    """Service types in the platform"""

    CORE_API = "core-api"
    MEMORY_SERVICE = "memory-service"
    GRAPH_SERVICE = "graph-service"
    BUSINESS_SERVICE = "business-service"
    UPLOAD_API = "upload-api"
    REDIS = "redis"
    POSTGRES = "postgres"
    PGBOUNCER = "pgbouncer"


class ContainerHealth:
    """Container health status"""

    def __init__(
        self,
        service: ServiceType,
        status: ContainerStatus,
        response_time_ms: Optional[float] = None,
        cpu_percent: Optional[float] = None,
        memory_mb: Optional[float] = None,
        uptime_seconds: Optional[float] = None,
        error: Optional[str] = None,
        dependencies: Optional[Dict[str, ContainerStatus]] = None,
        last_check: Optional[datetime] = None,
    ):
        self.service = service
        self.status = status
        self.response_time_ms = response_time_ms
        self.cpu_percent = cpu_percent
        self.memory_mb = memory_mb
        self.uptime_seconds = uptime_seconds
        self.error = error
        self.dependencies = dependencies or {}
        self.last_check = last_check or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "service": self.service.value,
            "status": self.status.value,
            "response_time_ms": self.response_time_ms,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "uptime_seconds": self.uptime_seconds,
            "error": self.error,
            "dependencies": {k: v.value for k, v in self.dependencies.items()},
            "last_check": self.last_check.isoformat(),
        }


class ContainerHealthMonitor:
    """
    Container Health Monitoring System

    Monitors all platform containers and their dependencies.
    Implements SPEC-051 requirements for platform stability.
    """

    def __init__(self):
        self.health_cache: Dict[ServiceType, ContainerHealth] = {}
        self.check_interval = 30  # seconds
        self.timeout = 5  # seconds
        self.monitoring_active = False
        self._monitor_task: Optional[asyncio.Task] = None

        # Platform health cache with TTL
        self._platform_health_cache: Optional[Dict[str, Any]] = None
        self._platform_health_cache_time: Optional[datetime] = None
        self._platform_health_cache_ttl = 5  # seconds

        # Reusable HTTP client with connection pooling (Fix #1)
        self._http_client: Optional[httpx.AsyncClient] = None

        # Service endpoints configuration
        self.service_endpoints = {
            ServiceType.CORE_API: "http://localhost:8000/health",
            ServiceType.MEMORY_SERVICE: "http://localhost:13393/health",
            ServiceType.GRAPH_SERVICE: "http://localhost:8002/health",
            ServiceType.BUSINESS_SERVICE: "http://localhost:8003/health",
            ServiceType.UPLOAD_API: "http://localhost:8004/health",
            ServiceType.REDIS: "redis://localhost:6379",
            ServiceType.POSTGRES: "postgresql://localhost:5432",
            ServiceType.PGBOUNCER: "postgresql://localhost:6432",
        }

        # Service dependencies
        self.service_dependencies = {
            ServiceType.CORE_API: [ServiceType.POSTGRES, ServiceType.PGBOUNCER, ServiceType.REDIS],
            ServiceType.MEMORY_SERVICE: [ServiceType.POSTGRES, ServiceType.REDIS],
            ServiceType.GRAPH_SERVICE: [ServiceType.POSTGRES],
            ServiceType.BUSINESS_SERVICE: [ServiceType.POSTGRES, ServiceType.REDIS],
            ServiceType.UPLOAD_API: [ServiceType.POSTGRES, ServiceType.REDIS],
        }

    def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create reusable HTTP client with connection pooling"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=self.timeout, limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
        return self._http_client

    async def close(self):
        """Close HTTP client and cleanup resources"""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def check_http_service(self, service: ServiceType, url: str) -> ContainerHealth:
        """Check HTTP-based service health using reusable HTTP client"""
        start_time = time.time()

        try:
            client = self._get_http_client()
            response = await client.get(url)
            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                uptime = data.get("uptime_seconds", 0)

                # Check dependencies if service reports them
                dependencies = {}
                if "dependencies" in data:
                    for dep_name, dep_status in data["dependencies"].items():
                        if dep_status.get("status") == "healthy":
                            dependencies[dep_name] = ContainerStatus.HEALTHY
                        else:
                            dependencies[dep_name] = ContainerStatus.UNHEALTHY

                return ContainerHealth(
                    service=service,
                    status=ContainerStatus.HEALTHY,
                    response_time_ms=response_time_ms,
                    uptime_seconds=uptime,
                    dependencies=dependencies,
                )
            else:
                return ContainerHealth(
                    service=service,
                    status=ContainerStatus.DEGRADED,
                    response_time_ms=response_time_ms,
                    error=f"HTTP {response.status_code}",
                )

        except httpx.TimeoutException:
            return ContainerHealth(service=service, status=ContainerStatus.UNHEALTHY, error="Timeout")
        except httpx.ConnectError:
            return ContainerHealth(service=service, status=ContainerStatus.UNHEALTHY, error="Connection refused")
        except Exception as e:
            return ContainerHealth(service=service, status=ContainerStatus.UNHEALTHY, error=str(e))

    async def check_redis(self) -> ContainerHealth:
        """Check Redis health"""
        try:
            import redis.asyncio as redis

            client = redis.from_url(self.service_endpoints[ServiceType.REDIS], decode_responses=True)

            start_time = time.time()
            await client.ping()
            response_time_ms = (time.time() - start_time) * 1000

            # Get Redis info
            info = await client.info()
            uptime_seconds = info.get("uptime_in_seconds", 0)
            memory_mb = info.get("used_memory", 0) / (1024 * 1024)

            await client.close()

            return ContainerHealth(
                service=ServiceType.REDIS,
                status=ContainerStatus.HEALTHY,
                response_time_ms=response_time_ms,
                memory_mb=memory_mb,
                uptime_seconds=uptime_seconds,
            )

        except Exception as e:
            return ContainerHealth(service=ServiceType.REDIS, status=ContainerStatus.UNHEALTHY, error=str(e))

    async def check_postgres(self, service: ServiceType, port: int) -> ContainerHealth:
        """Check PostgreSQL/PgBouncer health"""
        try:
            import asyncpg

            start_time = time.time()
            conn = await asyncpg.connect(
                host="localhost",
                port=port,
                user="postgres",
                password="postgres",
                database="ninaivalaigal",
                timeout=self.timeout,
            )

            # Simple query
            await conn.fetchval("SELECT 1")
            response_time_ms = (time.time() - start_time) * 1000

            await conn.close()

            return ContainerHealth(service=service, status=ContainerStatus.HEALTHY, response_time_ms=response_time_ms)

        except Exception as e:
            return ContainerHealth(service=service, status=ContainerStatus.UNHEALTHY, error=str(e))

    async def check_all_services(self) -> Dict[ServiceType, ContainerHealth]:
        """Check health of all services"""
        tasks = []

        # HTTP services
        for service in [
            ServiceType.CORE_API,
            ServiceType.MEMORY_SERVICE,
            ServiceType.GRAPH_SERVICE,
            ServiceType.BUSINESS_SERVICE,
            ServiceType.UPLOAD_API,
        ]:
            if service in self.service_endpoints:
                tasks.append(self.check_http_service(service, self.service_endpoints[service]))

        # Redis
        tasks.append(self.check_redis())

        # PostgreSQL
        tasks.append(self.check_postgres(ServiceType.POSTGRES, 5432))

        # PgBouncer
        tasks.append(self.check_postgres(ServiceType.PGBOUNCER, 6432))

        # Execute all checks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update cache
        health_status = {}
        for result in results:
            if isinstance(result, ContainerHealth):
                health_status[result.service] = result
                self.health_cache[result.service] = result
            elif isinstance(result, Exception):
                logger.error("health_check_failed", error=str(result))

        return health_status

    async def validate_dependencies(self) -> Dict[ServiceType, Dict[str, ContainerStatus]]:
        """Validate service dependencies"""
        dependency_status = {}

        for service, deps in self.service_dependencies.items():
            service_deps = {}
            for dep in deps:
                if dep in self.health_cache:
                    service_deps[dep.value] = self.health_cache[dep].status
                else:
                    service_deps[dep.value] = ContainerStatus.UNKNOWN

            dependency_status[service] = service_deps

        return dependency_status

    async def get_platform_health(self) -> Dict[str, Any]:
        """Get overall platform health status with caching"""
        # Check if cache is valid
        now = datetime.utcnow()
        if (
            self._platform_health_cache is not None
            and self._platform_health_cache_time is not None
            and (now - self._platform_health_cache_time).total_seconds() < self._platform_health_cache_ttl
        ):
            # Return cached result
            return self._platform_health_cache

        # Cache miss or expired - fetch fresh data
        health_status = await self.check_all_services()
        dependency_status = await self.validate_dependencies()

        # Calculate overall status
        statuses = [h.status for h in health_status.values()]
        if all(s == ContainerStatus.HEALTHY for s in statuses):
            overall_status = "healthy"
        elif any(s == ContainerStatus.UNHEALTHY for s in statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        # Count services by status
        status_counts = {
            "healthy": sum(1 for s in statuses if s == ContainerStatus.HEALTHY),
            "degraded": sum(1 for s in statuses if s == ContainerStatus.DEGRADED),
            "unhealthy": sum(1 for s in statuses if s == ContainerStatus.UNHEALTHY),
            "unknown": sum(1 for s in statuses if s == ContainerStatus.UNKNOWN),
        }

        result = {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {s.value: h.to_dict() for s, h in health_status.items()},
            "dependencies": {s.value: deps for s, deps in dependency_status.items()},
            "summary": {"total_services": len(health_status), "status_counts": status_counts},
        }

        # Update cache
        self._platform_health_cache = result
        self._platform_health_cache_time = now

        return result

    async def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            logger.warning("monitoring_already_active")
            return

        self.monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("container_health_monitoring_started", interval=self.check_interval)

    async def stop_monitoring(self):
        """Stop continuous health monitoring"""
        self.monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("container_health_monitoring_stopped")

    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.monitoring_active:
            try:
                await self.check_all_services()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("monitoring_loop_error", error=str(e))
                await asyncio.sleep(self.check_interval)


# Global instance
_monitor: Optional[ContainerHealthMonitor] = None


def get_container_health_monitor() -> ContainerHealthMonitor:
    """Get global container health monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = ContainerHealthMonitor()
    return _monitor


async def initialize_container_monitoring():
    """Initialize and start container health monitoring"""
    monitor = get_container_health_monitor()
    await monitor.start_monitoring()
    return monitor
