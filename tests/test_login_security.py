#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# US#21: Login Security Tests
#
"""
Unit tests for services/core-api/utils/login_security.py

Tests account lockout and failed login attempt tracking.
"""

from datetime import datetime, timedelta
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


class TestLoginSecurity:
    """Tests for login security utilities"""

    def test_record_failed_attempt(self):
        """Test recording a failed login attempt"""
        try:
            from utils.login_security import (
                clear_failed_attempts,
                is_account_locked,
                record_failed_attempt,
            )
        except ImportError:
            pytest.skip("login_security module not available")

        email = "test@example.com"

        # Clear any existing attempts

        clear_failed_attempts(email)

        # Record first failed attempt
        record_failed_attempt(email)

        # Account should not be locked after 1 attempt
        locked, _ = is_account_locked(email)
        assert locked is False

    def test_multiple_failed_attempts(self):
        """Test multiple failed attempts"""
        try:
            from utils.login_security import (
                clear_failed_attempts,
                is_account_locked,
                record_failed_attempt,
            )
        except ImportError:
            pytest.skip("login_security module not available")

        email = "test@example.com"
        clear_failed_attempts(email)

        # Record multiple failed attempts
        for _ in range(4):
            record_failed_attempt(email)

        # Should not be locked after 4 attempts
        locked, _ = is_account_locked(email)
        assert locked is False

        # 5th attempt should lock account
        record_failed_attempt(email)
        locked, _ = is_account_locked(email)
        assert locked is True

    def test_is_account_locked(self):
        """Test checking if account is locked"""
        try:
            from utils.login_security import (
                clear_failed_attempts,
                is_account_locked,
                record_failed_attempt,
            )
        except ImportError:
            pytest.skip("login_security module not available")

        email = "test@example.com"
        clear_failed_attempts(email)

        # Account should not be locked initially
        locked, _ = is_account_locked(email)
        assert locked is False

        # Lock account
        for _ in range(5):
            record_failed_attempt(email)

        locked, _ = is_account_locked(email)
        assert locked is True

    def test_clear_failed_attempts(self):
        """Test clearing failed attempts"""
        try:
            from utils.login_security import (
                clear_failed_attempts,
                is_account_locked,
                record_failed_attempt,
            )
        except ImportError:
            pytest.skip("login_security module not available")

        email = "test@example.com"
        clear_failed_attempts(email)

        # Record failed attempts
        for _ in range(5):
            record_failed_attempt(email)

        locked, _ = is_account_locked(email)
        assert locked is True

        # Clear attempts
        clear_failed_attempts(email)
        locked, _ = is_account_locked(email)
        assert locked is False

    def test_lockout_expires(self):
        """Test that lockout expires after duration"""
        try:
            from utils.login_security import (
                LOCKOUT_DURATION_MINUTES,
                _lockouts,
                clear_failed_attempts,
                is_account_locked,
                record_failed_attempt,
            )
        except ImportError:
            pytest.skip("login_security module not available")

        email = "test@example.com"
        clear_failed_attempts(email)

        # Lock account
        for _ in range(5):
            record_failed_attempt(email)

        locked, _ = is_account_locked(email)
        assert locked is True

        # Simulate time passing beyond lockout duration
        if email.lower() in _lockouts:
            # Set lockout time to past
            _lockouts[email.lower()] = datetime.utcnow() - timedelta(minutes=LOCKOUT_DURATION_MINUTES + 1)

        # Account should no longer be locked (expired)
        locked, _ = is_account_locked(email)
        assert locked is False

    def test_attempt_window_cleanup(self):
        """Test that old attempts are cleaned up"""
        try:
            from utils.login_security import (
                ATTEMPT_WINDOW_MINUTES,
                _failed_attempts,
                clear_failed_attempts,
                record_failed_attempt,
            )
        except ImportError:
            pytest.skip("login_security module not available")

        email = "test@example.com"
        clear_failed_attempts(email)

        # Record old attempt
        with patch("utils.login_security.datetime") as mock_datetime:
            old_time = datetime.utcnow() - timedelta(minutes=ATTEMPT_WINDOW_MINUTES + 10)
            mock_datetime.utcnow.return_value = old_time
            record_failed_attempt(email)

            # Record new attempt
            mock_datetime.utcnow.return_value = datetime.utcnow()
            record_failed_attempt(email)

            # Should only have 1 attempt (old one cleaned up)
            if email.lower() in _failed_attempts:
                assert len(_failed_attempts[email.lower()]) == 1

    def test_case_insensitive_email(self):
        """Test that email handling is case insensitive"""
        try:
            from utils.login_security import (
                clear_failed_attempts,
                is_account_locked,
                record_failed_attempt,
            )
        except ImportError:
            pytest.skip("login_security module not available")

        email1 = "Test@Example.com"
        email2 = "test@example.com"

        clear_failed_attempts(email1)
        clear_failed_attempts(email2)

        # Record attempts with different cases
        for _ in range(5):
            record_failed_attempt(email1)

        # Should be locked for both cases
        locked1, _ = is_account_locked(email1)
        locked2, _ = is_account_locked(email2)
        assert locked1 is True
        assert locked2 is True

    def test_get_failed_attempt_count(self):
        """Test getting failed attempt count"""
        try:
            from utils.login_security import (
                clear_failed_attempts,
                get_failed_attempt_count,
                record_failed_attempt,
            )
        except ImportError:
            pytest.skip("login_security module not available")

        email = "test@example.com"
        clear_failed_attempts(email)

        # Should start at 0
        assert get_failed_attempt_count(email) == 0

        # Record attempts
        for i in range(3):
            record_failed_attempt(email)
            assert get_failed_attempt_count(email) == i + 1
