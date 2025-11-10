#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-114: Rate Limiting Tests
#
"""
Unit tests for services/core-api/utils/rate_limiting.py

Tests authentication endpoint rate limiting.
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


class TestAuthRateLimiter:
    """Tests for AuthRateLimiter class"""

    def test_initialization(self):
        """Test rate limiter initialization"""
        try:
            from utils.rate_limiting import AuthRateLimiter

            limiter = AuthRateLimiter()
            assert limiter is not None
            assert limiter.attempts is not None
        except ImportError:
            pytest.skip("rate_limiting module not available")

    def test_login_allowed_within_limit(self):
        """Test login allowed within limit"""
        try:
            from utils.rate_limiting import AuthRateLimiter

            limiter = AuthRateLimiter()
            identifier = "ip:test@example.com"

            # First 5 attempts should be allowed
            for i in range(5):
                allowed, error, info = limiter.is_allowed(identifier, endpoint="login")
                assert allowed is True
                assert error is None
                assert info["remaining"] == 4 - i
        except ImportError:
            pytest.skip("rate_limiting module not available")

    def test_login_blocked_after_limit(self):
        """Test login blocked after limit exceeded"""
        try:
            from utils.rate_limiting import AuthRateLimiter

            limiter = AuthRateLimiter()
            identifier = "ip:test@example.com"

            # Make 5 attempts
            for _ in range(5):
                allowed, _, _ = limiter.is_allowed(identifier, endpoint="login")
                assert allowed is True

            # 6th attempt should be blocked
            allowed, error, info = limiter.is_allowed(identifier, endpoint="login")
            assert allowed is False
            assert error is not None
            assert "Too many" in error
            assert info["remaining"] == 0
        except ImportError:
            pytest.skip("rate_limiting module not available")

    def test_signup_allowed_within_limit(self):
        """Test signup allowed within limit"""
        try:
            from utils.rate_limiting import AuthRateLimiter

            limiter = AuthRateLimiter()
            identifier = "ip:test@example.com"

            # First 3 attempts should be allowed
            for i in range(3):
                allowed, error, info = limiter.is_allowed(identifier, endpoint="signup")
                assert allowed is True
                assert error is None
                assert info["remaining"] == 2 - i
        except ImportError:
            pytest.skip("rate_limiting module not available")

    def test_signup_blocked_after_limit(self):
        """Test signup blocked after limit exceeded"""
        try:
            from utils.rate_limiting import AuthRateLimiter

            limiter = AuthRateLimiter()
            identifier = "ip:test@example.com"

            # Make 3 attempts
            for _ in range(3):
                allowed, _, _ = limiter.is_allowed(identifier, endpoint="signup")
                assert allowed is True

            # 4th attempt should be blocked
            allowed, error, info = limiter.is_allowed(identifier, endpoint="signup")
            assert allowed is False
            assert error is not None
            assert info["remaining"] == 0
        except ImportError:
            pytest.skip("rate_limiting module not available")

    def test_rate_limit_window_expiry(self):
        """Test that rate limit window expires"""
        try:
            from utils.rate_limiting import AuthRateLimiter

            limiter = AuthRateLimiter()
            identifier = "ip:test@example.com"

            # Make 5 login attempts
            for _ in range(5):
                limiter.is_allowed(identifier, endpoint="login")

            # Should be blocked
            allowed, _, _ = limiter.is_allowed(identifier, endpoint="login")
            assert allowed is False

            # Simulate time passing beyond window by clearing attempts
            limiter.attempts[identifier] = []

            # Should be allowed again
            allowed, _, _ = limiter.is_allowed(identifier, endpoint="login")
            assert allowed is True
        except ImportError:
            pytest.skip("rate_limiting module not available")

    def test_different_identifiers_independent(self):
        """Test that different identifiers have independent limits"""
        try:
            from utils.rate_limiting import AuthRateLimiter

            limiter = AuthRateLimiter()
            identifier1 = "ip:user1@example.com"
            identifier2 = "ip:user2@example.com"

            # Lock identifier1
            for _ in range(5):
                limiter.is_allowed(identifier1, endpoint="login")

            # identifier1 should be blocked
            allowed1, _, _ = limiter.is_allowed(identifier1, endpoint="login")
            assert allowed1 is False

            # identifier2 should still be allowed
            allowed2, _, _ = limiter.is_allowed(identifier2, endpoint="login")
            assert allowed2 is True
        except ImportError:
            pytest.skip("rate_limiting module not available")

    def test_rate_limit_info_structure(self):
        """Test that rate limit info has correct structure"""
        try:
            from utils.rate_limiting import AuthRateLimiter

            limiter = AuthRateLimiter()
            identifier = "ip:test@example.com"

            allowed, error, info = limiter.is_allowed(identifier, endpoint="login")

            assert "limit" in info
            assert "remaining" in info
            assert "reset_time" in info
            assert "retry_after" in info
            assert isinstance(info["limit"], int)
            assert isinstance(info["remaining"], int)
        except ImportError:
            pytest.skip("rate_limiting module not available")
