# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
API Rate Limiting Middleware - US-91

FastAPI middleware that applies rate limiting to all API endpoints.
Integrates with utils.api_rate_limiting for per-IP and per-user limits.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
current_dir = Path(__file__).parent
core_api_dir = current_dir.parent
sys.path.insert(0, str(core_api_dir))

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from utils.api_rate_limiting import api_rate_limiter

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Try X-Forwarded-For first (for reverse proxy setups)
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        # Take the first IP (client IP)
        ip = forwarded_for.split(",")[0].strip()
        if ip:
            return ip

    # Try X-Real-IP
    real_ip = request.headers.get("X-Real-IP", "")
    if real_ip:
        return real_ip

    # Fallback to client host
    if request.client:
        return request.client.host

    return "unknown"


def get_user_id(request: Request) -> Optional[str]:
    """Extract user ID from request (if authenticated)"""
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user_id"):
        return str(request.state.user_id)

    # Try to get from JWT token in Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            import jwt

            token = auth_header.replace("Bearer ", "")
            jwt_secret = os.getenv("NINAIVALAIGAL_JWT_SECRET", os.getenv("NINA_JWT_SECRET", ""))
            if jwt_secret:
                payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
                user_id = payload.get("user_id")
                if user_id:
                    return str(user_id)
        except Exception:
            # If JWT decode fails, continue without user_id
            pass

    return None


class APIRateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for API rate limiting - US-91"""

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to request"""

        # Skip rate limiting for health checks and metrics
        path = request.url.path
        if path in ["/health", "/ready", "/metrics", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Get client IP
        client_ip = get_client_ip(request)

        # Get user ID if authenticated
        user_id = get_user_id(request)

        # Check IP-based rate limit
        is_allowed, error_msg, rate_info = api_rate_limiter.check_ip_limit(ip=client_ip, endpoint=path)

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for IP {client_ip} on {path}",
                ip=client_ip,
                endpoint=path,
                limit=rate_info.get("limit"),
                retry_after=rate_info.get("retry_after"),
            )

            response = Response(
                content=f'{{"detail": "{error_msg or "Rate limit exceeded"}"}}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
            )

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(rate_info.get("limit", 0))
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(rate_info.get("reset_time", 0))
            response.headers["Retry-After"] = str(rate_info.get("retry_after", 0))

            return response

        # Check user-based rate limit (if authenticated)
        if user_id:
            is_allowed, error_msg, user_rate_info = api_rate_limiter.check_user_limit(user_id=user_id, endpoint=path)

            if not is_allowed:
                logger.warning(
                    f"Rate limit exceeded for user {user_id} on {path}",
                    user_id=user_id,
                    endpoint=path,
                    limit=user_rate_info.get("limit"),
                    retry_after=user_rate_info.get("retry_after"),
                )

                response = Response(
                    content=f'{{"detail": "{error_msg or "Rate limit exceeded"}"}}',
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json",
                )

                # Add rate limit headers
                response.headers["X-RateLimit-Limit"] = str(user_rate_info.get("limit", 0))
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = str(user_rate_info.get("reset_time", 0))
                response.headers["Retry-After"] = str(user_rate_info.get("retry_after", 0))

                return response

        # Process request
        response = await call_next(request)

        # Add rate limit headers to successful responses
        rate_info = api_rate_limiter.get_rate_limit_info(ip=client_ip, user_id=user_id, endpoint=path)

        # Add IP rate limit headers
        if "ip" in rate_info and not rate_info["ip"].get("whitelisted"):
            ip_info = rate_info["ip"]
            response.headers["X-RateLimit-Limit"] = str(ip_info.get("limit", 0))
            response.headers["X-RateLimit-Remaining"] = str(ip_info.get("remaining", 0))
            response.headers["X-RateLimit-Reset"] = str(ip_info.get("reset_time", 0))

        # Add user rate limit headers (if authenticated)
        if user_id and "user" in rate_info:
            user_info = rate_info["user"]
            response.headers["X-RateLimit-User-Limit"] = str(user_info.get("limit", 0))
            response.headers["X-RateLimit-User-Remaining"] = str(user_info.get("remaining", 0))
            response.headers["X-RateLimit-User-Reset"] = str(user_info.get("reset_time", 0))

        # Add endpoint-specific headers (if applicable)
        if "endpoint" in rate_info and rate_info["endpoint"]:
            endpoint_info = rate_info["endpoint"]
            response.headers["X-RateLimit-Endpoint-Limit"] = str(endpoint_info.get("limit", 0))
            response.headers["X-RateLimit-Endpoint-Remaining"] = str(endpoint_info.get("remaining", 0))
            response.headers["X-RateLimit-Endpoint-Reset"] = str(endpoint_info.get("reset_time", 0))

        return response
