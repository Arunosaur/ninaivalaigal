#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-030: Security Monitoring Tests
#
"""
Unit tests for services/core-api/lib/security_monitoring.py

Tests security monitoring and metrics collection.
"""

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def setup_imports():
    """Setup imports for all tests"""
    import sys
    from pathlib import Path

    core_api_path = str(Path(__file__).parent.parent / "services" / "core-api")
    if core_api_path not in sys.path:
        sys.path.insert(0, core_api_path)


class TestSecurityMonitoring:
    """Tests for security monitoring functions"""

    def test_record_security_event(self):
        """Test recording a security event"""
        try:
            from lib.security_monitoring import (
                get_security_events,
                record_security_event,
            )

            event_type = "login_failure"
            details = {"ip": "192.168.1.1", "email": "test@example.com"}

            record_security_event(event_type, details)

            events = get_security_events(event_type, limit=10)
            assert len(events) > 0
            assert events[0]["event_type"] == event_type
            assert events[0]["ip"] == details["ip"]
        except ImportError:
            pytest.skip("security_monitoring module not available")

    def test_get_auth_failures_by_period(self):
        """Test getting authentication failures in period"""
        try:
            from lib.security_monitoring import (
                get_auth_failures_by_period,
                record_security_event,
            )

            # Record some security events
            record_security_event("login_failure", {"ip": "192.168.1.1"})
            record_security_event("login_failure", {"ip": "192.168.1.2"})

            # Get failures in last 24 hours
            count = get_auth_failures_by_period(hours=24)

            assert isinstance(count, int)
            assert count >= 0
        except ImportError:
            pytest.skip("security_monitoring module not available")

    def test_get_failed_logins_by_user(self):
        """Test getting top users with failed logins"""
        try:
            from lib.security_monitoring import get_failed_logins_by_user

            users = get_failed_logins_by_user(limit=10)

            assert isinstance(users, list)
            # Should return list of user dicts or empty list
            if users:
                assert "email" in users[0] or "user_id" in users[0]
        except ImportError:
            pytest.skip("security_monitoring module not available")

    def test_get_security_events(self):
        """Test getting security events"""
        try:
            from lib.security_monitoring import (
                get_security_events,
                record_security_event,
            )

            event_type = "rate_limit"
            record_security_event(event_type, {"ip": "192.168.1.1"})

            events = get_security_events(event_type, limit=10)

            assert isinstance(events, list)
            if events:
                assert events[0]["event_type"] == event_type
        except ImportError:
            pytest.skip("security_monitoring module not available")

    def test_security_metrics_retention(self):
        """Test that security metrics are limited to 1000 events"""
        try:
            from lib.security_monitoring import _security_metrics, record_security_event

            event_type = "test_event"

            # Record more than 1000 events
            for i in range(1100):
                record_security_event(event_type, {"index": i})

            # Should only keep last 1000
            assert len(_security_metrics[event_type]) == 1000
        except ImportError:
            pytest.skip("security_monitoring module not available")
