#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Redis Caching for Usage Quotas
# Developer D - January 2025
#
# BILL-002: Redis integration for real-time quota checks

"""
Redis caching layer for usage quota checks.

Reduces database load by caching:
- Current usage per billing account and resource type
- Quota limits
- Usage percentages
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional, Tuple
from uuid import UUID

try:
    import redis

    REDIS_AVAILABLE = True
    # Type hint for Redis client
    if hasattr(redis, "Redis"):
        RedisType = redis.Redis
    else:
        RedisType = None  # type: ignore
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore
    RedisType = None  # type: ignore

from .models import ResourceType


class UsageQuotaCache:
    """
    Redis cache for usage quota data.

    Cache keys:
    - usage:{billing_account_id}:{resource_type} -> current usage (Decimal)
    - quota:{billing_account_id}:{resource_type} -> quota limit (Decimal)
    - percentage:{billing_account_id}:{resource_type} -> usage percentage (float)

    TTL: 60 seconds (1 minute)
    """

    CACHE_TTL = 60  # 1 minute
    KEY_PREFIX = "billing:usage"

    def __init__(self, redis_client: Optional[Any] = None):
        """
        Initialize usage quota cache.

        Args:
            redis_client: Redis client instance (optional, will try to get from app state)
        """
        self.redis_client = redis_client
        self.enabled = REDIS_AVAILABLE and redis_client is not None

    def _get_redis(self):
        """Get Redis client (lazy initialization)"""
        if not self.enabled:
            return None

        if self.redis_client is None:
            # Try to get from global state or create new connection
            try:
                import redis

                # Default connection - in production, get from app state
                self.redis_client = redis.Redis(
                    host="localhost",
                    port=6379,
                    db=0,
                    decode_responses=False,  # Store as bytes for Decimal compatibility
                )
            except Exception:
                self.enabled = False
                return None

        return self.redis_client

    def get_current_usage(self, billing_account_id: UUID, resource_type: ResourceType) -> Optional[Decimal]:
        """
        Get current usage from cache.

        Args:
            billing_account_id: Billing account ID
            resource_type: Resource type

        Returns:
            Current usage as Decimal, or None if not cached
        """
        if not self.enabled:
            return None

        redis_client = self._get_redis()
        if not redis_client:
            return None

        key = f"{self.KEY_PREFIX}:{billing_account_id}:{resource_type.value}"

        try:
            value = redis_client.get(key)
            if value is None:
                return None

            # Decode from bytes and convert to Decimal
            if isinstance(value, bytes):
                value = value.decode("utf-8")
            return Decimal(value)
        except Exception:
            # Cache miss or error - return None to fall back to DB
            return None

    def set_current_usage(
        self, billing_account_id: UUID, resource_type: ResourceType, usage: Decimal, ttl: Optional[int] = None
    ):
        """
        Cache current usage.

        Args:
            billing_account_id: Billing account ID
            resource_type: Resource type
            usage: Current usage value
            ttl: Optional TTL override (default: CACHE_TTL)
        """
        if not self.enabled:
            return

        redis_client = self._get_redis()
        if not redis_client:
            return

        key = f"{self.KEY_PREFIX}:{billing_account_id}:{resource_type.value}"
        ttl = ttl or self.CACHE_TTL

        try:
            # Store as string for Decimal compatibility
            redis_client.setex(key, ttl, str(usage))
        except Exception:
            # Ignore cache errors - not critical
            pass

    def get_quota_limit(self, billing_account_id: UUID, resource_type: ResourceType) -> Optional[Decimal]:
        """
        Get quota limit from cache.

        Args:
            billing_account_id: Billing account ID
            resource_type: Resource type

        Returns:
            Quota limit as Decimal, or None if not cached
        """
        if not self.enabled:
            return None

        redis_client = self._get_redis()
        if not redis_client:
            return None

        key = f"{self.KEY_PREFIX}:quota:{billing_account_id}:{resource_type.value}"

        try:
            value = redis_client.get(key)
            if value is None:
                return None

            if isinstance(value, bytes):
                value = value.decode("utf-8")
            return Decimal(value)
        except Exception:
            return None

    def set_quota_limit(
        self, billing_account_id: UUID, resource_type: ResourceType, limit: Decimal, ttl: Optional[int] = None
    ):
        """
        Cache quota limit.

        Args:
            billing_account_id: Billing account ID
            resource_type: Resource type
            limit: Quota limit value
            ttl: Optional TTL override
        """
        if not self.enabled:
            return

        redis_client = self._get_redis()
        if not redis_client:
            return

        key = f"{self.KEY_PREFIX}:quota:{billing_account_id}:{resource_type.value}"
        ttl = ttl or self.CACHE_TTL * 10  # Longer TTL for quotas (10 minutes)

        try:
            redis_client.setex(key, ttl, str(limit))
        except Exception:
            pass

    def get_usage_percentage(self, billing_account_id: UUID, resource_type: ResourceType) -> Optional[float]:
        """
        Get usage percentage from cache.

        Args:
            billing_account_id: Billing account ID
            resource_type: Resource type

        Returns:
            Usage percentage as float, or None if not cached
        """
        if not self.enabled:
            return None

        redis_client = self._get_redis()
        if not redis_client:
            return None

        key = f"{self.KEY_PREFIX}:percentage:{billing_account_id}:{resource_type.value}"

        try:
            value = redis_client.get(key)
            if value is None:
                return None

            if isinstance(value, bytes):
                value = value.decode("utf-8")
            return float(value)
        except Exception:
            return None

    def set_usage_percentage(
        self, billing_account_id: UUID, resource_type: ResourceType, percentage: float, ttl: Optional[int] = None
    ):
        """
        Cache usage percentage.

        Args:
            billing_account_id: Billing account ID
            resource_type: Resource type
            percentage: Usage percentage
            ttl: Optional TTL override
        """
        if not self.enabled:
            return

        redis_client = self._get_redis()
        if not redis_client:
            return

        key = f"{self.KEY_PREFIX}:percentage:{billing_account_id}:{resource_type.value}"
        ttl = ttl or self.CACHE_TTL

        try:
            redis_client.setex(key, ttl, str(percentage))
        except Exception:
            pass

    def invalidate_usage(self, billing_account_id: UUID, resource_type: Optional[ResourceType] = None):
        """
        Invalidate usage cache for billing account.

        Args:
            billing_account_id: Billing account ID
            resource_type: Optional resource type (if None, invalidate all)
        """
        if not self.enabled:
            return

        redis_client = self._get_redis()
        if not redis_client:
            return

        try:
            if resource_type:
                # Invalidate specific resource type
                pattern = f"{self.KEY_PREFIX}:{billing_account_id}:{resource_type.value}*"
                keys = redis_client.keys(pattern)
                if keys:
                    redis_client.delete(*keys)
            else:
                # Invalidate all resource types for account
                pattern = f"{self.KEY_PREFIX}:{billing_account_id}:*"
                keys = redis_client.keys(pattern)
                if keys:
                    redis_client.delete(*keys)
        except Exception:
            pass

    def clear_all(self):
        """Clear all usage cache (use with caution)"""
        if not self.enabled:
            return

        redis_client = self._get_redis()
        if not redis_client:
            return

        try:
            pattern = f"{self.KEY_PREFIX}:*"
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
        except Exception:
            pass
