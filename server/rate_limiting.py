#!/usr/bin/env python3
"""
Rate Limiting and DDoS Protection - Critical P0 security fix
Implements comprehensive rate limiting for API endpoints
"""

import hashlib
import re
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse


class RateLimiter:
    """Token bucket rate limiter with sliding window"""

    def __init__(
        self, max_requests: int, window_seconds: int, burst_allowance: int = None
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.burst_allowance = burst_allowance or max_requests

        # Storage for request timestamps per client
        self.client_requests: dict[str, deque] = defaultdict(lambda: deque())

        # Token bucket storage
        self.token_buckets: dict[str, dict] = defaultdict(
            lambda: {"tokens": self.max_requests, "last_refill": time.time()}
        )

    def is_allowed(self, client_id: str) -> tuple[bool, dict[str, any]]:
        """Check if request is allowed for client"""
        current_time = time.time()

        # Clean old requests (sliding window)
        self._cleanup_old_requests(client_id, current_time)

        # Token bucket algorithm
        bucket = self.token_buckets[client_id]
        time_passed = current_time - bucket["last_refill"]

        # Refill tokens based on time passed
        tokens_to_add = time_passed * (self.max_requests / self.window_seconds)
        bucket["tokens"] = min(self.burst_allowance, bucket["tokens"] + tokens_to_add)
        bucket["last_refill"] = current_time

        # Check if request is allowed
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            self.client_requests[client_id].append(current_time)

            return True, {
                "allowed": True,
                "remaining": int(bucket["tokens"]),
                "reset_time": current_time + self.window_seconds,
                "retry_after": None,
            }
        else:
            # Calculate retry after
            retry_after = self.window_seconds / self.max_requests

            return False, {
                "allowed": False,
                "remaining": 0,
                "reset_time": current_time + self.window_seconds,
                "retry_after": retry_after,
            }

    def _cleanup_old_requests(self, client_id: str, current_time: float):
        """Remove requests older than the window"""
        cutoff_time = current_time - self.window_seconds
        requests = self.client_requests[client_id]

        while requests and requests[0] < cutoff_time:
            requests.popleft()


class EndpointRateLimiter:
    """Rate limiter with different limits per endpoint"""

    def __init__(self):
        # Define rate limits per endpoint pattern
        self.endpoint_limits = {
            "/auth/signup": RateLimiter(
                max_requests=5, window_seconds=300
            ),  # 5 per 5 minutes
            "/auth/login": RateLimiter(
                max_requests=10, window_seconds=300
            ),  # 10 per 5 minutes
            "/auth/": RateLimiter(
                max_requests=20, window_seconds=300
            ),  # 20 per 5 minutes for auth
            "/api/memory": RateLimiter(
                max_requests=100, window_seconds=60
            ),  # 100 per minute
            "/api/": RateLimiter(
                max_requests=200, window_seconds=60
            ),  # 200 per minute general API
            "default": RateLimiter(max_requests=50, window_seconds=60),  # Default limit
        }

        # Global rate limiter for aggressive clients
        self.global_limiter = RateLimiter(
            max_requests=1000, window_seconds=3600
        )  # 1000 per hour

        # Blocked IPs (temporary blocks)
        self.blocked_ips: dict[str, float] = {}
        self.block_duration = 3600  # 1 hour block

    def get_client_id(self, request: Request) -> str:
        """Generate client ID from request"""
        # Try to get real IP from headers (for reverse proxy setups)
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP", "")
            or request.client.host
        )

        # Include user agent for better identification
        user_agent = request.headers.get("User-Agent", "")

        # Create hash for privacy
        client_data = f"{client_ip}:{user_agent}"
        return hashlib.sha256(client_data.encode()).hexdigest()[:16]

    def get_endpoint_pattern(self, path: str) -> str:
        """Get the most specific endpoint pattern for path"""
        # Sort by specificity (longest first)
        patterns = sorted(self.endpoint_limits.keys(), key=len, reverse=True)

        for pattern in patterns:
            if pattern != "default" and path.startswith(pattern):
                return pattern

        return "default"

    async def check_rate_limit(self, request: Request) -> JSONResponse | None:
        """Check rate limit for request, return error response if exceeded"""
        client_id = self.get_client_id(request)
        current_time = time.time()

        # Check if IP is temporarily blocked
        if client_id in self.blocked_ips:
            if current_time < self.blocked_ips[client_id]:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "IP temporarily blocked due to excessive requests",
                        "retry_after": int(self.blocked_ips[client_id] - current_time),
                    },
                )
            else:
                # Block expired, remove it
                del self.blocked_ips[client_id]

        # Check global rate limit first
        global_allowed, global_info = self.global_limiter.is_allowed(client_id)
        if not global_allowed:
            # Block IP for repeated global limit violations
            self.blocked_ips[client_id] = current_time + self.block_duration

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Global rate limit exceeded",
                    "retry_after": global_info["retry_after"],
                },
            )

        # Check endpoint-specific rate limit
        endpoint_pattern = self.get_endpoint_pattern(request.url.path)
        limiter = self.endpoint_limits[endpoint_pattern]

        allowed, info = limiter.is_allowed(client_id)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": f"Rate limit exceeded for {endpoint_pattern}",
                    "retry_after": info["retry_after"],
                    "limit": limiter.max_requests,
                    "window": limiter.window_seconds,
                },
                headers={
                    "X-RateLimit-Limit": str(limiter.max_requests),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(int(info["reset_time"])),
                    "Retry-After": str(int(info["retry_after"])),
                },
            )

        # Request allowed, add rate limit headers
        return None  # No error response needed


