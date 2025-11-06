# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
SPEC-114 Compliant Rate Limiting for Authentication Endpoints

Rate limiting configuration:
- Login: 5 attempts per 15 minutes (900 seconds)
- Signup: 3 attempts per 10 minutes (600 seconds)
"""

from __future__ import annotations

import time
from typing import Final


class AuthRateLimiter:
    """Rate limiter for authentication endpoints - SPEC-114 compliant"""

    def __init__(self):
        self.attempts: dict[str, list[float]] = {}

    def is_allowed(self, identifier: str, endpoint: str = "login") -> tuple[bool, str | None, dict]:
        """
        Check if request is within rate limit.

        SPEC-114 requirements:
        - Login: 5 attempts per 15 minutes (900 seconds)
        - Signup: 3 attempts per 10 minutes (600 seconds)

        Args:
            identifier: Unique identifier (e.g., IP:email)
            endpoint: Endpoint type ("login" or "signup")

        Returns:
            Tuple of (is_allowed, error_message, rate_limit_info)
            rate_limit_info contains:
            - limit: Maximum allowed attempts
            - remaining: Remaining attempts
            - reset_time: Unix timestamp when limit resets
            - retry_after: Seconds until retry is allowed
        """
        now = time.time()

        # SPEC-114 compliant limits
        if endpoint == "login":
            max_attempts: Final[int] = 5
            window_seconds: Final[int] = 900  # 15 minutes
        elif endpoint == "signup":
            max_attempts: Final[int] = 3
            window_seconds: Final[int] = 600  # 10 minutes
        else:
            # Default for other auth endpoints
            max_attempts = 10
            window_seconds = 300  # 5 minutes

        window_start = now - window_seconds

        # Clean old attempts
        if identifier in self.attempts:
            self.attempts[identifier] = [attempt for attempt in self.attempts[identifier] if attempt > window_start]
        else:
            self.attempts[identifier] = []

        # Calculate remaining attempts and reset time
        current_attempts = len(self.attempts[identifier])
        remaining = max(0, max_attempts - current_attempts)

        # Calculate reset time (when oldest attempt expires)
        if self.attempts[identifier]:
            oldest_attempt = min(self.attempts[identifier])
            reset_time = oldest_attempt + window_seconds
        else:
            reset_time = now + window_seconds

        # Check limit
        if current_attempts >= max_attempts:
            retry_after = max(0, int(reset_time - now))
            error_msg = f"Too many {endpoint} attempts. Please try again in {retry_after // 60} minutes."
            rate_info = {"limit": max_attempts, "remaining": 0, "reset_time": reset_time, "retry_after": retry_after}
            return False, error_msg, rate_info

        # Record attempt
        self.attempts[identifier].append(now)

        # Recalculate remaining after recording
        remaining = max(0, max_attempts - len(self.attempts[identifier]))

        rate_info = {"limit": max_attempts, "remaining": remaining, "reset_time": reset_time, "retry_after": 0}
        return True, None, rate_info
