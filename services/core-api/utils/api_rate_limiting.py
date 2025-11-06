# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
General API Rate Limiting and Throttling - US-91

Implements comprehensive rate limiting for all API endpoints:
- Per-IP limit: 100 requests/minute
- Per-user limit: 1000 requests/hour
- Per-endpoint custom limits
- In-memory storage (can be migrated to Redis)
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any, Dict, Optional, Tuple

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# US-91 Configuration
PER_IP_LIMIT = 100  # requests per minute
PER_IP_WINDOW = 60  # seconds
PER_USER_LIMIT = 1000  # requests per hour
PER_USER_WINDOW = 3600  # seconds

# Endpoint-specific limits (can override global limits)
ENDPOINT_LIMITS: Dict[str, Dict[str, int]] = {
    "/auth/login": {"limit": 5, "window": 60},  # 5 per minute (already handled by auth rate limiter)
    "/auth/signup": {"limit": 3, "window": 60},  # 3 per minute (already handled by auth rate limiter)
    "/api/memory": {"limit": 100, "window": 60},  # 100 per minute
    "/api/search": {"limit": 50, "window": 60},  # 50 per minute
}

# Whitelist for internal services (CIDR notation or exact IPs)
WHITELIST_IPS = [
    "127.0.0.1",
    "localhost",
    "::1",
    # Add internal service IPs here
]


