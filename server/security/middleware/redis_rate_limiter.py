"""
Redis-backed Rate Limiting Middleware

Production-ready rate limiting with Redis for consistency across all nodes.
"""

import os
import time
from typing import Optional, Tuple

import redis.asyncio as aioredis
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


class RedisRateLimiterMiddleware(BaseHTTPMiddleware):
    """Redis-backed rate limiter for production consistency"""

    def __init__(self, app, limit: int = 100, window: int = 60):
        """
        Initialize Redis rate limiter.

        Args:
            app: FastAPI application
            limit: Maximum requests per window
            window: Time window in seconds
        """
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.redis: Optional[aioredis.Redis] = None

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to requests"""
        if not self.redis:
            try:
                redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
                self.redis = aioredis.from_url(redis_url, decode_responses=True)
            except Exception as e:
                # Fail fast if Redis isn't available
                raise RuntimeError(f"Redis connection failed: {e}")

        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}"

        try:
            # Increment counter in Redis
            current = await self.redis.incr(key)

            if current == 1:
                # First request in window, set expiration
                await self.redis.expire(key, self.window)

            if current > self.limit:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            return await call_next(request)

        except HTTPException:
            raise
        except Exception as e:
            # If Redis fails, fail fast instead of silently falling back
            raise RuntimeError(f"Rate limiting error: {e}")
