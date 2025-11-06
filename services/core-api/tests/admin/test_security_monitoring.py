# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""Unit tests for security monitoring module."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from lib.security_monitoring import (
    calculate_auth_success_rate,
    calculate_security_health_score,
    get_account_lockouts,
    get_auth_failures_by_period,
    get_failed_logins_by_user,
    get_security_metrics,
    record_security_event,
)


@pytest.fixture(autouse=True)
def clear_security_data(monkeypatch):
    """Clear security data before each test."""
    # Clear security metrics
    from lib import security_monitoring

    security_monitoring._security_metrics.clear()

    # Clear failed attempts and lockouts
    try:
        from utils import login_security

        login_security._failed_attempts.clear()
        login_security._lockouts.clear()
    except ImportError:
        pass

    yield

    # Cleanup after test
    security_monitoring._security_metrics.clear()


class TestSecurityEventRecording:
    """Test security event recording."""

    def test_record_security_event(self):
        """Test recording a security event."""
        record_security_event("login_failure", {"email": "test@example.com", "ip": "192.168.1.1"})

        from lib import security_monitoring

        events = security_monitoring._security_metrics["login_failure"]
        assert len(events) == 1
        assert events[0]["email"] == "test@example.com"
        assert events[0]["ip"] == "192.168.1.1"

    def test_security_events_limited_to_1000(self):
        """Test that security events are limited to 1000 per type."""
        from lib import security_monitoring

        # Record 1001 events
        for i in range(1001):
            record_security_event("test_event", {"index": i})

        events = security_monitoring._security_metrics["test_event"]
        assert len(events) == 1000  # Should be capped at 1000
        assert events[0]["index"] == 1  # First event should be removed


class TestAuthFailureTracking:
    """Test authentication failure tracking."""

    def test_get_auth_failures_by_period(self, monkeypatch):
        """Test getting auth failures for a time period."""
        # Mock failed attempts
        try:
            from utils import login_security

            now = datetime.utcnow()
            login_security._failed_attempts["test@example.com"] = [
                now - timedelta(hours=1),  # Within 24h
                now - timedelta(hours=2),  # Within 24h
                now - timedelta(hours=25),  # Outside 24h
            ]

            failures_24h = get_auth_failures_by_period(24)
            assert failures_24h == 2  # Only 2 failures within 24h
        except ImportError:
            pytest.skip("login_security module not available")

    def test_get_failed_logins_by_user(self, monkeypatch):
        """Test getting top users with failed logins."""
        try:
            from utils import login_security

            now = datetime.utcnow()

            # Set up test data
            login_security._failed_attempts["user1@example.com"] = [
                now - timedelta(days=1),
                now - timedelta(days=2),
                now - timedelta(days=3),
            ]
            login_security._failed_attempts["user2@example.com"] = [
                now - timedelta(days=1),
            ]

            top_users = get_failed_logins_by_user(limit=10)

            assert len(top_users) >= 1
            # user1 should have more failures
            if len(top_users) > 0:
                assert top_users[0]["failure_count"] >= 1
        except ImportError:
            pytest.skip("login_security module not available")


class TestSecurityMetrics:
    """Test security metrics calculation."""

    def test_get_account_lockouts(self, monkeypatch):
        """Test getting count of locked accounts."""
        try:
            from utils import login_security

            now = datetime.utcnow()

            # Set up locked accounts
            login_security._lockouts["user1@example.com"] = now + timedelta(minutes=10)  # Still locked
            login_security._lockouts["user2@example.com"] = now - timedelta(minutes=1)  # Expired

            locked_count = get_account_lockouts()
            assert locked_count == 1  # Only one still locked
        except ImportError:
            pytest.skip("login_security module not available")

    def test_calculate_auth_success_rate(self):
        """Test calculating authentication success rate."""
        rate = calculate_auth_success_rate(24)

        # Should return a float between 0 and 100
        assert isinstance(rate, float)
        assert 0 <= rate <= 100

    def test_calculate_security_health_score(self):
        """Test calculating security health score."""
        score = calculate_security_health_score()

        # Should return a float between 0 and 100
        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_get_security_metrics(self):
        """Test getting comprehensive security metrics."""
        metrics = get_security_metrics()

        # Verify all required fields are present
        assert "auth_failures_24h" in metrics
        assert "auth_failures_7d" in metrics
        assert "auth_failures_30d" in metrics
        assert "failed_logins_by_user" in metrics
        assert "failed_logins_by_ip" in metrics
        assert "suspicious_ips" in metrics
        assert "active_security_incidents" in metrics
        assert "auth_success_rate" in metrics
        assert "security_health_score" in metrics
        assert "timestamp" in metrics

        # Verify types
        assert isinstance(metrics["auth_failures_24h"], int)
        assert isinstance(metrics["auth_success_rate"], float)
        assert isinstance(metrics["security_health_score"], float)
        assert isinstance(metrics["failed_logins_by_user"], list)
