#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Leader Election Tests
#
"""
Unit tests for server/billing/leader_election.py

Tests Redis-based leader election for Celery beat scheduler.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

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
        return mock_client
    except ImportError:
        pytest.skip("Redis not available")


@pytest.fixture
def mock_redis_unavailable():
    """Mock Redis as unavailable"""
    return None


class TestLeaderElection:
    """Tests for LeaderElection class"""

    def test_initialization(self, mock_redis_client):
        """Test leader election initialization"""
        from server.billing.leader_election import LeaderElection

        leader = LeaderElection(mock_redis_client, region="us-east-1")

        assert leader.redis is not None
        assert leader.region == "us-east-1"
        assert leader.leader_id is not None
        assert leader.is_leader is False

    def test_initialization_with_leader_id(self, mock_redis_client):
        """Test initialization with custom leader ID"""
        from server.billing.leader_election import LeaderElection

        custom_id = "custom-leader-123"
        leader = LeaderElection(mock_redis_client, region="us-east-1", leader_id=custom_id)

        assert leader.leader_id == custom_id

    def test_acquire_leadership_success(self, mock_redis_client):
        """Test successful leadership acquisition"""
        from server.billing.leader_election import LeaderElection

        mock_redis_client.set.return_value = True

        leader = LeaderElection(mock_redis_client, region="us-east-1")
        result = leader.acquire_leadership()

        assert result is True
        assert leader.is_leader is True
        assert leader.last_renewal is not None
        mock_redis_client.set.assert_called_once()

    def test_acquire_leadership_failure(self, mock_redis_client):
        """Test leadership acquisition failure"""
        from server.billing.leader_election import LeaderElection

        # Mock set to return False (someone else is leader)
        mock_redis_client.set.return_value = False
        mock_redis_client.get.return_value = b"other-leader-id"

        leader = LeaderElection(mock_redis_client, region="us-east-1", leader_id="my-leader-id")
        result = leader.acquire_leadership()

        assert result is False
        assert leader.is_leader is False

    def test_acquire_leadership_without_redis(self, mock_redis_unavailable):
        """Test leadership acquisition when Redis is unavailable"""
        from server.billing.leader_election import LeaderElection

        leader = LeaderElection(mock_redis_unavailable, region="us-east-1")
        result = leader.acquire_leadership()

        # Should assume leadership when Redis unavailable
        assert result is True

    def test_renew_leadership(self, mock_redis_client):
        """Test leadership renewal"""
        from server.billing.leader_election import LeaderElection

        leader = LeaderElection(mock_redis_client, region="us-east-1", leader_id="leader-123")
        leader.is_leader = True

        # Mock get to return our leader ID
        mock_redis_client.get.return_value = b"leader-123"
        mock_redis_client.set.return_value = True

        result = leader.renew_leadership()

        assert result is True
        mock_redis_client.set.assert_called()

    def test_release_leadership(self, mock_redis_client):
        """Test leadership release"""
        from server.billing.leader_election import LeaderElection

        leader = LeaderElection(mock_redis_client, region="us-east-1", leader_id="leader-123")
        leader.is_leader = True

        # Mock get to return our leader ID
        mock_redis_client.get.return_value = b"leader-123"

        leader.release_leadership()

        assert leader.is_leader is False
        mock_redis_client.delete.assert_called_once()

    def test_is_current_leader(self, mock_redis_client):
        """Test checking if current leader"""
        from server.billing.leader_election import LeaderElection

        leader = LeaderElection(mock_redis_client, region="us-east-1", leader_id="leader-123")

        # Mock get to return our leader ID
        mock_redis_client.get.return_value = b"leader-123"

        result = leader.is_current_leader()

        assert result is True
        mock_redis_client.get.assert_called_once()

    def test_is_current_leader_false(self, mock_redis_client):
        """Test checking when not current leader"""
        from server.billing.leader_election import LeaderElection

        leader = LeaderElection(mock_redis_client, region="us-east-1", leader_id="leader-123")

        # Mock get to return different leader ID
        mock_redis_client.get.return_value = b"other-leader-456"

        result = leader.is_current_leader()

        assert result is False

    def test_leader_key_format(self, mock_redis_client):
        """Test leader key format"""
        from server.billing.leader_election import LeaderElection

        leader = LeaderElection(mock_redis_client, region="us-east-1")

        assert leader.leader_key.startswith("billing:beat:leader")
        assert "us-east-1" in leader.leader_key
