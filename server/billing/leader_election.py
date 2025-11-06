#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Leader Election for Beat Scheduler
# Developer D - January 2025
#
# BILL-012: Multi-Region Leader Election

"""
Redis-based leader election for Celery beat scheduler.

Ensures only one beat scheduler runs globally across regions.
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class LeaderElection:
    """
    Redis-based leader election for distributed beat scheduler.

    Uses SETNX with TTL to ensure only one leader is active.
    """

    LEADER_KEY_PREFIX = "billing:beat:leader"
    LEADER_TTL = 60  # 60 seconds TTL
    RENEWAL_INTERVAL = 30  # Renew every 30 seconds

    def __init__(self, redis_client, region: str = "default", leader_id: Optional[str] = None):
        """
        Initialize leader election.

        Args:
            redis_client: Redis client instance
            region: Region identifier
            leader_id: Unique leader ID (default: hostname + process ID)
        """
        self.redis = redis_client
        self.region = region

        if leader_id is None:
            import os
            import socket

            hostname = socket.gethostname()
            pid = os.getpid()
            self.leader_id = f"{hostname}:{pid}:{region}"
        else:
            self.leader_id = leader_id

        self.leader_key = f"{self.LEADER_KEY_PREFIX}:{region}"
        self.is_leader = False
        self.last_renewal = None

    def acquire_leadership(self) -> bool:
        """
        Attempt to acquire leadership.

        Returns:
            True if leadership acquired, False otherwise
        """
        if not REDIS_AVAILABLE or not self.redis:
            logger.warning("Redis not available, assuming leadership")
            return True

        try:
            # Try to acquire lock with SETNX
            acquired = self.redis.set(
                self.leader_key,
                self.leader_id,
                nx=True,  # Only set if not exists
                ex=self.LEADER_TTL,  # Expire after TTL
            )

            if acquired:
                self.is_leader = True
                self.last_renewal = datetime.now(timezone.utc)
                logger.info(f"Leadership acquired: {self.leader_id}")
                return True
            else:
                # Check if we're still the leader
                current_leader = self.redis.get(self.leader_key)
                if current_leader and current_leader.decode() == self.leader_id:
                    self.is_leader = True
                    self.last_renewal = datetime.now(timezone.utc)
                    return True
                else:
                    self.is_leader = False
                    return False

        except Exception as e:
            logger.error(f"Error acquiring leadership: {e}")
            # On error, assume leadership for resilience
            self.is_leader = True
            return True

    def renew_leadership(self) -> bool:
        """
        Renew leadership if we're the current leader.

        Returns:
            True if leadership renewed, False otherwise
        """
        if not REDIS_AVAILABLE or not self.redis:
            return True

        if not self.is_leader:
            return False

        try:
            # Check if we're still the leader
            current_leader = self.redis.get(self.leader_key)
            if current_leader and current_leader.decode() == self.leader_id:
                # Renew TTL
                self.redis.expire(self.leader_key, self.LEADER_TTL)
                self.last_renewal = datetime.now(timezone.utc)
                return True
            else:
                # Lost leadership
                self.is_leader = False
                logger.warning(f"Leadership lost: {self.leader_id}")
                return False

        except Exception as e:
            logger.error(f"Error renewing leadership: {e}")
            return False

    def release_leadership(self):
        """Release leadership"""
        if not REDIS_AVAILABLE or not self.redis:
            return

        try:
            current_leader = self.redis.get(self.leader_key)
            if current_leader and current_leader.decode() == self.leader_id:
                self.redis.delete(self.leader_key)
                logger.info(f"Leadership released: {self.leader_id}")
        except Exception as e:
            logger.error(f"Error releasing leadership: {e}")
        finally:
            self.is_leader = False

    def should_renew(self) -> bool:
        """
        Check if leadership should be renewed.

        Returns:
            True if renewal is needed
        """
        if not self.is_leader:
            return False

        if self.last_renewal is None:
            return True

        elapsed = (datetime.now(timezone.utc) - self.last_renewal).total_seconds()
        return elapsed >= self.RENEWAL_INTERVAL

    def get_current_leader(self) -> Optional[str]:
        """
        Get current leader ID.

        Returns:
            Leader ID or None
        """
        if not REDIS_AVAILABLE or not self.redis:
            return self.leader_id

        try:
            leader = self.redis.get(self.leader_key)
            if leader:
                return leader.decode()
            return None
        except Exception as e:
            logger.error(f"Error getting current leader: {e}")
            return None

    def is_current_leader(self) -> bool:
        """
        Check if we are the current leader.

        Returns:
            True if we are the leader
        """
        if not self.is_leader:
            return False

        current_leader = self.get_current_leader()
        return current_leader == self.leader_id


class LeaderElectionBeatScheduler:
    """
    Celery beat scheduler with leader election.

    Only runs scheduled tasks if this instance is the leader.
    """

    def __init__(self, leader_election: LeaderElection):
        """
        Initialize scheduler with leader election.

        Args:
            leader_election: LeaderElection instance
        """
        self.leader_election = leader_election
        self.scheduler = None

    def setup_scheduler(self, celery_app):
        """Setup Celery beat scheduler"""
        from celery.beat import PersistentScheduler

        # Get beat schedule from celery app
        beat_schedule = celery_app.conf.beat_schedule

        # Create persistent scheduler
        self.scheduler = PersistentScheduler(
            app=celery_app, schedule_filename="celerybeat-schedule", schedule=beat_schedule
        )

        # Try to acquire leadership
        if self.leader_election.acquire_leadership():
            logger.info("Beat scheduler started as leader")
        else:
            logger.info("Beat scheduler started as standby (waiting for leadership)")

    def tick(self, celery_app):
        """
        Tick the scheduler (called periodically).

        Only executes tasks if we're the leader.
        """
        # Renew leadership
        if self.leader_election.should_renew():
            if not self.leader_election.renew_leadership():
                # Lost leadership, try to acquire
                self.leader_election.acquire_leadership()

        # Only run tasks if we're the leader
        if self.leader_election.is_current_leader():
            if self.scheduler:
                return self.scheduler.tick()
        else:
            # Not leader, sleep and wait
            time.sleep(1)
            return None

    def close(self):
        """Close scheduler and release leadership"""
        if self.scheduler:
            self.scheduler.close()
        self.leader_election.release_leadership()
