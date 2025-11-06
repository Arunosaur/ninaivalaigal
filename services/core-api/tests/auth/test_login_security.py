# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""Unit tests for login security utilities (account lockout and failed attempt tracking)."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from utils import login_security
from utils.login_security import (
    clear_failed_attempts,
    get_failed_attempt_count,
    is_account_locked,
    record_failed_attempt,
)


@pytest.fixture(autouse=True)
def clear_security_state():
    """Clear security state before each test to ensure isolation."""
    # Clear failed attempts and lockouts
    login_security._failed_attempts.clear()
    login_security._lockouts.clear()
    yield
    # Clean up after test
    login_security._failed_attempts.clear()
    login_security._lockouts.clear()


class TestFailedAttemptTracking:
    """Test failed login attempt tracking."""

    def test_record_failed_attempt(self):
        """Test recording a failed login attempt."""
        email = "test@example.com"
        record_failed_attempt(email)

        count = get_failed_attempt_count(email)
        assert count == 1

    def test_multiple_failed_attempts(self):
        """Test tracking multiple failed attempts."""
        email = "test@example.com"

        # Record multiple attempts
        for _ in range(3):
            record_failed_attempt(email)

        count = get_failed_attempt_count(email)
        assert count == 3

    def test_clear_failed_attempts(self):
        """Test clearing failed attempts."""
        email = "test@example.com"

        # Record some attempts
        record_failed_attempt(email)
        record_failed_attempt(email)

        assert get_failed_attempt_count(email) == 2

        # Clear attempts
        clear_failed_attempts(email)

        assert get_failed_attempt_count(email) == 0

    def test_get_failed_attempt_count_returns_zero_for_new_email(self):
        """Test that new emails start with zero failed attempts."""
        email = "newuser@example.com"
        count = get_failed_attempt_count(email)
        assert count == 0


class TestAccountLockout:
    """Test account lockout functionality."""

    def test_account_not_locked_initially(self):
        """Test that accounts are not locked initially."""
        email = "test@example.com"
        is_locked, lock_until = is_account_locked(email)

        assert is_locked is False
        assert lock_until is None

    def test_account_locks_after_max_attempts(self):
        """Test that account locks after maximum failed attempts."""
        email = "test@example.com"

        # Record maximum failed attempts (5)
        for _ in range(5):
            record_failed_attempt(email)

        # Check if account is locked
        is_locked, lock_until = is_account_locked(email)

        assert is_locked is True
        assert lock_until is not None
        assert isinstance(lock_until, str)  # ISO format string

    def test_account_unlocks_after_duration(self, monkeypatch):
        """Test that account unlocks after lockout duration expires."""
        email = "test@example.com"

        # Record maximum attempts to lock account
        for _ in range(5):
            record_failed_attempt(email)

        # Verify locked
        is_locked, _ = is_account_locked(email)
        assert is_locked is True

        # Manually expire the lockout by setting lock_until to past time
        email_lower = email.lower()
        if email_lower in login_security._lockouts:
            # Set lockout to past time
            past_time = datetime.utcnow() - timedelta(minutes=1)
            login_security._lockouts[email_lower] = past_time

        # Check again - should be unlocked now
        is_locked, lock_until = is_account_locked(email)
        assert is_locked is False
        assert lock_until is None

    def test_clear_failed_attempts_also_unlocks(self):
        """Test that clearing failed attempts also unlocks account."""
        email = "test@example.com"

        # Lock the account
        for _ in range(5):
            record_failed_attempt(email)

        assert is_account_locked(email)[0] is True

        # Clear attempts
        clear_failed_attempts(email)

        # Should be unlocked
        is_locked, lock_until = is_account_locked(email)
        assert is_locked is False
        assert lock_until is None

    def test_failed_attempts_are_email_case_insensitive(self):
        """Test that failed attempts are tracked case-insensitively."""
        email1 = "Test@Example.com"
        email2 = "test@example.com"

        record_failed_attempt(email1)
        record_failed_attempt(email2)

        # Should be 2 attempts for the same email
        count1 = get_failed_attempt_count(email1)
        count2 = get_failed_attempt_count(email2)

        assert count1 == 2
        assert count2 == 2
