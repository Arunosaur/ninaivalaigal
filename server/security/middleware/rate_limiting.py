"""
Enhanced Rate Limiting Middleware

RBAC-aware rate limiting with different limits based on user roles and endpoint sensitivity.
"""

import asyncio
import os
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from rbac.permissions import Role


class RateLimitType(Enum):
    """Types of rate limiting"""

    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    CONCURRENT_REQUESTS = "concurrent_requests"


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""

    limit: int
    window_seconds: int
    limit_type: RateLimitType
    burst_allowance: int = 0


class TokenBucket:
    """Token bucket algorithm for rate limiting"""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket"""
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now


class SlidingWindowCounter:
    """Sliding window counter for rate limiting"""

    def __init__(self, window_seconds: int, limit: int):
        self.window_seconds = window_seconds
        self.limit = limit
        self.requests = deque()

    def is_allowed(self) -> bool:
        """Check if request is allowed within the sliding window"""
        now = time.time()

        # Remove old requests outside the window
        while self.requests and self.requests[0] <= now - self.window_seconds:
            self.requests.popleft()

        # Check if we're under the limit
        if len(self.requests) < self.limit:
            self.requests.append(now)
            return True

        return False

    def get_reset_time(self) -> float:
        """Get time when the oldest request will expire"""
        if not self.requests:
            return 0
        return self.requests[0] + self.window_seconds


class EnhancedRateLimiter:
    """Enhanced rate limiter with RBAC awareness"""

    def __init__(self):
        # Rate limits by endpoint pattern and role
        self.endpoint_limits = {
            # Authentication endpoints (stricter limits)
            "/auth/login": {
                Role.VIEWER: RateLimitConfig(
                    5, 300, RateLimitType.REQUESTS_PER_MINUTE
                ),  # 5 per 5 min
                Role.MEMBER: RateLimitConfig(5, 300, RateLimitType.REQUESTS_PER_MINUTE),
                Role.ADMIN: RateLimitConfig(10, 300, RateLimitType.REQUESTS_PER_MINUTE),
                Role.OWNER: RateLimitConfig(15, 300, RateLimitType.REQUESTS_PER_MINUTE),
                Role.SYSTEM: RateLimitConfig(
                    50, 300, RateLimitType.REQUESTS_PER_MINUTE
                ),
                "anonymous": RateLimitConfig(3, 300, RateLimitType.REQUESTS_PER_MINUTE),
            },
            "/auth/signup": {
                "anonymous": RateLimitConfig(
                    3, 600, RateLimitType.REQUESTS_PER_MINUTE
                )  # 3 per 10 min
            },
            # Memory operations
            "/memory": {
                Role.VIEWER: RateLimitConfig(50, 60, RateLimitType.REQUESTS_PER_MINUTE),
                Role.MEMBER: RateLimitConfig(
                    100, 60, RateLimitType.REQUESTS_PER_MINUTE
                ),
                Role.ADMIN: RateLimitConfig(200, 60, RateLimitType.REQUESTS_PER_MINUTE),
                Role.OWNER: RateLimitConfig(300, 60, RateLimitType.REQUESTS_PER_MINUTE),
                Role.SYSTEM: RateLimitConfig(
                    1000, 60, RateLimitType.REQUESTS_PER_MINUTE
                ),
            },
            # Context operations
            "/contexts": {
                Role.VIEWER: RateLimitConfig(30, 60, RateLimitType.REQUESTS_PER_MINUTE),
                Role.MEMBER: RateLimitConfig(50, 60, RateLimitType.REQUESTS_PER_MINUTE),
                Role.ADMIN: RateLimitConfig(100, 60, RateLimitType.REQUESTS_PER_MINUTE),
                Role.OWNER: RateLimitConfig(150, 60, RateLimitType.REQUESTS_PER_MINUTE),
                Role.SYSTEM: RateLimitConfig(
                    500, 60, RateLimitType.REQUESTS_PER_MINUTE
                ),
            },
            # RBAC operations (more restrictive)
            "/rbac/": {
                Role.VIEWER: RateLimitConfig(
                    10, 300, RateLimitType.REQUESTS_PER_MINUTE
                ),
                Role.MEMBER: RateLimitConfig(
                    15, 300, RateLimitType.REQUESTS_PER_MINUTE
                ),
                Role.ADMIN: RateLimitConfig(30, 300, RateLimitType.REQUESTS_PER_MINUTE),
                Role.OWNER: RateLimitConfig(50, 300, RateLimitType.REQUESTS_PER_MINUTE),
                Role.SYSTEM: RateLimitConfig(
                    100, 300, RateLimitType.REQUESTS_PER_MINUTE
                ),
            },
            # Admin operations (very restrictive)
            "/admin/": {
                Role.ADMIN: RateLimitConfig(
                    20, 3600, RateLimitType.REQUESTS_PER_HOUR
                ),  # 20 per hour
                Role.OWNER: RateLimitConfig(50, 3600, RateLimitType.REQUESTS_PER_HOUR),
                Role.SYSTEM: RateLimitConfig(
                    200, 3600, RateLimitType.REQUESTS_PER_HOUR
                ),
            },
        }

        # Storage for rate limit counters
        self.counters = defaultdict(dict)  # {user_id: {endpoint: counter}}
        self.token_buckets = defaultdict(dict)  # {user_id: {endpoint: bucket}}

        # Concurrent request tracking
        self.concurrent_requests = defaultdict(int)

        self.redis_client = None
        self.local_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self._cleanup_task = None
        self._cleanup_started = False

    def _start_cleanup_task(self):
        """Start background task to clean up old counters"""
        if self._cleanup_started:
            return

        try:

            async def cleanup():
                while True:
                    await asyncio.sleep(300)  # Clean up every 5 minutes
                    await self._cleanup_old_counters()

            self._cleanup_task = asyncio.create_task(cleanup())
            self._cleanup_started = True
        except RuntimeError:
            # No event loop running, defer cleanup task creation
            pass

    async def _cleanup_old_counters(self):
        """Remove old counters to prevent memory leaks"""
        current_time = time.time()

        # Clean up sliding window counters
        for user_id in list(self.counters.keys()):
            for endpoint in list(self.counters[user_id].keys()):
                counter = self.counters[user_id][endpoint]
                if hasattr(counter, "requests") and counter.requests:
                    # Remove if no recent requests
                    if counter.requests[-1] < current_time - 3600:  # 1 hour old
                        del self.counters[user_id][endpoint]

            # Remove user if no counters left
            if not self.counters[user_id]:
                del self.counters[user_id]

    async def check_rate_limit(self, request: Request) -> tuple[bool, dict | None]:
        """
        Check if request is within rate limits.

        Args:
            request: FastAPI request object

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        # Get user identification
        user_id, user_role = self._get_user_info(request)

        # Get endpoint pattern and rate limit config
        endpoint_pattern = self._get_endpoint_pattern(request.url.path)
        rate_config = self._get_rate_config(endpoint_pattern, user_role)

        if not rate_config:
            return True, None  # No rate limit configured

        # Check rate limit
        is_allowed = await self._check_limit(user_id, endpoint_pattern, rate_config)

        # Prepare rate limit info for headers
        rate_limit_info = {
            "limit": rate_config.limit,
            "window_seconds": rate_config.window_seconds,
            "remaining": self._get_remaining_requests(
                user_id, endpoint_pattern, rate_config
            ),
            "reset_time": self._get_reset_time(user_id, endpoint_pattern, rate_config),
        }

        return is_allowed, rate_limit_info

    def _get_user_info(self, request: Request) -> tuple[str, str]:
        """Get user ID and role from request"""
        rbac_context = getattr(request.state, "rbac_context", None)

        if rbac_context:
            user_id = str(rbac_context.user_id)
            user_role = rbac_context.user_role
        else:
            # Anonymous user - use IP address
            user_id = (
                f"anon_{request.client.host}" if request.client else "anon_unknown"
            )
            user_role = "anonymous"

        return user_id, user_role

    def _get_endpoint_pattern(self, path: str) -> str:
        """Get endpoint pattern for rate limiting"""
        for pattern in self.endpoint_limits.keys():
            if path.startswith(pattern):
                return pattern
        return "default"

    def _get_rate_config(
        self, endpoint_pattern: str, user_role
    ) -> RateLimitConfig | None:
        """Get rate limit configuration for endpoint and role"""
        endpoint_config = self.endpoint_limits.get(endpoint_pattern, {})

        # Try to get config for specific role
        if isinstance(user_role, Role):
            config = endpoint_config.get(user_role)
        else:
            config = endpoint_config.get(user_role)

        # Fallback to default if no specific config
        if not config and "default" in endpoint_config:
            config = endpoint_config["default"]

        return config

    async def is_rate_limited(
        self, user_id: str, endpoint: str
    ) -> tuple[bool, dict[str, Any]]:
        # Start cleanup task if not already started
        if not self._cleanup_started:
            self._start_cleanup_task()

        # Get endpoint pattern and rate limit config
        endpoint_pattern = self._get_endpoint_pattern(endpoint)
        rate_config = self._get_rate_config(endpoint_pattern, "anonymous")

        if not rate_config:
            return False, {}

        # Check rate limit
        is_allowed = await self._check_limit(user_id, endpoint_pattern, rate_config)

        # Prepare rate limit info for headers
        rate_limit_info = {
            "limit": rate_config.limit,
            "window_seconds": rate_config.window_seconds,
            "remaining": self._get_remaining_requests(
                user_id, endpoint_pattern, rate_config
            ),
            "reset_time": self._get_reset_time(user_id, endpoint_pattern, rate_config),
        }

        return not is_allowed, rate_limit_info

    async def _check_limit(
        self, user_id: str, endpoint: str, config: RateLimitConfig
    ) -> bool:
        """Check if request is within limits"""

        if config.limit_type == RateLimitType.REQUESTS_PER_MINUTE:
            return self._check_sliding_window(user_id, endpoint, config)

        elif config.limit_type == RateLimitType.REQUESTS_PER_HOUR:
            return self._check_sliding_window(user_id, endpoint, config)

        elif config.limit_type == RateLimitType.CONCURRENT_REQUESTS:
            return self._check_concurrent_limit(user_id, endpoint, config)

        return True

    def _check_sliding_window(
        self, user_id: str, endpoint: str, config: RateLimitConfig
    ) -> bool:
        """Check sliding window rate limit"""
        key = f"{user_id}:{endpoint}"

        if key not in self.counters[user_id]:
            self.counters[user_id][key] = SlidingWindowCounter(
                config.window_seconds, config.limit
            )

        counter = self.counters[user_id][key]
        return counter.is_allowed()

    def _check_concurrent_limit(
        self, user_id: str, endpoint: str, config: RateLimitConfig
    ) -> bool:
        """Check concurrent request limit"""
        key = f"{user_id}:{endpoint}"
        current_concurrent = self.concurrent_requests[key]

        return current_concurrent < config.limit

    def _get_remaining_requests(
        self, user_id: str, endpoint: str, config: RateLimitConfig
    ) -> int:
        """Get remaining requests in current window"""
        key = f"{user_id}:{endpoint}"

        if key in self.counters[user_id]:
            counter = self.counters[user_id][key]
            if hasattr(counter, "requests"):
                return max(0, config.limit - len(counter.requests))

        return config.limit

    def _get_reset_time(
        self, user_id: str, endpoint: str, config: RateLimitConfig
    ) -> float:
        """Get time when rate limit resets"""
        key = f"{user_id}:{endpoint}"

        if key in self.counters[user_id]:
            counter = self.counters[user_id][key]
            if hasattr(counter, "get_reset_time"):
                return counter.get_reset_time()

        return time.time() + config.window_seconds

    def increment_concurrent(self, user_id: str, endpoint: str):
        """Increment concurrent request counter"""
        key = f"{user_id}:{endpoint}"
        self.concurrent_requests[key] += 1

    def decrement_concurrent(self, user_id: str, endpoint: str):
        """Decrement concurrent request counter"""
        key = f"{user_id}:{endpoint}"
        if self.concurrent_requests[key] > 0:
            self.concurrent_requests[key] -= 1


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""

    def __init__(self, app, rate_limiter: EnhancedRateLimiter | None = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or EnhancedRateLimiter()

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to requests"""

        # Check rate limit
        is_allowed, rate_info = await self.rate_limiter.check_rate_limit(request)

        if not is_allowed:
            # Rate limit exceeded
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(rate_info["reset_time"])),
                    "Retry-After": str(int(rate_info["reset_time"] - time.time())),
                },
            )

        # Track concurrent requests
        user_id, _ = self.rate_limiter._get_user_info(request)
        endpoint = self.rate_limiter._get_endpoint_pattern(request.url.path)

        self.rate_limiter.increment_concurrent(user_id, endpoint)

        try:
            # Process request
            response = await call_next(request)

            # Add rate limit headers
            if rate_info:
                response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
                response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(
                    int(rate_info["reset_time"])
                )

            return response

        finally:
            # Decrement concurrent counter
            self.rate_limiter.decrement_concurrent(user_id, endpoint)
