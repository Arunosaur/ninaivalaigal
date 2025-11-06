#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Redis Cache Tests
#
"""
Unit tests for server/billing/redis_cache.py

Tests Redis caching layer for usage quota checks.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from server.billing.models import ResourceType
from server.billing.redis_cache import UsageQuotaCache

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client for testing"""
    try:
        from unittest.mock import MagicMock

        import redis

        mock_client = MagicMock(spec=redis.Redis)
        mock_client.get.return_value = None
        mock_client.set.return_value = True
        mock_client.delete.return_value = 1
        mock_client.exists.return_value = False
        return mock_client
    except ImportError:
        pytest.skip("Redis not available")


@pytest.fixture
def cache_with_mock(mock_redis_client):
    """Create UsageQuotaCache with mock Redis client"""
    return UsageQuotaCache(redis_client=mock_redis_client)


@pytest.fixture
def cache_without_redis():
    """Create UsageQuotaCache without Redis (disabled mode)"""
    return UsageQuotaCache(redis_client=None)


def test_cache_initialization_with_redis(mock_redis_client):
    """Test cache initialization with Redis client"""
    cache = UsageQuotaCache(redis_client=mock_redis_client)
    assert cache.enabled is True
    assert cache.redis_client is not None


def test_cache_initialization_without_redis():
    """Test cache initialization without Redis client"""
    cache = UsageQuotaCache(redis_client=None)
    assert cache.enabled is False


def test_set_current_usage(mock_redis_client, cache_with_mock):
    """Test setting current usage in cache"""
    billing_account_id = uuid4()
    resource_type = ResourceType.STORAGE
    usage = Decimal("100.5")

    cache_with_mock.set_current_usage(billing_account_id, resource_type, usage)

    # Verify Redis set was called
    mock_redis_client.set.assert_called()


def test_get_current_usage(mock_redis_client, cache_with_mock):
    """Test getting current usage from cache"""
    billing_account_id = uuid4()
    resource_type = ResourceType.STORAGE
    expected_usage = Decimal("100.5")

    # Mock Redis get to return cached value
    mock_redis_client.get.return_value = str(expected_usage)

    result = cache_with_mock.get_current_usage(billing_account_id, resource_type)

    assert result == expected_usage
    mock_redis_client.get.assert_called()


def test_get_current_usage_not_found(mock_redis_client, cache_with_mock):
    """Test getting usage when not in cache"""
    billing_account_id = uuid4()
    resource_type = ResourceType.STORAGE

    # Mock Redis get to return None (not cached)
    mock_redis_client.get.return_value = None

    result = cache_with_mock.get_current_usage(billing_account_id, resource_type)

    assert result is None


def test_set_quota_limit(mock_redis_client, cache_with_mock):
    """Test setting quota limit in cache"""
    billing_account_id = uuid4()
    resource_type = ResourceType.STORAGE
    quota = Decimal("1000.0")

    cache_with_mock.set_quota_limit(billing_account_id, resource_type, quota)

    mock_redis_client.set.assert_called()


def test_get_quota_limit(mock_redis_client, cache_with_mock):
    """Test getting quota limit from cache"""
    billing_account_id = uuid4()
    resource_type = ResourceType.STORAGE
    expected_quota = Decimal("1000.0")

    mock_redis_client.get.return_value = str(expected_quota)

    result = cache_with_mock.get_quota_limit(billing_account_id, resource_type)

    assert result == expected_quota


def test_set_usage_percentage(mock_redis_client, cache_with_mock):
    """Test setting usage percentage in cache"""
    billing_account_id = uuid4()
    resource_type = ResourceType.STORAGE
    percentage = 75.5

    cache_with_mock.set_usage_percentage(billing_account_id, resource_type, percentage)

    mock_redis_client.set.assert_called_once()


def test_get_usage_percentage(mock_redis_client, cache_with_mock):
    """Test getting usage percentage from cache"""
    billing_account_id = uuid4()
    resource_type = ResourceType.STORAGE
    expected_percentage = 75.5

    mock_redis_client.get.return_value = str(expected_percentage)

    result = cache_with_mock.get_usage_percentage(billing_account_id, resource_type)

    assert result == expected_percentage


def test_invalidate_usage(mock_redis_client, cache_with_mock):
    """Test invalidating usage cache"""
    billing_account_id = uuid4()
    resource_type = ResourceType.STORAGE

    cache_with_mock.invalidate_usage(billing_account_id, resource_type)

    mock_redis_client.delete.assert_called_once()


def test_invalidate_all(mock_redis_client, cache_with_mock):
    """Test invalidating all cache for a billing account"""
    billing_account_id = uuid4()

    cache_with_mock.invalidate_all(billing_account_id)

    # Should delete multiple keys (usage, quota, percentage for each resource type)
    assert mock_redis_client.delete.call_count >= 1


def test_cache_disabled_operations(cache_without_redis):
    """Test cache operations when Redis is disabled"""
    billing_account_id = uuid4()
    resource_type = ResourceType.STORAGE

    # All operations should return None/False silently when disabled
    assert cache_without_redis.get_current_usage(billing_account_id, resource_type) is None
    assert cache_without_redis.get_quota_limit(billing_account_id, resource_type) is None
    assert cache_without_redis.get_usage_percentage(billing_account_id, resource_type) is None

    # Set operations should not raise errors
    cache_without_redis.set_current_usage(billing_account_id, resource_type, Decimal("100"))
    cache_without_redis.set_quota_limit(billing_account_id, resource_type, Decimal("1000"))
    cache_without_redis.set_usage_percentage(billing_account_id, resource_type, 10.0)
    cache_without_redis.invalidate_usage(billing_account_id, resource_type)
    cache_without_redis.clear_all()
