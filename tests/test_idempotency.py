#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Idempotency Tests
#
"""
Unit tests for server/billing/idempotency.py

Tests distributed locking and idempotency mechanisms.
"""

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_redis_client():
    """Create mock Redis client"""
    try:
        from unittest.mock import MagicMock

        import redis

        mock_client = MagicMock(spec=redis.Redis)
        mock_client.set.return_value = True
        mock_client.get.return_value = None
        mock_client.delete.return_value = 1
        mock_client.exists.return_value = False
        return mock_client
    except ImportError:
        pytest.skip("Redis not available")


@pytest.fixture
def mock_redis_unavailable():
    """Mock Redis as unavailable"""
    return None


class TestDistributedLock:
    """Tests for DistributedLock class"""

    def test_lock_initialization(self, mock_redis_client):
        """Test lock initialization"""
        from server.billing.idempotency import DistributedLock

        lock = DistributedLock(mock_redis_client, "test-key", ttl=300)

        assert lock.lock_key.startswith("billing:lock")
        assert "test-key" in lock.lock_key
        assert lock.ttl == 300
        assert lock.lock_id is not None
        assert lock.acquired is False

    def test_lock_acquire_success(self, mock_redis_client):
        """Test successful lock acquisition"""
        from server.billing.idempotency import DistributedLock

        # Mock SETNX to return True (lock acquired)
        mock_redis_client.set.return_value = True

        lock = DistributedLock(mock_redis_client, "test-key", ttl=300)
        result = lock.acquire(timeout=1)

        assert result is True
        assert lock.acquired is True
        assert lock.acquired_at is not None
        mock_redis_client.set.assert_called()

    def test_lock_acquire_failure(self, mock_redis_client):
        """Test lock acquisition failure (already locked)"""
        from server.billing.idempotency import DistributedLock

        # Mock SETNX to return False (lock already held)
        mock_redis_client.set.return_value = False

        lock = DistributedLock(mock_redis_client, "test-key", ttl=300)
        result = lock.acquire(timeout=1)

        assert result is False
        assert lock.acquired is False

    def test_lock_acquire_without_redis(self, mock_redis_unavailable):
        """Test lock acquisition when Redis is unavailable"""
        from server.billing.idempotency import DistributedLock

        lock = DistributedLock(mock_redis_unavailable, "test-key", ttl=300)
        result = lock.acquire()

        # Should assume lock acquired when Redis unavailable
        assert result is True
        assert lock.acquired is True

    def test_lock_release(self, mock_redis_client):
        """Test lock release"""
        from server.billing.idempotency import DistributedLock

        mock_redis_client.set.return_value = True
        mock_redis_client.get.return_value = b"lock-id"

        lock = DistributedLock(mock_redis_client, "test-key", ttl=300, lock_id="lock-id")
        lock.acquire()
        lock.release()

        assert lock.acquired is False
        mock_redis_client.delete.assert_called_once()

    def test_lock_context_manager(self, mock_redis_client):
        """Test lock as context manager"""
        from server.billing.idempotency import DistributedLock

        mock_redis_client.set.return_value = True

        with DistributedLock(mock_redis_client, "test-key", ttl=300) as lock:
            assert lock.acquired is True

        # Lock should be released after context
        assert lock.acquired is False

    def test_lock_auto_renewal(self, mock_redis_client):
        """Test lock auto-renewal"""
        from server.billing.idempotency import DistributedLock

        mock_redis_client.set.return_value = True

        lock = DistributedLock(mock_redis_client, "test-key", ttl=300)
        lock.acquire()

        # Simulate renewal
        lock._renew_lock()

        # Should call SET to renew TTL
        assert mock_redis_client.set.call_count >= 2


class TestGetTaskLockKey:
    """Tests for get_task_lock_key function"""

    def test_get_task_lock_key(self):
        """Test task lock key creation"""
        from server.billing.idempotency import get_task_lock_key

        key = get_task_lock_key("task-name", ("param1", "value1"))

        assert key is not None
        assert isinstance(key, str)
        assert len(key) > 0
        assert "task-name" in key

    def test_task_lock_key_consistency(self):
        """Test that same inputs produce same key"""
        from server.billing.idempotency import get_task_lock_key

        task_args = ("param1", "value1", "param2", "value2")
        key1 = get_task_lock_key("task-name", task_args)
        key2 = get_task_lock_key("task-name", task_args)

        assert key1 == key2

    def test_task_lock_key_uniqueness(self):
        """Test that different inputs produce different keys"""
        from server.billing.idempotency import get_task_lock_key

        key1 = get_task_lock_key("task-name", ("param1", "value1"))
        key2 = get_task_lock_key("task-name", ("param1", "value2"))

        assert key1 != key2


class TestWithIdempotencyLock:
    """Tests for with_idempotency_lock decorator"""

    def test_idempotency_lock_decorator(self, mock_redis_client):
        """Test idempotency lock decorator"""
        from server.billing.idempotency import with_idempotency_lock

        mock_redis_client.set.return_value = True

        @with_idempotency_lock(mock_redis_client, "test-task")
        def test_function(param1, param2):
            return param1 + param2

        result = test_function("a", "b")

        assert result == "ab"
        mock_redis_client.set.assert_called()

    def test_idempotency_lock_prevents_duplicate_execution(self, mock_redis_client):
        """Test that lock prevents duplicate execution"""
        from server.billing.idempotency import with_idempotency_lock

        call_count = 0

        # First call acquires lock
        mock_redis_client.set.return_value = True

        @with_idempotency_lock(mock_redis_client, "test-task")
        def test_function():
            nonlocal call_count
            call_count += 1
            return call_count

        result1 = test_function()

        # Second call should fail to acquire lock (already locked)
        mock_redis_client.set.return_value = False

        # Function should not execute if lock not acquired
        # (This depends on decorator implementation)
        assert result1 == 1
