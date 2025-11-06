# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""Unit tests for SPEC-114 compliant rate limiting."""

from __future__ import annotations

import time

import pytest

from utils.rate_limiting import AuthRateLimiter


@pytest.fixture
def rate_limiter():
    """Create a fresh rate limiter instance for each test."""
    return AuthRateLimiter()


class TestSPEC114RateLimiting:
    """Test SPEC-114 compliant rate limiting for authentication endpoints."""

    def test_login_rate_limit_5_per_15_minutes(self, rate_limiter):
        """Test login endpoint: 5 attempts per 15 minutes."""
        identifier = "test_user@example.com"

        # Should allow 5 attempts
        for i in range(5):
            is_allowed, error_msg, rate_info = rate_limiter.is_allowed(identifier, endpoint="login")
            assert is_allowed is True, f"Attempt {i+1} should be allowed"
            assert rate_info["remaining"] == 4 - i

        # 6th attempt should be blocked
        is_allowed, error_msg, rate_info = rate_limiter.is_allowed(identifier, endpoint="login")
        assert is_allowed is False
        assert "login attempts" in error_msg.lower()
        assert rate_info["remaining"] == 0
        assert rate_info["limit"] == 5

    def test_signup_rate_limit_3_per_10_minutes(self, rate_limiter):
        """Test signup endpoint: 3 attempts per 10 minutes."""
        identifier = "new_user@example.com"

        # Should allow 3 attempts
        for i in range(3):
            is_allowed, error_msg, rate_info = rate_limiter.is_allowed(identifier, endpoint="signup")
            assert is_allowed is True, f"Attempt {i+1} should be allowed"
            assert rate_info["limit"] == 3
            assert rate_info["remaining"] == 2 - i

        # 4th attempt should be blocked
        is_allowed, error_msg, rate_info = rate_limiter.is_allowed(identifier, endpoint="signup")
        assert is_allowed is False
        assert "signup attempts" in error_msg.lower()
        assert rate_info["remaining"] == 0
        assert rate_info["limit"] == 3

    def test_rate_limit_reset_after_window(self, rate_limiter, monkeypatch):
        """Test that rate limit resets after window expires."""
        identifier = "test@example.com"

        # Use up all attempts
        for _ in range(5):
            rate_limiter.is_allowed(identifier, endpoint="login")

        # Verify blocked
        is_allowed, _, _ = rate_limiter.is_allowed(identifier, endpoint="login")
        assert is_allowed is False

        # Simulate time passing (16 minutes)
        current_time = time.time()
        future_time = current_time + (16 * 60)  # 16 minutes

        # Mock time.time() to return future time
        original_time = time.time

        def mock_time():
            return future_time

        monkeypatch.setattr(time, "time", mock_time)

        # Should be allowed again (old attempts expired)
        is_allowed, _, rate_info = rate_limiter.is_allowed(identifier, endpoint="login")
        assert is_allowed is True
        assert rate_info["remaining"] == 4  # One attempt used

    def test_different_identifiers_have_separate_limits(self, rate_limiter):
        """Test that different identifiers have separate rate limits."""
        identifier1 = "user1@example.com"
        identifier2 = "user2@example.com"

        # Use all attempts for user1
        for _ in range(5):
            rate_limiter.is_allowed(identifier1, endpoint="login")

        # User1 should be blocked
        is_allowed1, _, _ = rate_limiter.is_allowed(identifier1, endpoint="login")
        assert is_allowed1 is False

        # User2 should still be allowed
        is_allowed2, _, rate_info2 = rate_limiter.is_allowed(identifier2, endpoint="login")
        assert is_allowed2 is True
        assert rate_info2["remaining"] == 4

    def test_rate_limit_info_contains_correct_headers(self, rate_limiter):
        """Test that rate limit info contains data for response headers."""
        identifier = "test@example.com"

        # Make one attempt
        is_allowed, _, rate_info = rate_limiter.is_allowed(identifier, endpoint="login")

        assert is_allowed is True
        assert "limit" in rate_info
        assert "remaining" in rate_info
        assert "reset_time" in rate_info
        assert "retry_after" in rate_info
        assert rate_info["limit"] == 5
        assert rate_info["remaining"] == 4
        assert rate_info["retry_after"] == 0

    def test_rate_limit_headers_when_exceeded(self, rate_limiter):
        """Test rate limit info when limit is exceeded."""
        identifier = "test@example.com"

        # Use all attempts
        for _ in range(5):
            rate_limiter.is_allowed(identifier, endpoint="login")

        # Get rate info for blocked request
        is_allowed, error_msg, rate_info = rate_limiter.is_allowed(identifier, endpoint="login")

        assert is_allowed is False
        assert rate_info["remaining"] == 0
        assert rate_info["retry_after"] > 0  # Should have retry time
        assert rate_info["reset_time"] > time.time()  # Future reset time
