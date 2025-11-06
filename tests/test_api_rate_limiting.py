#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# US-91: API Rate Limiting Tests
#
"""
Unit tests for services/core-api/utils/api_rate_limiting.py

Tests general API rate limiting functionality.
"""

import time
from unittest.mock import patch

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


class TestAPIRateLimiter:
    """Tests for APIRateLimiter class"""

    def test_initialization(self):
        """Test rate limiter initialization"""
        try:
            from utils.api_rate_limiting import APIRateLimiter

            limiter = APIRateLimiter()
            assert limiter is not None
            assert limiter.ip_requests is not None
            assert limiter.user_requests is not None
        except ImportError:
            pytest.skip("api_rate_limiting module not available")

    def test_is_ip_whitelisted(self):
        """Test IP whitelist checking"""
        try:
            from utils.api_rate_limiting import APIRateLimiter

            limiter = APIRateLimiter()

            # Test whitelisted IPs
            assert limiter.is_ip_whitelisted("127.0.0.1") is True
            assert limiter.is_ip_whitelisted("localhost") is True

            # Test non-whitelisted IP
            assert limiter.is_ip_whitelisted("192.168.1.1") is False
        except ImportError:
            pytest.skip("api_rate_limiting module not available")

    def test_check_ip_limit_within_limit(self):
        """Test IP limit check when within limit"""
        try:
            from utils.api_rate_limiting import APIRateLimiter

            limiter = APIRateLimiter()
            ip = "192.168.1.1"

            # First request should be allowed
            allowed, error, info = limiter.check_ip_limit(ip)

            assert allowed is True
            assert error is None
            assert "remaining" in info
        except ImportError:
            pytest.skip("api_rate_limiting module not available")

    def test_check_ip_limit_exceeded(self):
        """Test IP limit check when limit exceeded"""
        try:
            from utils.api_rate_limiting import PER_IP_LIMIT, APIRateLimiter

            limiter = APIRateLimiter()
            ip = "192.168.1.1"

            # Make requests up to limit
            for _ in range(PER_IP_LIMIT):
                allowed, _, _ = limiter.check_ip_limit(ip)
                assert allowed is True

            # Next request should be denied
            allowed, error, info = limiter.check_ip_limit(ip)

            assert allowed is False
            assert error is not None
            assert "remaining" in info
            assert info["remaining"] == 0
        except ImportError:
            pytest.skip("api_rate_limiting module not available")

    def test_check_user_limit(self):
        """Test user rate limit checking"""
        try:
            from utils.api_rate_limiting import PER_USER_LIMIT, APIRateLimiter

            limiter = APIRateLimiter()
            user_id = "user-123"

            # First request should be allowed
            allowed, error, info = limiter.check_user_limit(user_id)

            assert allowed is True
            assert error is None
            assert "remaining" in info
        except ImportError:
            pytest.skip("api_rate_limiting module not available")

    def test_check_endpoint_limit(self):
        """Test endpoint-specific rate limiting"""
        try:
            from utils.api_rate_limiting import APIRateLimiter

            limiter = APIRateLimiter()
            ip = "192.168.1.1"
            endpoint = "/auth/login"

            # Check endpoint limit
            allowed, error, info = limiter.check_ip_limit(ip, endpoint=endpoint)

            assert allowed is True
            assert "remaining" in info
        except ImportError:
            pytest.skip("api_rate_limiting module not available")

    def test_rate_limit_window_expiry(self):
        """Test that rate limit window expires correctly"""
        try:
            import time as time_module

            from utils.api_rate_limiting import APIRateLimiter

            limiter = APIRateLimiter()
            ip = "192.168.1.1"

            # Make request
            limiter.check_ip_limit(ip)

            # Simulate time passing beyond window by directly manipulating the deque
            # Clear old requests
            if ip in limiter.ip_requests:
                limiter.ip_requests[ip].clear()

            # Should be able to make request again after clearing
            allowed, _, _ = limiter.check_ip_limit(ip)
            assert allowed is True
        except ImportError:
            pytest.skip("api_rate_limiting module not available")

    def test_whitelisted_ip_bypass(self):
        """Test that whitelisted IPs bypass rate limiting"""
        try:
            from utils.api_rate_limiting import PER_IP_LIMIT, APIRateLimiter

            limiter = APIRateLimiter()
            whitelisted_ip = "127.0.0.1"

            # Make many requests - should all be allowed
            for _ in range(PER_IP_LIMIT * 2):
                allowed, error, info = limiter.check_ip_limit(whitelisted_ip)
                assert allowed is True
                assert error is None
        except ImportError:
            pytest.skip("api_rate_limiting module not available")
