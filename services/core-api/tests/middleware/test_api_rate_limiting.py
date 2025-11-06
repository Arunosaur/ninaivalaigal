# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""Unit tests for API rate limiting - US-91"""

from __future__ import annotations

import time

import pytest

from utils.api_rate_limiting import PER_IP_LIMIT, PER_USER_LIMIT, APIRateLimiter


@pytest.fixture
def rate_limiter():
    """Create a fresh rate limiter instance for each test"""
    return APIRateLimiter()


class TestIPRateLimiting:
    """Test IP-based rate limiting"""

    def test_ip_within_limit(self, rate_limiter):
        """Test that requests within limit are allowed"""
        ip = "192.168.1.1"

        for i in range(PER_IP_LIMIT):
            is_allowed, error_msg, rate_info = rate_limiter.check_ip_limit(ip)
            assert is_allowed is True
            assert error_msg is None
            assert rate_info["remaining"] == PER_IP_LIMIT - i - 1

    def test_ip_exceeds_limit(self, rate_limiter):
        """Test that requests exceeding limit are blocked"""
        ip = "192.168.1.2"

        # Make requests up to limit
        for _ in range(PER_IP_LIMIT):
            is_allowed, _, _ = rate_limiter.check_ip_limit(ip)
            assert is_allowed is True

        # Next request should be blocked
        is_allowed, error_msg, rate_info = rate_limiter.check_ip_limit(ip)
        assert is_allowed is False
        assert error_msg is not None
        assert "Rate limit exceeded" in error_msg
        assert rate_info["remaining"] == 0
        assert rate_info["retry_after"] > 0

    def test_ip_limit_resets_after_window(self, rate_limiter, monkeypatch):
        """Test that IP limit resets after time window"""
        ip = "192.168.1.3"

        # Make requests up to limit
        for _ in range(PER_IP_LIMIT):
            rate_limiter.check_ip_limit(ip)

        # Simulate time passing (beyond window)
        now = time.time()
        monkeypatch.setattr(time, "time", lambda: now + 61)  # 61 seconds later

        # Should be allowed again
        is_allowed, _, rate_info = rate_limiter.check_ip_limit(ip)
        assert is_allowed is True
        assert rate_info["remaining"] == PER_IP_LIMIT - 1

    def test_whitelisted_ip(self, rate_limiter):
        """Test that whitelisted IPs bypass rate limiting"""
        ip = "127.0.0.1"  # Localhost is whitelisted

        # Make many requests
        for _ in range(1000):
            is_allowed, error_msg, rate_info = rate_limiter.check_ip_limit(ip)
            assert is_allowed is True
            assert error_msg is None
            assert rate_info.get("whitelisted") is True


class TestUserRateLimiting:
    """Test user-based rate limiting"""

    def test_user_within_limit(self, rate_limiter):
        """Test that requests within limit are allowed"""
        user_id = "test-user-123"

        for i in range(min(100, PER_USER_LIMIT)):  # Test up to 100
            is_allowed, error_msg, rate_info = rate_limiter.check_user_limit(user_id)
            assert is_allowed is True
            assert error_msg is None
            assert rate_info["remaining"] == PER_USER_LIMIT - i - 1

    def test_user_exceeds_limit(self, rate_limiter):
        """Test that requests exceeding limit are blocked"""
        user_id = "test-user-456"

        # Make requests up to limit (simulate by directly manipulating)
        # For testing, we'll make many requests
        for _ in range(PER_USER_LIMIT):
            rate_limiter.check_user_limit(user_id)

        # Next request should be blocked
        is_allowed, error_msg, rate_info = rate_limiter.check_user_limit(user_id)
        assert is_allowed is False
        assert error_msg is not None
        assert "Rate limit exceeded" in error_msg
        assert rate_info["remaining"] == 0


class TestEndpointSpecificLimits:
    """Test endpoint-specific rate limiting"""

    def test_endpoint_limit_applied(self, rate_limiter):
        """Test that endpoint-specific limits override global limits"""
        ip = "192.168.1.10"
        endpoint = "/api/search"  # Has limit of 50 per minute

        # Make requests up to endpoint limit
        for i in range(50):
            is_allowed, _, rate_info = rate_limiter.check_ip_limit(ip, endpoint=endpoint)
            assert is_allowed is True
            assert rate_info["scope"] == "endpoint"
            assert rate_info["limit"] == 50

        # Next request should be blocked
        is_allowed, error_msg, rate_info = rate_limiter.check_ip_limit(ip, endpoint=endpoint)
        assert is_allowed is False
        assert "Rate limit exceeded" in error_msg
        assert rate_info["scope"] == "endpoint"


class TestRateLimitInfo:
    """Test rate limit information retrieval"""

    def test_get_rate_limit_info(self, rate_limiter):
        """Test getting rate limit info without consuming request"""
        ip = "192.168.1.20"
        user_id = "test-user-789"

        # Make some requests
        rate_limiter.check_ip_limit(ip)
        rate_limiter.check_user_limit(user_id)

        # Get info
        info = rate_limiter.get_rate_limit_info(ip=ip, user_id=user_id)

        assert "ip" in info
        assert "user" in info
        assert info["ip"]["used"] == 1
        assert info["user"]["used"] == 1


class TestAdminFunctions:
    """Test admin functions for rate limit management"""

    def test_reset_ip_limit(self, rate_limiter):
        """Test resetting IP rate limit"""
        ip = "192.168.1.30"

        # Make requests
        for _ in range(10):
            rate_limiter.check_ip_limit(ip)

        # Reset
        success = rate_limiter.reset_ip_limit(ip)
        assert success is True

        # Should be reset
        info = rate_limiter.get_rate_limit_info(ip=ip)
        assert info["ip"]["used"] == 0

    def test_reset_user_limit(self, rate_limiter):
        """Test resetting user rate limit"""
        user_id = "test-user-reset"
        ip = "192.168.1.100"  # Need IP for get_rate_limit_info

        # Make requests
        for _ in range(10):
            rate_limiter.check_user_limit(user_id)

        # Reset
        success = rate_limiter.reset_user_limit(user_id)
        assert success is True

        # Should be reset
        info = rate_limiter.get_rate_limit_info(ip=ip, user_id=user_id)
        assert info["user"]["used"] == 0