class APIRateLimiter:
    """General API rate limiter for US-91"""

    def __init__(self):
        # Per-IP tracking
        self.ip_requests: Dict[str, deque] = defaultdict(lambda: deque())

        # Per-user tracking (requires user_id from authenticated requests)
        self.user_requests: Dict[str, deque] = defaultdict(lambda: deque())

        # Endpoint-specific tracking
        self.endpoint_requests: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(lambda: deque()))

    def is_ip_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        if ip in WHITELIST_IPS:
            return True

        # Check CIDR notation (simplified - for exact matches only)
        for whitelist_ip in WHITELIST_IPS:
            if ip == whitelist_ip:
                return True

        return False

    def check_ip_limit(self, ip: str, endpoint: Optional[str] = None) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Check if request from IP is within rate limit.

        Args:
            ip: Client IP address
            endpoint: Optional endpoint path for endpoint-specific limits

        Returns:
            Tuple of (is_allowed, error_message, rate_limit_info)
        """
        # Check whitelist
        if self.is_ip_whitelisted(ip):
            return True, None, {"limit": -1, "remaining": -1, "reset_time": 0, "retry_after": 0, "whitelisted": True}

        now = time.time()

        # Check endpoint-specific limit first
        if endpoint and endpoint in ENDPOINT_LIMITS:
            endpoint_config = ENDPOINT_LIMITS[endpoint]
            limit = endpoint_config["limit"]
            window = endpoint_config["window"]

            # Clean old requests
            endpoint_key = f"{ip}:{endpoint}"
            requests = self.endpoint_requests[endpoint][endpoint_key]

            while requests and requests[0] <= now - window:
                requests.popleft()

            if len(requests) >= limit:
                reset_time = requests[0] + window if requests else now + window
                retry_after = max(0, int(reset_time - now))

                return (
                    False,
                    f"Rate limit exceeded for endpoint {endpoint}. Limit: {limit} requests per {window} seconds.",
                    {
                        "limit": limit,
                        "remaining": 0,
                        "reset_time": int(reset_time),
                        "retry_after": retry_after,
                        "scope": "endpoint",
                    },
                )

            # Record request
            requests.append(now)
            remaining = limit - len(requests)

            return (
                True,
                None,
                {
                    "limit": limit,
                    "remaining": remaining,
                    "reset_time": int(requests[0] + window) if requests else int(now + window),
                    "retry_after": 0,
                    "scope": "endpoint",
                },
            )

        # Check global per-IP limit
        requests = self.ip_requests[ip]

        # Clean old requests (last minute)
        while requests and requests[0] <= now - PER_IP_WINDOW:
            requests.popleft()

        if len(requests) >= PER_IP_LIMIT:
            reset_time = requests[0] + PER_IP_WINDOW if requests else now + PER_IP_WINDOW
            retry_after = max(0, int(reset_time - now))

            return (
                False,
                f"Rate limit exceeded. Limit: {PER_IP_LIMIT} requests per minute.",
                {
                    "limit": PER_IP_LIMIT,
                    "remaining": 0,
                    "reset_time": int(reset_time),
                    "retry_after": retry_after,
                    "scope": "ip",
                },
            )

        # Record request
        requests.append(now)
        remaining = PER_IP_LIMIT - len(requests)

        return (
            True,
            None,
            {
                "limit": PER_IP_LIMIT,
                "remaining": remaining,
                "reset_time": int(requests[0] + PER_IP_WINDOW) if requests else int(now + PER_IP_WINDOW),
                "retry_after": 0,
                "scope": "ip",
            },
        )

    def check_user_limit(
        self, user_id: str, endpoint: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Check if request from authenticated user is within rate limit.

        Args:
            user_id: User ID
            endpoint: Optional endpoint path

        Returns:
            Tuple of (is_allowed, error_message, rate_limit_info)
        """
        now = time.time()

        # Check per-user limit
        requests = self.user_requests[user_id]

        # Clean old requests (last hour)
        while requests and requests[0] <= now - PER_USER_WINDOW:
            requests.popleft()

        if len(requests) >= PER_USER_LIMIT:
            reset_time = requests[0] + PER_USER_WINDOW if requests else now + PER_USER_WINDOW
            retry_after = max(0, int(reset_time - now))

            return (
                False,
                f"Rate limit exceeded. Limit: {PER_USER_LIMIT} requests per hour.",
                {
                    "limit": PER_USER_LIMIT,
                    "remaining": 0,
                    "reset_time": int(reset_time),
                    "retry_after": retry_after,
                    "scope": "user",
                },
            )

        # Record request
        requests.append(now)
        remaining = PER_USER_LIMIT - len(requests)

        return (
            True,
            None,
            {
                "limit": PER_USER_LIMIT,
                "remaining": remaining,
                "reset_time": int(requests[0] + PER_USER_WINDOW) if requests else int(now + PER_USER_WINDOW),
                "retry_after": 0,
                "scope": "user",
            },
        )

    def get_rate_limit_info(
        self, ip: str, user_id: Optional[str] = None, endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get current rate limit information without consuming a request"""
        now = time.time()

        info = {"ip": {}, "user": {}, "endpoint": {}}

        # IP limit info
        if not self.is_ip_whitelisted(ip):
            ip_requests = self.ip_requests[ip]
            while ip_requests and ip_requests[0] <= now - PER_IP_WINDOW:
                ip_requests.popleft()

            info["ip"] = {
                "limit": PER_IP_LIMIT,
                "remaining": max(0, PER_IP_LIMIT - len(ip_requests)),
                "used": len(ip_requests),
                "reset_time": int(ip_requests[0] + PER_IP_WINDOW) if ip_requests else int(now + PER_IP_WINDOW),
            }
        else:
            info["ip"] = {"whitelisted": True}

        # User limit info
        if user_id:
            user_requests = self.user_requests[user_id]
            while user_requests and user_requests[0] <= now - PER_USER_WINDOW:
                user_requests.popleft()

            info["user"] = {
                "limit": PER_USER_LIMIT,
                "remaining": max(0, PER_USER_LIMIT - len(user_requests)),
                "used": len(user_requests),
                "reset_time": int(user_requests[0] + PER_USER_WINDOW) if user_requests else int(now + PER_USER_WINDOW),
            }

        # Endpoint limit info
        if endpoint and endpoint in ENDPOINT_LIMITS:
            endpoint_config = ENDPOINT_LIMITS[endpoint]
            limit = endpoint_config["limit"]
            window = endpoint_config["window"]

            endpoint_key = f"{ip}:{endpoint}"
            endpoint_requests = self.endpoint_requests[endpoint].get(endpoint_key, deque())

            while endpoint_requests and endpoint_requests[0] <= now - window:
                endpoint_requests.popleft()

            info["endpoint"] = {
                "limit": limit,
                "remaining": max(0, limit - len(endpoint_requests)),
                "used": len(endpoint_requests),
                "reset_time": int(endpoint_requests[0] + window) if endpoint_requests else int(now + window),
                "window_seconds": window,
            }

        return info

    def reset_ip_limit(self, ip: str) -> bool:
        """Reset rate limit for an IP (admin function)"""
        if ip in self.ip_requests:
            self.ip_requests[ip].clear()
            return True
        return False

    def reset_user_limit(self, user_id: str) -> bool:
        """Reset rate limit for a user (admin function)"""
        if user_id in self.user_requests:
            self.user_requests[user_id].clear()
            return True
        return False


# Global instance
api_rate_limiter = APIRateLimiter()
