# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Login Security Utilities
Implements account lockout and failed login attempt tracking for US#21
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Final

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# Configuration constants
MAX_FAILED_ATTEMPTS: Final[int] = 5
LOCKOUT_DURATION_MINUTES: Final[int] = 15
ATTEMPT_WINDOW_MINUTES: Final[int] = 30  # Track attempts within this window

# In-memory storage for failed attempts
# TODO: Migrate to Redis for production/distributed systems
_failed_attempts: dict[str, list[datetime]] = {}
_lockouts: dict[str, datetime] = {}


def record_failed_attempt(email: str, ip_address: str = None, user_agent: str = None, db_session=None) -> None:
    """
    Record a failed login attempt for the given email.

    Args:
        email: User email address
        ip_address: IP address of the request (optional)
        user_agent: User agent string (optional)
        db_session: Database session for persistent logging (optional)
    """
    now = datetime.utcnow()
    email_lower = email.lower()

    # Clean old attempts outside the window
    window_start = now - timedelta(minutes=ATTEMPT_WINDOW_MINUTES)
    if email_lower in _failed_attempts:
        _failed_attempts[email_lower] = [attempt for attempt in _failed_attempts[email_lower] if attempt > window_start]
    else:
        _failed_attempts[email_lower] = []

    # Add new failed attempt
    _failed_attempts[email_lower].append(now)

    failed_count = len(_failed_attempts[email_lower])
    logger.warning(f"Failed login attempt recorded for {email_lower} (count: {failed_count}/{MAX_FAILED_ATTEMPTS})")

    # Record security event to persistent storage
    try:
        from lib.security_monitoring import record_security_event

        record_security_event(
            event_type="login_failure",
            details={
                "email": email_lower,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "failed_count": failed_count,
                "max_attempts": MAX_FAILED_ATTEMPTS,
                "reason": "Invalid credentials",
            },
            db_session=db_session,
            severity="warning",
        )
    except Exception as e:
        logger.warning(f"Failed to record security event: {e}")

    # Check if we should lock the account
    if failed_count >= MAX_FAILED_ATTEMPTS:
        lock_until = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        _lockouts[email_lower] = lock_until
        logger.error(
            f"Account locked due to excessive failed login attempts: {email_lower} "
            f"(failed_count: {failed_count}, locked_until: {lock_until.isoformat()})"
        )

        # Record account lockout event
        try:
            from lib.security_monitoring import record_security_event

            record_security_event(
                event_type="account_locked",
                details={
                    "email": email_lower,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "failed_count": failed_count,
                    "lock_duration_minutes": LOCKOUT_DURATION_MINUTES,
                    "lock_until": lock_until.isoformat(),
                    "reason": "Excessive failed login attempts",
                },
                db_session=db_session,
                severity="critical",
            )
        except Exception as e:
            logger.warning(f"Failed to record lockout event: {e}")


def clear_failed_attempts(email: str) -> None:
    """
    Clear failed login attempts for the given email (on successful login).

    Args:
        email: User email address
    """
    email_lower = email.lower()
    if email_lower in _failed_attempts:
        del _failed_attempts[email_lower]
    if email_lower in _lockouts:
        del _lockouts[email_lower]
    logger.info(f"Cleared failed login attempts for {email_lower}")


def is_account_locked(email: str) -> tuple[bool, str | None]:
    """
    Check if an account is currently locked due to failed login attempts.

    Args:
        email: User email address

    Returns:
        Tuple of (is_locked, lock_until_iso) where lock_until_iso is None if not locked
    """
    email_lower = email.lower()

    # Check if locked
    if email_lower not in _lockouts:
        return False, None

    lock_until = _lockouts[email_lower]
    now = datetime.utcnow()

    # Check if lockout has expired
    if now >= lock_until:
        # Lockout expired, clear it
        del _lockouts[email_lower]
        if email_lower in _failed_attempts:
            del _failed_attempts[email_lower]
        return False, None

    # Still locked
    remaining_minutes = int((lock_until - now).total_seconds() / 60)
    return True, lock_until.isoformat()


def get_failed_attempt_count(email: str) -> int:
    """
    Get the current count of failed login attempts for an email.

    Args:
        email: User email address

    Returns:
        Number of failed attempts in the current window
    """
    email_lower = email.lower()
    if email_lower not in _failed_attempts:
        return 0

    # Clean old attempts
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=ATTEMPT_WINDOW_MINUTES)
    _failed_attempts[email_lower] = [attempt for attempt in _failed_attempts[email_lower] if attempt > window_start]

    return len(_failed_attempts[email_lower])