class SecurityMiddleware:
    """Additional security middleware for DDoS protection"""

    def __init__(self):
        self.suspicious_patterns = [
            # SQL injection attempts
            r"(?i)(union|select|insert|delete|drop|create|alter|exec)",
            # XSS attempts
            r"(?i)(<script|javascript:|on\w+\s*=)",
            # Path traversal
            r"(\.\./|\.\.\\)",
            # Command injection
            r"[;&|`$()]",
        ]

        # Track suspicious activity
        self.suspicious_clients: dict[str, int] = defaultdict(int)
        self.max_suspicious_requests = 5

    def is_suspicious_request(self, request: Request) -> bool:
        """Check if request contains suspicious patterns"""
        # Check URL path
        if any(
            re.search(pattern, request.url.path) for pattern in self.suspicious_patterns
        ):
            return True

        # Check query parameters
        for param_value in request.query_params.values():
            if any(
                re.search(pattern, param_value) for pattern in self.suspicious_patterns
            ):
                return True

        # Check headers for suspicious content
        suspicious_headers = ["User-Agent", "Referer", "X-Forwarded-For"]
        for header in suspicious_headers:
            header_value = request.headers.get(header, "")
            if any(
                re.search(pattern, header_value) for pattern in self.suspicious_patterns
            ):
                return True

        return False

    async def process_request(
        self, request: Request, rate_limiter: EndpointRateLimiter
    ) -> JSONResponse | None:
        """Process request for security threats"""
        client_id = rate_limiter.get_client_id(request)

        # Check for suspicious patterns
        if self.is_suspicious_request(request):
            self.suspicious_clients[client_id] += 1

            if self.suspicious_clients[client_id] >= self.max_suspicious_requests:
                # Block client temporarily
                rate_limiter.blocked_ips[client_id] = (
                    time.time() + rate_limiter.block_duration
                )

                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Suspicious activity detected. Access temporarily blocked.",
                        "retry_after": rate_limiter.block_duration,
                    },
                )

        return None


# Global instances
_rate_limiter = None
_security_middleware = None


def get_rate_limiter() -> EndpointRateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = EndpointRateLimiter()
    return _rate_limiter


def get_security_middleware() -> SecurityMiddleware:
    """Get global security middleware instance"""
    global _security_middleware
    if _security_middleware is None:
        _security_middleware = SecurityMiddleware()
    return _security_middleware


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting"""
    rate_limiter = get_rate_limiter()
    security_middleware = get_security_middleware()

    # Check security threats first
    security_response = await security_middleware.process_request(request, rate_limiter)
    if security_response:
        return security_response

    # Check rate limits
    rate_limit_response = await rate_limiter.check_rate_limit(request)
    if rate_limit_response:
        return rate_limit_response

    # Process request normally
    response = await call_next(request)

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=31536000; includeSubDomains"

    return response


# Test function
def test_rate_limiting():
    """Test the rate limiting system"""
    limiter = RateLimiter(max_requests=5, window_seconds=60)

    print("Testing rate limiter:")

    # Test normal requests
    for i in range(7):
        allowed, info = limiter.is_allowed("test_client")
        print(
            f"Request {i+1}: {'ALLOWED' if allowed else 'BLOCKED'} - Remaining: {info['remaining']}"
        )

        if not allowed:
            print(f"Retry after: {info['retry_after']} seconds")

    print("\nWaiting for token refill...")
    time.sleep(2)

    # Test after partial refill
    allowed, info = limiter.is_allowed("test_client")
    print(
        f"After wait: {'ALLOWED' if allowed else 'BLOCKED'} - Remaining: {info['remaining']}"
    )


if __name__ == "__main__":
    test_rate_limiting()
