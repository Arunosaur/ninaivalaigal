"""
Response Caching Middleware for Performance Optimization
Implements intelligent caching of API responses with Redis backend
"""

import hashlib
import json
import time
from typing import Dict, Optional, Set

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware for caching API responses to improve performance.

    Features:
    - Caches GET requests only
    - Configurable TTL per endpoint
    - Cache invalidation on data modifications
    - Performance metrics integration
    """

    def __init__(
        self,
        app,
        redis_client,
        default_ttl: int = 300,  # 5 minutes default
        cache_prefix: str = "response_cache",
    ):
        super().__init__(app)
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.cache_prefix = cache_prefix

        # Endpoint-specific TTL configuration
        self.endpoint_ttls: Dict[str, int] = {
            "/health": 30,  # Health checks - short TTL
            "/health/detailed": 60,  # Detailed health - medium TTL
            "/memory/health": 60,  # Memory health - medium TTL
            "/contexts": 300,  # Context lists - longer TTL
            "/memory": 180,  # Memory lists - medium TTL
            "/users": 600,  # User lists - long TTL
        }

        # Endpoints that should never be cached
        self.no_cache_endpoints: Set[str] = {
            "/auth/login",
            "/auth/signup",
            "/auth/token/refresh",
            "/metrics",  # Prometheus metrics should be real-time
        }

        # Cache invalidation patterns
        self.invalidation_patterns: Dict[str, Set[str]] = {
            "POST /memory": {"/memory", "/memory/search", "/contexts"},
            "PUT /memory": {"/memory", "/memory/search"},
            "DELETE /memory": {"/memory", "/memory/search", "/contexts"},
            "POST /contexts": {"/contexts", "/memory"},
            "PUT /contexts": {"/contexts", "/memory"},
            "DELETE /contexts": {"/contexts", "/memory"},
        }

    def generate_cache_key(self, request: Request) -> str:
        """Generate a unique cache key for the request."""
        # Include method, path, query parameters, and user context
        key_components = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items())),
        ]

        # Include user ID if available for user-specific caching
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            key_components.append(f"user:{user_id}")

        # Create hash of components for consistent key length
        key_string = "|".join(key_components)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]

        return f"{self.cache_prefix}:{key_hash}"

    def should_cache_request(self, request: Request) -> bool:
        """Determine if a request should be cached."""
        # Only cache GET requests
        if request.method != "GET":
            return False

        # Check if endpoint is in no-cache list
        if request.url.path in self.no_cache_endpoints:
            return False

        # Don't cache requests with authentication errors
        if hasattr(request.state, "auth_error"):
            return False

        return True

    def get_ttl_for_endpoint(self, path: str) -> int:
        """Get TTL for specific endpoint or return default."""
        return self.endpoint_ttls.get(path, self.default_ttl)

    async def get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Retrieve cached response from Redis."""
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning("Cache retrieval failed", cache_key=cache_key, error=str(e))
        return None

    async def cache_response(
        self, cache_key: str, response_data: Dict, ttl: int
    ) -> None:
        """Store response in Redis cache."""
        try:
            await self.redis.setex(
                cache_key, ttl, json.dumps(response_data, default=str)
            )
            logger.debug("Response cached", cache_key=cache_key, ttl=ttl)
        except Exception as e:
            logger.warning("Cache storage failed", cache_key=cache_key, error=str(e))

    async def invalidate_cache_patterns(self, request: Request) -> None:
        """Invalidate cache entries based on request patterns."""
        invalidation_key = f"{request.method} {request.url.path}"
        patterns_to_invalidate = self.invalidation_patterns.get(invalidation_key, set())

        if patterns_to_invalidate:
            try:
                # Get all cache keys matching patterns
                for pattern in patterns_to_invalidate:
                    cache_pattern = f"{self.cache_prefix}:*{pattern}*"
                    keys_to_delete = await self.redis.keys(cache_pattern)
                    if keys_to_delete:
                        await self.redis.delete(*keys_to_delete)
                        logger.info(
                            "Cache invalidated",
                            pattern=pattern,
                            keys_deleted=len(keys_to_delete),
                        )
            except Exception as e:
                logger.warning("Cache invalidation failed", error=str(e))

    async def dispatch(self, request: Request, call_next):
        """Main middleware logic."""
        start_time = time.time()
        cache_hit = False

        # Check if request should be cached
        if self.should_cache_request(request):
            cache_key = self.generate_cache_key(request)

            # Try to get cached response
            cached_response = await self.get_cached_response(cache_key)
            if cached_response:
                cache_hit = True
                response = Response(
                    content=cached_response["content"],
                    status_code=cached_response["status_code"],
                    headers=cached_response.get("headers", {}),
                    media_type=cached_response.get("media_type", "application/json"),
                )

                # Add cache headers
                response.headers["X-Cache"] = "HIT"
                response.headers["X-Cache-Key"] = cache_key

                # Log cache hit
                duration = time.time() - start_time
                logger.info(
                    "Cache hit",
                    path=request.url.path,
                    cache_key=cache_key,
                    duration_ms=round(duration * 1000, 2),
                )

                return response

        # Process request normally
        response = await call_next(request)
        duration = time.time() - start_time

        # Cache successful responses
        if (
            self.should_cache_request(request)
            and response.status_code == 200
            and hasattr(response, "body")
        ):
            cache_key = self.generate_cache_key(request)
            ttl = self.get_ttl_for_endpoint(request.url.path)

            # Prepare response data for caching
            response_data = {
                "content": response.body.decode() if response.body else "",
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type,
                "cached_at": time.time(),
            }

            await self.cache_response(cache_key, response_data, ttl)

            # Add cache headers
            response.headers["X-Cache"] = "MISS"
            response.headers["X-Cache-Key"] = cache_key
            response.headers["X-Cache-TTL"] = str(ttl)

        # Handle cache invalidation for modifying requests
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            await self.invalidate_cache_patterns(request)

        # Log request performance
        logger.info(
            "Request processed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
            cache_hit=cache_hit,
        )

        return response


class CacheManager:
    """Utility class for manual cache management."""

    def __init__(self, redis_client, cache_prefix: str = "response_cache"):
        self.redis = redis_client
        self.cache_prefix = cache_prefix

    async def clear_all_cache(self) -> int:
        """Clear all cached responses."""
        pattern = f"{self.cache_prefix}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            deleted = await self.redis.delete(*keys)
            logger.info("All cache cleared", keys_deleted=deleted)
            return deleted
        return 0

    async def clear_cache_pattern(self, pattern: str) -> int:
        """Clear cache entries matching a pattern."""
        cache_pattern = f"{self.cache_prefix}:*{pattern}*"
        keys = await self.redis.keys(cache_pattern)
        if keys:
            deleted = await self.redis.delete(*keys)
            logger.info("Cache pattern cleared", pattern=pattern, keys_deleted=deleted)
            return deleted
        return 0

    async def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        pattern = f"{self.cache_prefix}:*"
        keys = await self.redis.keys(pattern)

        stats = {
            "total_keys": len(keys),
            "cache_prefix": self.cache_prefix,
            "sample_keys": keys[:10] if keys else [],
        }

        # Get memory usage if available
        try:
            info = await self.redis.info("memory")
            stats["memory_usage_bytes"] = info.get("used_memory", 0)
            stats["memory_usage_human"] = info.get("used_memory_human", "0B")
        except Exception:
            pass

        return stats
