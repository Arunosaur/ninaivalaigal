#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Shared dependency providers for the Core API service."""

from __future__ import annotations

from functools import lru_cache

from redis.asyncio import Redis
from redis_client import RateLimiter
from redis_client import get_rate_limiter as _get_rate_limiter
from redis_client import redis_client
from uploads import MultipartUploadService, build_service_from_env


async def get_redis() -> Redis:
    """Return a connected Redis client instance."""

    if not redis_client.is_connected:
        await redis_client.connect()
    if not redis_client.redis:
        raise RuntimeError("Redis client unavailable")
    return redis_client.redis


@lru_cache()
def get_upload_service() -> MultipartUploadService:
    """Return a cached multipart upload service instance."""

    return build_service_from_env()


async def get_rate_limiter() -> RateLimiter:
    """Return the shared rate limiter instance."""

    return await _get_rate_limiter()
