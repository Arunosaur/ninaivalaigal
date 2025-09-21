"""
Redis Client for Ninaivalaigal - SPEC-033 Implementation
Provides Redis connection management, caching, and session storage
"""

import json
import os
from datetime import datetime
from typing import Any

import redis.asyncio as redis
import structlog
from redis.asyncio import Redis

logger = structlog.get_logger(__name__)


class RedisClient:
    """Redis client with connection pooling and caching utilities"""

    def __init__(self):
        self.redis: Redis | None = None
        self.connection_pool = None
        self._connected = False

    async def connect(self):
        """Initialize Redis connection with configuration from environment"""
        try:
            redis_url = os.getenv("REDIS_URL") or os.getenv("NINAIVALAIGAL_REDIS_URL")

            if not redis_url:
                # Fallback to individual components
                host = os.getenv("REDIS_HOST", "localhost")
                port = int(os.getenv("REDIS_PORT", "6379"))
                password = os.getenv("REDIS_PASSWORD", "nina_redis_dev_password")
                db = int(os.getenv("REDIS_DB", "0"))

                redis_url = f"redis://:{password}@{host}:{port}/{db}"

            # Create connection pool
            self.connection_pool = redis.ConnectionPool.from_url(
                redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
            )

            # Create Redis client
            self.redis = Redis(connection_pool=self.connection_pool)

            # Test connection
            await self.redis.ping()
            self._connected = True

            logger.info(
                "Redis connected successfully",
                host=host if "host" in locals() else "from_url",
                port=port if "port" in locals() else "from_url",
            )

        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            self._connected = False
            raise

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            self._connected = False
            logger.info("Redis disconnected")

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self._connected and self.redis is not None

    async def health_check(self) -> dict[str, Any]:
        """Perform Redis health check"""
        if not self.is_connected:
            return {"status": "unhealthy", "error": "Not connected to Redis"}

        try:
            # Test basic operations
            start_time = datetime.utcnow()
            await self.redis.ping()
            ping_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Get Redis info
            info = await self.redis.info()

            return {
                "status": "healthy",
                "ping_ms": round(ping_time, 2),
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime_seconds": info.get("uptime_in_seconds"),
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


class MemoryTokenCache:
    """Redis-backed memory token caching - Core SPEC-033 feature"""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.default_ttl = 3600  # 1 hour
        self.key_prefix = "memory:"

    def _make_key(self, memory_id: str) -> str:
        """Generate Redis key for memory token"""
        return f"{self.key_prefix}{memory_id}"

    async def get(self, memory_id: str) -> dict[str, Any] | None:
        """Get memory token from cache"""
        if not self.redis.is_connected:
            return None

        try:
            key = self._make_key(memory_id)
            cached_data = await self.redis.redis.get(key)

            if cached_data:
                logger.debug("Memory cache hit", memory_id=memory_id)
                return json.loads(cached_data)
            else:
                logger.debug("Memory cache miss", memory_id=memory_id)
                return None

        except Exception as e:
            logger.error("Memory cache get error", memory_id=memory_id, error=str(e))
            return None

    async def set(
        self, memory_id: str, memory_data: dict[str, Any], ttl: int | None = None
    ) -> bool:
        """Set memory token in cache"""
        if not self.redis.is_connected:
            return False

        try:
            key = self._make_key(memory_id)
            ttl = ttl or self.default_ttl

            # Add cache metadata
            cache_data = {
                **memory_data,
                "_cached_at": datetime.utcnow().isoformat(),
                "_ttl": ttl,
            }

            await self.redis.redis.setex(key, ttl, json.dumps(cache_data))
            logger.debug("Memory cached", memory_id=memory_id, ttl=ttl)
            return True

        except Exception as e:
            logger.error("Memory cache set error", memory_id=memory_id, error=str(e))
            return False

    async def delete(self, memory_id: str) -> bool:
        """Delete memory token from cache"""
        if not self.redis.is_connected:
            return False

        try:
            key = self._make_key(memory_id)
            result = await self.redis.redis.delete(key)
            logger.debug(
                "Memory cache deleted", memory_id=memory_id, deleted=bool(result)
            )
            return bool(result)

        except Exception as e:
            logger.error("Memory cache delete error", memory_id=memory_id, error=str(e))
            return False

    async def get_stats(self) -> dict[str, Any]:
        """Get memory cache statistics"""
        if not self.redis.is_connected:
            return {"error": "Redis not connected"}

        try:
            # Count memory keys
            pattern = f"{self.key_prefix}*"
            keys = await self.redis.redis.keys(pattern)

            return {
                "total_cached_memories": len(keys),
                "cache_pattern": pattern,
                "default_ttl_seconds": self.default_ttl,
            }

        except Exception as e:
            logger.error("Memory cache stats error", error=str(e))
            return {"error": str(e)}


class SessionStore:
    """Redis-backed session storage - SPEC-045 synergy"""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.default_ttl = 1800  # 30 minutes
        self.key_prefix = "session:"

    def _make_key(self, user_id: str) -> str:
        """Generate Redis key for user session"""
        return f"{self.key_prefix}{user_id}"

    async def get_session(self, user_id: str) -> dict[str, Any] | None:
        """Get user session from Redis"""
        if not self.redis.is_connected:
            return None

        try:
            key = self._make_key(user_id)
            session_data = await self.redis.redis.get(key)

            if session_data:
                return json.loads(session_data)
            return None

        except Exception as e:
            logger.error("Session get error", user_id=user_id, error=str(e))
            return None

    async def set_session(
        self, user_id: str, session_data: dict[str, Any], ttl: int | None = None
    ) -> bool:
        """Set user session in Redis"""
        if not self.redis.is_connected:
            return False

        try:
            key = self._make_key(user_id)
            ttl = ttl or self.default_ttl

            # Add session metadata
            enhanced_data = {
                **session_data,
                "created_at": datetime.utcnow().isoformat(),
                "expires_in": ttl,
            }

            await self.redis.redis.setex(key, ttl, json.dumps(enhanced_data))
            logger.debug("Session stored", user_id=user_id, ttl=ttl)
            return True

        except Exception as e:
            logger.error("Session set error", user_id=user_id, error=str(e))
            return False

    async def delete_session(self, user_id: str) -> bool:
        """Delete user session from Redis"""
        if not self.redis.is_connected:
            return False

        try:
            key = self._make_key(user_id)
            result = await self.redis.redis.delete(key)
            logger.debug("Session deleted", user_id=user_id)
            return bool(result)

        except Exception as e:
            logger.error("Session delete error", user_id=user_id, error=str(e))
            return False


class RateLimiter:
    """Redis-backed API rate limiting"""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.key_prefix = "rate:"

    def _make_key(self, user_id: str, endpoint: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"{self.key_prefix}{user_id}:{endpoint}"

    async def is_allowed(
        self, user_id: str, endpoint: str, limit: int = 100, window: int = 60
    ) -> tuple[bool, dict[str, Any]]:
        """Check if request is allowed under rate limit"""
        if not self.redis.is_connected:
            return True, {"error": "Rate limiter unavailable"}

        try:
            key = self._make_key(user_id, endpoint)

            # Use sliding window counter
            current_time = int(datetime.utcnow().timestamp())
            window_start = current_time - window

            # Remove old entries
            await self.redis.redis.zremrangebyscore(key, 0, window_start)

            # Count current requests
            current_count = await self.redis.redis.zcard(key)

            if current_count >= limit:
                return False, {
                    "allowed": False,
                    "limit": limit,
                    "remaining": 0,
                    "reset_at": current_time + window,
                }

            # Add current request
            await self.redis.redis.zadd(key, {str(current_time): current_time})
            await self.redis.redis.expire(key, window)

            return True, {
                "allowed": True,
                "limit": limit,
                "remaining": limit - current_count - 1,
                "reset_at": current_time + window,
            }

        except Exception as e:
            logger.error(
                "Rate limit check error",
                user_id=user_id,
                endpoint=endpoint,
                error=str(e),
            )
            return True, {"error": str(e)}


# Global Redis client instance
redis_client = RedisClient()
memory_cache = MemoryTokenCache(redis_client)
session_store = SessionStore(redis_client)
rate_limiter = RateLimiter(redis_client)


async def get_redis_client() -> RedisClient:
    """Dependency injection for Redis client"""
    if not redis_client.is_connected:
        await redis_client.connect()
    return redis_client


async def get_memory_cache() -> MemoryTokenCache:
    """Dependency injection for memory cache"""
    if not redis_client.is_connected:
        await redis_client.connect()
    return memory_cache


async def get_session_store() -> SessionStore:
    """Dependency injection for session store"""
    if not redis_client.is_connected:
        await redis_client.connect()
    return session_store


async def get_rate_limiter() -> RateLimiter:
    """Dependency injection for rate limiter"""
    if not redis_client.is_connected:
        await redis_client.connect()
    return rate_limiter
