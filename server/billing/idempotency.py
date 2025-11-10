#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Idempotency & Distributed Locking
# Developer D - January 2025
#
# BILL-013: Idempotency & Distributed Locking

"""
Idempotency and distributed locking for billing tasks.

Prevents duplicate task execution across regions using Redis locks.
Includes event hash verification for task idempotency.
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class DistributedLock:
    """
    Redis-based distributed lock for task idempotency.

    Uses SETNX with TTL to ensure only one instance executes a task.
    """

    LOCK_KEY_PREFIX = "billing:lock"
    DEFAULT_TTL = 300  # 5 minutes default TTL
    LOCK_RENEWAL_INTERVAL = 60  # Renew every 60 seconds

    def __init__(self, redis_client, lock_key: str, ttl: int = DEFAULT_TTL, lock_id: Optional[str] = None):
        """
        Initialize distributed lock.

        Args:
            redis_client: Redis client instance
            lock_key: Lock key (will be prefixed)
            ttl: Lock TTL in seconds
            lock_id: Unique lock ID (default: UUID)
        """
        self.redis = redis_client
        self.lock_key = f"{self.LOCK_KEY_PREFIX}:{lock_key}"
        self.ttl = ttl
        self.lock_id = lock_id or str(uuid4())
        self.acquired = False
        self.acquired_at = None
        self.last_renewal = None

    def acquire(self, timeout: int = 10) -> bool:
        """
        Acquire lock with timeout.

        Args:
            timeout: Maximum time to wait for lock (seconds)

        Returns:
            True if lock acquired, False otherwise
        """
        if not REDIS_AVAILABLE or not self.redis:
            logger.warning("Redis not available, assuming lock acquired")
            self.acquired = True
            self.acquired_at = datetime.now(timezone.utc)
            return True

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Try to acquire lock with SETNX
                acquired = self.redis.set(
                    self.lock_key, self.lock_id, nx=True, ex=self.ttl  # Only set if not exists  # Expire after TTL
                )

                if acquired:
                    self.acquired = True
                    self.acquired_at = datetime.now(timezone.utc)
                    self.last_renewal = self.acquired_at
                    logger.debug(f"Lock acquired: {self.lock_key}")
                    return True

                # Wait before retry
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error acquiring lock {self.lock_key}: {e}")
                # On error, assume lock acquired for resilience
                self.acquired = True
                self.acquired_at = datetime.now(timezone.utc)
                return True

        logger.warning(f"Failed to acquire lock {self.lock_key} within timeout")
        return False

    def renew(self) -> bool:
        """
        Renew lock TTL.

        Returns:
            True if lock renewed, False otherwise
        """
        if not REDIS_AVAILABLE or not self.redis:
            return True

        if not self.acquired:
            return False

        try:
            # Check if we still own the lock
            current_owner = self.redis.get(self.lock_key)
            if current_owner and current_owner.decode() == self.lock_id:
                # Renew TTL
                self.redis.expire(self.lock_key, self.ttl)
                self.last_renewal = datetime.now(timezone.utc)
                return True
            else:
                # Lost lock
                self.acquired = False
                logger.warning(f"Lock lost: {self.lock_key}")
                return False

        except Exception as e:
            logger.error(f"Error renewing lock {self.lock_key}: {e}")
            return False

    def release(self):
        """Release lock"""
        if not REDIS_AVAILABLE or not self.redis:
            return

        if not self.acquired:
            return

        try:
            # Only release if we own the lock
            current_owner = self.redis.get(self.lock_key)
            if current_owner and current_owner.decode() == self.lock_id:
                self.redis.delete(self.lock_key)
                logger.debug(f"Lock released: {self.lock_key}")
        except Exception as e:
            logger.error(f"Error releasing lock {self.lock_key}: {e}")
        finally:
            self.acquired = False

    def should_renew(self) -> bool:
        """
        Check if lock should be renewed.

        Returns:
            True if renewal is needed
        """
        if not self.acquired:
            return False

        if self.last_renewal is None:
            return True

        elapsed = (datetime.now(timezone.utc) - self.last_renewal).total_seconds()
        return elapsed >= self.LOCK_RENEWAL_INTERVAL

    def __enter__(self):
        """Context manager entry"""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()


def get_task_lock_key(task_name: str, task_args: tuple, region: str = "default") -> str:
    """
    Generate lock key for task.

    Args:
        task_name: Task name
        task_args: Task arguments
        region: Region identifier

    Returns:
        Lock key
    """
    import hashlib
    import json

    # Create hash of task name + args
    task_data = json.dumps({"task": task_name, "args": task_args}, sort_keys=True)
    task_hash = hashlib.sha256(task_data.encode()).hexdigest()[:16]

    return f"{task_name}:{task_hash}:{region}"


def with_idempotency_lock(redis_client, task_name: str, task_args: tuple, region: str = "default", ttl: int = 300):
    """
    Decorator for idempotent task execution.

    Args:
        redis_client: Redis client
        task_name: Task name
        task_args: Task arguments
        region: Region identifier
        ttl: Lock TTL

    Returns:
        Decorator function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            lock_key = get_task_lock_key(task_name, task_args, region)
            lock = DistributedLock(redis_client, lock_key, ttl=ttl)

            if not lock.acquire():
                logger.info(f"Task {task_name} already running, skipping")
                return {"status": "skipped", "reason": "already_running"}

            try:
                # Renew lock periodically if task runs long
                import threading

                renewal_thread = None

                def renew_lock_periodically():
                    while lock.acquired:
                        time.sleep(lock.LOCK_RENEWAL_INTERVAL)
                        if lock.should_renew():
                            lock.renew()

                renewal_thread = threading.Thread(target=renew_lock_periodically, daemon=True)
                renewal_thread.start()

                # Execute task
                result = func(*args, **kwargs)
                return result

            finally:
                lock.release()

        return wrapper

    return decorator


