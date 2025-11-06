# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Security Monitoring Module for Admin Analytics

SPEC-030: US-262 - Security Monitoring Dashboard
Tracks authentication failures, suspicious activity, and security metrics.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Import failed attempts and lockouts from login_security module
# Note: These are internal variables, imported for monitoring purposes
try:
    from utils import login_security

    _failed_attempts = login_security._failed_attempts
    _lockouts = login_security._lockouts
    get_failed_attempt_count = login_security.get_failed_attempt_count
except ImportError:
    # Fallback if module not available
    _failed_attempts = {}
    _lockouts = {}

    def get_failed_attempt_count(email: str) -> int:
        return 0


# In-memory storage for security metrics (can be migrated to database later)
_security_metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)


def record_security_event(event_type: str, details: Dict[str, Any]) -> None:
    """
    Record a security event for monitoring.

    Args:
        event_type: Type of security event (login_failure, rate_limit, account_locked, etc.)
        details: Event details (ip, user_id, email, etc.)
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        **details,
    }
    _security_metrics[event_type].append(event)

    # Keep only last 1000 events per type
    if len(_security_metrics[event_type]) > 1000:
        _security_metrics[event_type] = _security_metrics[event_type][-1000:]


def get_auth_failures_by_period(hours: int = 24) -> int:
    """
    Get total authentication failures in the specified period.

    Args:
        hours: Number of hours to look back

    Returns:
        Total number of failed login attempts
    """
    count = 0
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    for email, attempts in _failed_attempts.items():
        for attempt_time in attempts:
            if attempt_time > cutoff_time:
                count += 1

    return count


def get_failed_logins_by_user(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get top users with failed login attempts.

    Args:
        limit: Maximum number of users to return

    Returns:
        List of dicts with user email and failure count
    """
    user_failures = defaultdict(int)
    cutoff_time = datetime.utcnow() - timedelta(days=30)

    for email, attempts in _failed_attempts.items():
        recent_attempts = [a for a in attempts if a > cutoff_time]
        if recent_attempts:
            user_failures[email] = len(recent_attempts)

    # Sort by failure count and return top users
    sorted_users = sorted(user_failures.items(), key=lambda x: x[1], reverse=True)[:limit]

    return [
        {
            "email": email,
            "failure_count": count,
            "risk_level": "high" if count >= 5 else "medium" if count >= 3 else "low",
        }
        for email, count in sorted_users
    ]


def get_failed_logins_by_ip(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get top IP addresses with failed login attempts.

    Note: This is a simplified version. In production, this would query
    from audit logs stored in database with IP addresses.

    Args:
        limit: Maximum number of IPs to return

    Returns:
        List of dicts with IP address and failure count
    """
    # For now, return empty list since we don't track IPs in failed_attempts
    # In production, this would query from audit_logs table
    return []


def detect_suspicious_ips(threshold: int = 10, hours: int = 24) -> List[Dict[str, Any]]:
    """
    Detect suspicious IP addresses based on failed login attempts.

    Args:
        threshold: Minimum number of failures to flag as suspicious
        hours: Time window to check

    Returns:
        List of suspicious IPs with details
    """
    # For now, return empty list since we don't track IPs directly
    # In production, this would query from audit_logs table
    # This is a placeholder that can be enhanced when audit logs are in database
    return []


def get_account_lockouts() -> int:
    """
    Get count of currently locked accounts.

    Returns:
        Number of accounts currently locked
    """
    now = datetime.utcnow()
    locked_count = 0

    for email, lock_until in _lockouts.items():
        if lock_until > now:
            locked_count += 1

    return locked_count


def calculate_auth_success_rate(hours: int = 24) -> float:
    """
    Calculate authentication success rate.

    Note: Simplified calculation. In production, this would query
    from audit logs for accurate success/failure counts.

    Args:
        hours: Time window to calculate

    Returns:
        Success rate as percentage (0-100)
    """
    failures = get_auth_failures_by_period(hours)

    # Estimate: assume 10 successful logins for every failure
    # In production, query actual success/failure counts from audit logs
    estimated_successes = failures * 10 if failures > 0 else 100
    total = failures + estimated_successes

    if total == 0:
        return 100.0

    return round((estimated_successes / total) * 100, 2)


def calculate_security_health_score() -> float:
    """
    Calculate overall security health score (0-100).

    Returns:
        Security health score
    """
    score = 100.0

    # Deduct points for various security issues
    locked_accounts = get_account_lockouts()
    if locked_accounts > 0:
        score -= min(locked_accounts * 2, 20)  # Max 20 points deduction

    failures_24h = get_auth_failures_by_period(24)
    if failures_24h > 50:
        score -= min((failures_24h - 50) * 0.5, 30)  # Max 30 points deduction

    # Ensure score is between 0 and 100
    return max(0.0, min(100.0, score))


def get_security_metrics() -> Dict[str, Any]:
    """
    Get comprehensive security metrics for admin dashboard.

    Returns:
        Dictionary with all security metrics
    """
    now = datetime.utcnow()

    # Calculate metrics for different time periods
    auth_failures_24h = get_auth_failures_by_period(24)
    auth_failures_7d = get_auth_failures_by_period(24 * 7)
    auth_failures_30d = get_auth_failures_by_period(24 * 30)

    # Get top failed logins
    failed_logins_by_user = get_failed_logins_by_user(limit=10)
    failed_logins_by_ip = get_failed_logins_by_ip(limit=10)
    suspicious_ips = detect_suspicious_ips(threshold=10, hours=24)

    # Calculate rates and scores
    auth_success_rate = calculate_auth_success_rate(24)
    security_health_score = calculate_security_health_score()
    active_security_incidents = get_account_lockouts()

    return {
        "auth_failures_24h": auth_failures_24h,
        "auth_failures_7d": auth_failures_7d,
        "auth_failures_30d": auth_failures_30d,
        "failed_logins_by_user": failed_logins_by_user,
        "failed_logins_by_ip": failed_logins_by_ip,
        "suspicious_ips": suspicious_ips,
        "active_security_incidents": active_security_incidents,
        "auth_success_rate": auth_success_rate,
        "security_health_score": security_health_score,
        "unauthorized_access_attempts": 0,  # Placeholder - would query from audit logs
        "account_lockouts": active_security_incidents,
        "rate_limit_exceeded_count": 0,  # Placeholder - would track from rate limiter
        "timestamp": now.isoformat(),
    }
