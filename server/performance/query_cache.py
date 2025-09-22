"""
Database Query Caching for Performance Optimization
Implements intelligent caching of database queries with Redis backend
"""

import hashlib
import json
import time
from typing import Any, Callable, Dict, List, Optional, Union

import structlog

logger = structlog.get_logger(__name__)


class QueryCache:
    """
    Intelligent database query caching system.

    Features:
    - Automatic query result caching
    - Configurable TTL per query type
    - Cache invalidation on data changes
    - Query performance monitoring
    """

    def __init__(
        self,
        redis_client,
        default_ttl: int = 300,  # 5 minutes default
        cache_prefix: str = "query_cache",
    ):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.cache_prefix = cache_prefix

        # Query-specific TTL configuration
        self.query_ttls: Dict[str, int] = {
            "user_list": 600,  # User lists - 10 minutes
            "context_list": 300,  # Context lists - 5 minutes
            "memory_search": 180,  # Memory searches - 3 minutes
            "memory_count": 120,  # Memory counts - 2 minutes
            "health_check": 30,  # Health checks - 30 seconds
            "user_permissions": 300,  # User permissions - 5 minutes
            "organization_data": 600,  # Organization data - 10 minutes
        }

        # Cache invalidation patterns
        self.invalidation_patterns: Dict[str, List[str]] = {
            "memory": ["memory_search", "memory_count", "context_list"],
            "user": ["user_list", "user_permissions"],
            "context": ["context_list", "memory_search"],
            "organization": ["organization_data", "user_list"],
        }

    def generate_cache_key(
        self, query_type: str, params: Dict[str, Any], user_id: Optional[str] = None
    ) -> str:
        """Generate a unique cache key for the query."""
        key_components = [query_type]

        # Add sorted parameters for consistency
        if params:
            sorted_params = sorted(params.items())
            key_components.append(json.dumps(sorted_params, sort_keys=True))

        # Add user context for user-specific queries
        if user_id:
            key_components.append(f"user:{user_id}")

        # Create hash for consistent key length
        key_string = "|".join(str(comp) for comp in key_components)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]

        return f"{self.cache_prefix}:{query_type}:{key_hash}"

    def get_ttl_for_query(self, query_type: str) -> int:
        """Get TTL for specific query type or return default."""
        return self.query_ttls.get(query_type, self.default_ttl)

    async def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Retrieve cached query result from Redis."""
        try:
            start_time = time.time()
            cached_data = await self.redis.get(cache_key)

            if cached_data:
                result = json.loads(cached_data)
                duration = time.time() - start_time

                logger.debug(
                    "Cache hit",
                    cache_key=cache_key,
                    duration_ms=round(duration * 1000, 2),
                )

                return result["data"]

            return None

        except Exception as e:
            logger.warning("Cache retrieval failed", cache_key=cache_key, error=str(e))
            return None

    async def cache_result(
        self,
        cache_key: str,
        result: Any,
        ttl: int,
        query_metadata: Optional[Dict] = None,
    ) -> None:
        """Store query result in Redis cache."""
        try:
            cache_data = {
                "data": result,
                "cached_at": time.time(),
                "ttl": ttl,
                "metadata": query_metadata or {},
            }

            await self.redis.setex(cache_key, ttl, json.dumps(cache_data, default=str))

            logger.debug(
                "Query result cached",
                cache_key=cache_key,
                ttl=ttl,
                result_size=len(str(result)) if result else 0,
            )

        except Exception as e:
            logger.warning("Cache storage failed", cache_key=cache_key, error=str(e))

    async def get_or_execute(
        self,
        query_type: str,
        query_func: Callable,
        params: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        ttl: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Any:
        """
        Get cached result or execute query and cache the result.

        Args:
            query_type: Type of query for cache key generation
            query_func: Async function that executes the query
            params: Query parameters for cache key generation
            user_id: User ID for user-specific caching
            ttl: Custom TTL, uses default if not provided
            force_refresh: Skip cache and force query execution
        """
        params = params or {}
        cache_key = self.generate_cache_key(query_type, params, user_id)
        ttl = ttl or self.get_ttl_for_query(query_type)

        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_result = await self.get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result

        # Execute query
        start_time = time.time()
        try:
            result = await query_func()
            execution_time = time.time() - start_time

            # Cache the result
            query_metadata = {
                "query_type": query_type,
                "execution_time_ms": round(execution_time * 1000, 2),
                "params": params,
            }

            await self.cache_result(cache_key, result, ttl, query_metadata)

            logger.info(
                "Query executed and cached",
                query_type=query_type,
                execution_time_ms=round(execution_time * 1000, 2),
                cache_key=cache_key,
                force_refresh=force_refresh,
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "Query execution failed",
                query_type=query_type,
                execution_time_ms=round(execution_time * 1000, 2),
                error=str(e),
            )
            raise

    async def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern."""
        try:
            cache_pattern = f"{self.cache_prefix}:*{pattern}*"
            keys = await self.redis.keys(cache_pattern)

            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(
                    "Cache invalidated by pattern",
                    pattern=pattern,
                    keys_deleted=deleted,
                )
                return deleted

            return 0

        except Exception as e:
            logger.warning("Cache invalidation failed", pattern=pattern, error=str(e))
            return 0

    async def invalidate_by_type(self, data_type: str) -> int:
        """Invalidate cache entries for a specific data type."""
        patterns = self.invalidation_patterns.get(data_type, [])
        total_deleted = 0

        for pattern in patterns:
            deleted = await self.invalidate_by_pattern(pattern)
            total_deleted += deleted

        if total_deleted > 0:
            logger.info(
                "Cache invalidated by type",
                data_type=data_type,
                total_deleted=total_deleted,
            )

        return total_deleted

    async def clear_all_cache(self) -> int:
        """Clear all cached query results."""
        try:
            pattern = f"{self.cache_prefix}:*"
            keys = await self.redis.keys(pattern)

            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info("All query cache cleared", keys_deleted=deleted)
                return deleted

            return 0

        except Exception as e:
            logger.warning("Cache clear failed", error=str(e))
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        try:
            pattern = f"{self.cache_prefix}:*"
            keys = await self.redis.keys(pattern)

            # Group keys by query type
            query_type_counts: Dict[str, int] = {}
            for key in keys:
                parts = key.split(":")
                if len(parts) >= 3:
                    query_type = parts[2]
                    query_type_counts[query_type] = (
                        query_type_counts.get(query_type, 0) + 1
                    )

            stats = {
                "total_keys": len(keys),
                "cache_prefix": self.cache_prefix,
                "query_type_counts": query_type_counts,
                "configured_ttls": self.query_ttls,
                "invalidation_patterns": self.invalidation_patterns,
            }

            # Get memory usage if available
            try:
                info = await self.redis.info("memory")
                stats["redis_memory_usage"] = {
                    "used_memory_bytes": info.get("used_memory", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
                }
            except Exception:
                pass

            return stats

        except Exception as e:
            logger.warning("Cache stats retrieval failed", error=str(e))
            return {"error": str(e)}


class QueryCacheDecorator:
    """Decorator for automatic query caching."""

    def __init__(self, query_cache: QueryCache):
        self.cache = query_cache

    def cached_query(
        self,
        query_type: str,
        ttl: Optional[int] = None,
        user_specific: bool = False,
    ):
        """
        Decorator to automatically cache query results.

        Args:
            query_type: Type of query for cache key generation
            ttl: Custom TTL, uses default if not provided
            user_specific: Whether to include user context in cache key
        """

        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # Extract user_id if user_specific is True
                user_id = None
                if user_specific and "user_id" in kwargs:
                    user_id = kwargs["user_id"]

                # Create params dict from function arguments
                params = {
                    "args": args,
                    "kwargs": {k: v for k, v in kwargs.items() if k != "user_id"},
                }

                return await self.cache.get_or_execute(
                    query_type=query_type,
                    query_func=lambda: func(*args, **kwargs),
                    params=params,
                    user_id=user_id,
                    ttl=ttl,
                )

            return wrapper

        return decorator
