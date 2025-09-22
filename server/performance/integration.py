"""
Performance Integration Module
Integrates all performance optimizations into the FastAPI application
"""

import time
from typing import Optional

import structlog
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..middleware.response_cache import CacheManager, ResponseCacheMiddleware
from ..redis_client import RedisClient
from .async_optimizer import get_async_optimizer
from .connection_pool import get_optimized_db_manager
from .graph_integration import create_optimized_graph_intelligence
from .graph_optimizer import initialize_graph_performance_optimization
from .query_cache import QueryCache

logger = structlog.get_logger(__name__)


class PerformanceIntegrationMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive performance middleware that integrates all optimizations.
    """

    def __init__(self, app, redis_client, db_manager):
        super().__init__(app)
        self.redis = redis_client
        self.db_manager = db_manager
        self.async_optimizer = get_async_optimizer()

        # Performance tracking
        self.request_count = 0
        self.total_response_time = 0
        self.start_time = time.time()

    async def dispatch(self, request: Request, call_next):
        """Main performance integration logic."""
        start_time = time.time()
        self.request_count += 1

        # Add performance context to request
        request.state.performance_context = {
            "start_time": start_time,
            "request_id": f"req_{int(start_time * 1000)}_{self.request_count}",
            "optimizations_applied": [],
        }

        # Process request
        response = await call_next(request)

        # Calculate performance metrics
        duration = time.time() - start_time
        self.total_response_time += duration

        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        response.headers["X-Request-ID"] = request.state.performance_context[
            "request_id"
        ]

        # Log performance metrics
        logger.info(
            "Request performance",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
            optimizations=request.state.performance_context["optimizations_applied"],
        )

        return response

    def get_performance_summary(self) -> dict:
        """Get overall performance summary."""
        uptime = time.time() - self.start_time
        avg_response_time = self.total_response_time / max(1, self.request_count)

        return {
            "uptime_seconds": uptime,
            "total_requests": self.request_count,
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "requests_per_second": self.request_count / max(1, uptime),
            "optimizer_stats": self.async_optimizer.get_performance_stats(),
        }


class PerformanceManager:
    """
    Central manager for all performance optimizations.
    """

    def __init__(self):
        self.redis_client: Optional[RedisClient] = None
        self.db_manager = None
        self.query_cache: Optional[QueryCache] = None
        self.cache_manager: Optional[CacheManager] = None
        self.graph_optimizer = None
        self.graph_intelligence = None
        self.performance_middleware = None
        self.initialized = False

    async def initialize(
        self,
        app: FastAPI,
        database_url: str,
        redis_client: Optional[RedisClient] = None,
        graph_reasoner=None,
    ):
        """Initialize all performance components including graph optimizations."""
        if self.initialized:
            logger.warning("Performance manager already initialized")
            return

        try:
            # Initialize Redis client if not provided
            if redis_client is None:
                self.redis_client = RedisClient()
                await self.redis_client.connect()
            else:
                self.redis_client = redis_client

            # Initialize optimized database manager
            self.db_manager = get_optimized_db_manager(database_url)

            # Initialize query cache
            self.query_cache = QueryCache(self.redis_client)

            # Initialize cache manager
            self.cache_manager = CacheManager(self.redis_client)

            # Initialize graph performance optimization
            self.graph_optimizer = await initialize_graph_performance_optimization(
                self.redis_client
            )

            # Initialize optimized graph intelligence if graph reasoner is provided
            if graph_reasoner:
                self.graph_intelligence = await create_optimized_graph_intelligence(
                    graph_reasoner, self.redis_client
                )

            # Add response caching middleware
            app.add_middleware(
                ResponseCacheMiddleware,
                redis_client=self.redis_client,
            )

            # Add performance integration middleware
            self.performance_middleware = PerformanceIntegrationMiddleware(
                app, self.redis_client, self.db_manager
            )
            app.add_middleware(
                type(self.performance_middleware),
                redis_client=self.redis_client,
                db_manager=self.db_manager,
            )

            self.initialized = True

            components = [
                "redis_client",
                "optimized_db_manager",
                "query_cache",
                "response_cache_middleware",
                "performance_integration_middleware",
                "graph_optimizer",
            ]

            if self.graph_intelligence:
                components.append("graph_intelligence_optimization")

            logger.info(
                "Performance manager initialized with graph optimizations",
                components=components,
            )

        except Exception as e:
            logger.error("Performance manager initialization failed", error=str(e))
            raise

    async def get_comprehensive_stats(self) -> dict:
        """Get comprehensive performance statistics."""
        if not self.initialized:
            return {"error": "Performance manager not initialized"}

        stats = {
            "performance_manager": {
                "initialized": self.initialized,
                "components_active": [
                    "redis_client",
                    "db_manager",
                    "query_cache",
                    "cache_manager",
                ],
            }
        }

        # Database performance stats
        if self.db_manager:
            stats["database"] = self.db_manager.get_pool_stats()
            stats["database_health"] = self.db_manager.health_check()

        # Query cache stats
        if self.query_cache:
            stats["query_cache"] = await self.query_cache.get_cache_stats()

        # Response cache stats
        if self.cache_manager:
            stats["response_cache"] = await self.cache_manager.get_cache_stats()

        # Graph performance stats
        if self.graph_optimizer:
            stats["graph_optimizer"] = (
                await self.graph_optimizer.get_graph_performance_stats()
            )

        # Graph intelligence stats
        if self.graph_intelligence:
            stats["graph_intelligence"] = (
                await self.graph_intelligence.get_graph_intelligence_performance_stats()
            )

        # Redis performance stats
        if self.redis_client:
            try:
                redis_info = await self.redis_client.redis.info()
                stats["redis"] = {
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "used_memory_human": redis_info.get("used_memory_human", "0B"),
                    "keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "keyspace_misses": redis_info.get("keyspace_misses", 0),
                    "instantaneous_ops_per_sec": redis_info.get(
                        "instantaneous_ops_per_sec", 0
                    ),
                }

                # Calculate cache hit rate
                hits = stats["redis"]["keyspace_hits"]
                misses = stats["redis"]["keyspace_misses"]
                if hits + misses > 0:
                    stats["redis"]["cache_hit_rate"] = hits / (hits + misses)

            except Exception as e:
                stats["redis"] = {"error": str(e)}

        # Overall performance summary
        if self.performance_middleware:
            stats["overall"] = self.performance_middleware.get_performance_summary()

        return stats

    async def optimize_database_pools(self) -> dict:
        """Optimize database connection pools based on usage patterns."""
        if not self.db_manager:
            return {"error": "Database manager not initialized"}

        return self.db_manager.optimize_pool_size()

    async def clear_all_caches(self) -> dict:
        """Clear all caches for troubleshooting."""
        results = {}

        if self.query_cache:
            query_cleared = await self.query_cache.clear_all_cache()
            results["query_cache_cleared"] = query_cleared

        if self.cache_manager:
            response_cleared = await self.cache_manager.clear_all_cache()
            results["response_cache_cleared"] = response_cleared

        # Clear async optimizer cache
        async_optimizer = get_async_optimizer()
        async_optimizer.cache.clear()
        results["async_optimizer_cache_cleared"] = True

        logger.info("All caches cleared", results=results)
        return results

    async def health_check(self) -> dict:
        """Comprehensive health check for all performance components."""
        health = {
            "overall_status": "healthy",
            "components": {},
            "issues": [],
        }

        # Check database health
        if self.db_manager:
            db_health = self.db_manager.health_check()
            health["components"]["database"] = db_health
            if db_health["status"] != "healthy":
                health["overall_status"] = "degraded"
                health["issues"].append("Database connection issues")

        # Check Redis health
        if self.redis_client:
            try:
                await self.redis_client.redis.ping()
                health["components"]["redis"] = {"status": "healthy"}
            except Exception as e:
                health["components"]["redis"] = {"status": "unhealthy", "error": str(e)}
                health["overall_status"] = "degraded"
                health["issues"].append("Redis connection issues")

        # Check cache performance
        stats = await self.get_comprehensive_stats()
        if "redis" in stats and "cache_hit_rate" in stats["redis"]:
            hit_rate = stats["redis"]["cache_hit_rate"]
            if hit_rate < 0.5:  # Less than 50% hit rate
                health["issues"].append(f"Low cache hit rate: {hit_rate:.2%}")
                health["overall_status"] = "degraded"

        return health

    async def cleanup(self):
        """Clean up all performance components."""
        if self.redis_client and hasattr(self.redis_client, "disconnect"):
            await self.redis_client.disconnect()

        if self.db_manager:
            self.db_manager.close()

        # Clean up async optimizer
        async_optimizer = get_async_optimizer()
        async_optimizer.cleanup()

        self.initialized = False
        logger.info("Performance manager cleaned up")


# Global performance manager instance
_performance_manager: Optional[PerformanceManager] = None


def get_performance_manager() -> PerformanceManager:
    """Get the global performance manager instance."""
    global _performance_manager

    if _performance_manager is None:
        _performance_manager = PerformanceManager()

    return _performance_manager


async def initialize_performance_optimizations(
    app: FastAPI,
    database_url: str,
    redis_client: Optional[RedisClient] = None,
):
    """Initialize all performance optimizations for the FastAPI app."""
    manager = get_performance_manager()
    await manager.initialize(app, database_url, redis_client)
    return manager