def compute_event_hash(event_data: Dict[str, Any]) -> str:
    """
    Compute SHA256 hash of event data for verification.

    Args:
        event_data: Event data dictionary

    Returns:
        SHA256 hash as hex string
    """
    # Sort keys for deterministic hashing
    sorted_data = json.dumps(event_data, sort_keys=True)
    return hashlib.sha256(sorted_data.encode()).hexdigest()


def verify_event_hash(event_data: Dict[str, Any], expected_hash: str) -> bool:
    """
    Verify event hash matches expected hash.

    Args:
        event_data: Event data dictionary
        expected_hash: Expected hash value

    Returns:
        True if hash matches, False otherwise
    """
    computed_hash = compute_event_hash(event_data)
    return computed_hash == expected_hash


def get_event_hash_key(event_hash: str, task_name: str, region: str = "default") -> str:
    """
    Generate Redis key for event hash tracking.

    Args:
        event_hash: Event hash
        task_name: Task name
        region: Region identifier

    Returns:
        Redis key for event hash
    """
    return f"billing:event_hash:{task_name}:{event_hash}:{region}"


def check_event_hash_processed(redis_client, event_hash: str, task_name: str, region: str = "default") -> bool:
    """
    Check if event hash has been processed.

    Args:
        redis_client: Redis client
        event_hash: Event hash
        task_name: Task name
        region: Region identifier

    Returns:
        True if event hash already processed, False otherwise
    """
    if not REDIS_AVAILABLE or not redis_client:
        return False

    try:
        key = get_event_hash_key(event_hash, task_name, region)
        exists = redis_client.exists(key)
        return bool(exists)
    except Exception as e:
        logger.error(f"Error checking event hash: {e}")
        return False


def mark_event_hash_processed(redis_client, event_hash: str, task_name: str, region: str = "default", ttl: int = 86400):
    """
    Mark event hash as processed.

    Args:
        redis_client: Redis client
        event_hash: Event hash
        task_name: Task name
        region: Region identifier
        ttl: TTL in seconds (default: 24 hours)
    """
    if not REDIS_AVAILABLE or not redis_client:
        return

    try:
        key = get_event_hash_key(event_hash, task_name, region)
        redis_client.set(key, "1", ex=ttl)
    except Exception as e:
        logger.error(f"Error marking event hash as processed: {e}")


def with_event_hash_verification(redis_client, task_name: str, event_data: Dict[str, Any], region: str = "default"):
    """
    Decorator for task execution with event hash verification.

    Verifies event hash and prevents duplicate processing of same event.

    Args:
        redis_client: Redis client
        task_name: Task name
        event_data: Event data dictionary
        region: Region identifier

    Returns:
        Decorator function
    """
    event_hash = compute_event_hash(event_data)

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Check if event hash already processed
            if check_event_hash_processed(redis_client, event_hash, task_name, region):
                logger.info(f"Event hash {event_hash[:16]}... already processed for task {task_name}, skipping")
                return {"status": "skipped", "reason": "event_hash_already_processed", "event_hash": event_hash}

            try:
                # Execute task
                result = func(*args, **kwargs)

                # Mark event hash as processed on success
                mark_event_hash_processed(redis_client, event_hash, task_name, region)

                return result
            except Exception as e:
                logger.error(f"Error executing task {task_name} with event hash {event_hash[:16]}...: {e}")
                raise

        return wrapper

    return decorator
