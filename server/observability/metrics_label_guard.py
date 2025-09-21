"""Metrics label guard with bounded cardinality validation.

This module provides comprehensive validation for metrics labels to prevent
cardinality explosion and ensure consistent labeling across the application.

Features:
- Route template validation with allowlist
- Reason bucket validation with bounded cardinality
- Label value sanitization and normalization
- Cardinality tracking and limits enforcement
- Production-safe defaults with monitoring

Security Benefits:
- Prevents metrics cardinality explosion attacks
- Enforces consistent labeling patterns
- Provides audit trail for label violations
- Enables safe metrics collection at scale
"""

import logging
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Production-safe cardinality limits
DEFAULT_MAX_ROUTE_TEMPLATES = 100
DEFAULT_MAX_REASON_BUCKETS = 50
DEFAULT_MAX_USER_BUCKETS = 1000
DEFAULT_MAX_LABEL_LENGTH = 128
DEFAULT_CARDINALITY_WINDOW_SECONDS = 3600  # 1 hour

# Allowed route templates (expandable via configuration)
CORE_ROUTE_TEMPLATES = {
    "/contexts/{id}/memories",
    "/memories/{id}",
    "/users/{id}/contexts",
    "/auth/login",
    "/auth/logout",
    "/auth/refresh",
    "/healthz",
    "/healthz/config",
    "/metrics",
    "/upload",
    "/search",
    "/admin/users",
    "/admin/policies"
}

# Allowed reason buckets for different metric types
SECURITY_REASON_BUCKETS = {
    "jwt_invalid", "jwt_expired", "jwt_malformed", "jwt_missing",
    "rbac_denied", "rbac_missing_role", "rbac_invalid_scope",
    "multipart_rejected", "multipart_size_exceeded", "multipart_executable_blocked",
    "rate_limited", "ip_blocked", "suspicious_activity"
}

PERFORMANCE_REASON_BUCKETS = {
    "timeout", "circuit_breaker", "retry_exhausted", "queue_full",
    "memory_pressure", "cpu_throttled", "disk_full", "network_error"
}

ERROR_REASON_BUCKETS = {
    "validation_failed", "database_error", "external_service_error",
    "configuration_error", "dependency_unavailable", "unknown_error"
}

ALL_REASON_BUCKETS = SECURITY_REASON_BUCKETS | PERFORMANCE_REASON_BUCKETS | ERROR_REASON_BUCKETS

@dataclass
class CardinalityTracker:
    """Tracks label cardinality over time windows."""
    route_templates: set[str] = field(default_factory=set)
    reason_buckets: set[str] = field(default_factory=set)
    user_buckets: set[str] = field(default_factory=set)
    label_combinations: set[str] = field(default_factory=set)
    window_start: float = field(default_factory=time.time)
    violations: list[dict[str, Any]] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def reset_window(self) -> None:
        """Reset tracking window."""
        with self._lock:
            self.route_templates.clear()
            self.reason_buckets.clear()
            self.user_buckets.clear()
            self.label_combinations.clear()
            self.violations.clear()
            self.window_start = time.time()

    def should_reset_window(self, window_seconds: int) -> bool:
        """Check if tracking window should be reset."""
        return time.time() - self.window_start > window_seconds

@dataclass
class MetricsLabelGuardConfig:
    """Configuration for metrics label validation."""
    max_route_templates: int = DEFAULT_MAX_ROUTE_TEMPLATES
    max_reason_buckets: int = DEFAULT_MAX_REASON_BUCKETS
    max_user_buckets: int = DEFAULT_MAX_USER_BUCKETS
    max_label_length: int = DEFAULT_MAX_LABEL_LENGTH
    cardinality_window_seconds: int = DEFAULT_CARDINALITY_WINDOW_SECONDS
    allowed_route_templates: set[str] = field(default_factory=lambda: CORE_ROUTE_TEMPLATES.copy())
    allowed_reason_buckets: set[str] = field(default_factory=lambda: ALL_REASON_BUCKETS.copy())
    strict_mode: bool = True  # Fail-closed for production safety
    enable_cardinality_tracking: bool = True

class MetricsLabelGuard:
    """Comprehensive metrics label validation with cardinality bounds."""

    def __init__(self, config: MetricsLabelGuardConfig | None = None):
        self.config = config or MetricsLabelGuardConfig()
        self.tracker = CardinalityTracker()
        self._route_template_pattern = re.compile(r'^/[a-zA-Z0-9_/-]*(\{[a-zA-Z0-9_]+\}[a-zA-Z0-9_/-]*)*$')

    def validate_labels(self, labels: dict[str, str], metric_name: str = "") -> dict[str, Any]:
        """
        Validate metrics labels with cardinality bounds.
        
        Args:
            labels: Dictionary of label key-value pairs
            metric_name: Name of the metric for context
            
        Returns:
            Validation result with sanitized labels and violations
            
        Raises:
            ValueError: If labels violate cardinality or format rules in strict mode
        """
        result = {
            "valid": True,
            "sanitized_labels": {},
            "violations": [],
            "cardinality_stats": {}
        }

        # Reset tracking window if needed
        if self.config.enable_cardinality_tracking and self.tracker.should_reset_window(
            self.config.cardinality_window_seconds
        ):
            self.tracker.reset_window()

        # Validate each label
        for key, value in labels.items():
            try:
                sanitized_value = self._validate_label(key, value, metric_name)
                result["sanitized_labels"][key] = sanitized_value
            except ValueError as e:
                result["valid"] = False
                result["violations"].append({
                    "type": "label_validation_failed",
                    "label_key": key,
                    "label_value": value,
                    "message": str(e),
                    "severity": "high"
                })

                if self.config.strict_mode:
                    raise

        # Check cardinality bounds
        if self.config.enable_cardinality_tracking:
            cardinality_result = self._check_cardinality_bounds(result["sanitized_labels"])
            result["cardinality_stats"] = cardinality_result

            if not cardinality_result["within_bounds"]:
                result["valid"] = False
                result["violations"].extend(cardinality_result["violations"])

                if self.config.strict_mode:
                    raise ValueError(f"Cardinality bounds exceeded: {cardinality_result['violations']}")

        # Log violations for monitoring
        if result["violations"]:
            logger.warning(
                "Metrics label validation violations",
                extra={
                    "metric_name": metric_name,
                    "violations": result["violations"],
                    "cardinality_stats": result.get("cardinality_stats", {})
                }
            )

        return result

    def _validate_label(self, key: str, value: str, metric_name: str) -> str:
        """Validate individual label key-value pair."""
        # Length validation
        if len(value) > self.config.max_label_length:
            raise ValueError(f"Label '{key}' value exceeds maximum length {self.config.max_label_length}")

        # Key-specific validation
        if key == "route":
            return self._validate_route_template(value)
        elif key == "reason":
            return self._validate_reason_bucket(value)
        elif key == "user_id":
            return self._validate_user_bucket(value)
        else:
            # Generic label validation
            return self._sanitize_label_value(value)

    def _validate_route_template(self, route: str) -> str:
        """Validate route template against allowlist."""
        if not route:
            raise ValueError("Route template cannot be empty")

        # Normalize route template
        normalized_route = self._normalize_route_template(route)

        # Check against allowlist
        if normalized_route not in self.config.allowed_route_templates:
            raise ValueError(f"Route template '{normalized_route}' not in allowlist")

        # Check pattern format
        if not self._route_template_pattern.match(normalized_route):
            raise ValueError(f"Route template '{normalized_route}' has invalid format")

        return normalized_route

    def _validate_reason_bucket(self, reason: str) -> str:
        """Validate reason bucket against allowlist."""
        if not reason:
            raise ValueError("Reason bucket cannot be empty")

        # Normalize reason bucket
        normalized_reason = reason.lower().strip()

        # Check against allowlist
        if normalized_reason not in self.config.allowed_reason_buckets:
            raise ValueError(f"Reason bucket '{normalized_reason}' not in allowlist")

        return normalized_reason

    def _validate_user_bucket(self, user_id: str) -> str:
        """Validate user bucket with anonymization."""
        if not user_id:
            raise ValueError("User ID cannot be empty")

        # Anonymize user ID for metrics (hash to bounded set)
        user_hash = hash(user_id) % 10000  # Bound to 10k buckets
        return f"user_{user_hash:04d}"

    def _sanitize_label_value(self, value: str) -> str:
        """Sanitize generic label value."""
        # Remove potentially problematic characters
        sanitized = re.sub(r'[^\w\-\.]', '_', value)

        # Truncate if too long
        if len(sanitized) > self.config.max_label_length:
            sanitized = sanitized[:self.config.max_label_length]

        return sanitized

    def _normalize_route_template(self, route: str) -> str:
        """Normalize route template format."""
        # Remove query parameters
        route = route.split('?')[0]

        # Ensure starts with /
        if not route.startswith('/'):
            route = '/' + route

        # Remove trailing slash (except root)
        if len(route) > 1 and route.endswith('/'):
            route = route[:-1]

        return route

    def _check_cardinality_bounds(self, labels: dict[str, str]) -> dict[str, Any]:
        """Check if labels are within cardinality bounds."""
        result = {
            "within_bounds": True,
            "violations": [],
            "current_cardinality": {},
            "limits": {
                "route_templates": self.config.max_route_templates,
                "reason_buckets": self.config.max_reason_buckets,
                "user_buckets": self.config.max_user_buckets
            }
        }

        with self.tracker._lock:
            # Track route templates
            if "route" in labels:
                self.tracker.route_templates.add(labels["route"])
                if len(self.tracker.route_templates) > self.config.max_route_templates:
                    result["within_bounds"] = False
                    result["violations"].append({
                        "type": "route_cardinality_exceeded",
                        "current": len(self.tracker.route_templates),
                        "limit": self.config.max_route_templates,
                        "severity": "critical"
                    })

            # Track reason buckets
            if "reason" in labels:
                self.tracker.reason_buckets.add(labels["reason"])
                if len(self.tracker.reason_buckets) > self.config.max_reason_buckets:
                    result["within_bounds"] = False
                    result["violations"].append({
                        "type": "reason_cardinality_exceeded",
                        "current": len(self.tracker.reason_buckets),
                        "limit": self.config.max_reason_buckets,
                        "severity": "critical"
                    })

            # Track user buckets
            if "user_id" in labels:
                self.tracker.user_buckets.add(labels["user_id"])
                if len(self.tracker.user_buckets) > self.config.max_user_buckets:
                    result["within_bounds"] = False
                    result["violations"].append({
                        "type": "user_cardinality_exceeded",
                        "current": len(self.tracker.user_buckets),
                        "limit": self.config.max_user_buckets,
                        "severity": "high"
                    })

            # Track label combinations
            label_combo = "|".join(f"{k}={v}" for k, v in sorted(labels.items()))
            self.tracker.label_combinations.add(label_combo)

            # Update current cardinality stats
            result["current_cardinality"] = {
                "route_templates": len(self.tracker.route_templates),
                "reason_buckets": len(self.tracker.reason_buckets),
                "user_buckets": len(self.tracker.user_buckets),
                "total_combinations": len(self.tracker.label_combinations)
            }

        return result

    def get_cardinality_stats(self) -> dict[str, Any]:
        """Get current cardinality statistics."""
        with self.tracker._lock:
            return {
                "window_start": self.tracker.window_start,
                "window_duration": time.time() - self.tracker.window_start,
                "cardinality": {
                    "route_templates": len(self.tracker.route_templates),
                    "reason_buckets": len(self.tracker.reason_buckets),
                    "user_buckets": len(self.tracker.user_buckets),
                    "total_combinations": len(self.tracker.label_combinations)
                },
                "limits": {
                    "route_templates": self.config.max_route_templates,
                    "reason_buckets": self.config.max_reason_buckets,
                    "user_buckets": self.config.max_user_buckets
                },
                "violations_count": len(self.tracker.violations)
            }

# Global instance for application use
_default_guard = None
_guard_lock = threading.Lock()

def get_metrics_label_guard(config: MetricsLabelGuardConfig | None = None) -> MetricsLabelGuard:
    """Get or create the default metrics label guard instance."""
    global _default_guard

    if _default_guard is None:
        with _guard_lock:
            if _default_guard is None:
                _default_guard = MetricsLabelGuard(config)

    return _default_guard

def validate_metric_labels(labels: dict[str, str], metric_name: str = "") -> dict[str, str]:
    """
    Convenience function for validating metrics labels.
    
    Args:
        labels: Dictionary of label key-value pairs
        metric_name: Name of the metric for context
        
    Returns:
        Sanitized labels dictionary
        
    Raises:
        ValueError: If labels violate validation rules
    """
    guard = get_metrics_label_guard()
    result = guard.validate_labels(labels, metric_name)

    if not result["valid"]:
        violations = [v["message"] for v in result["violations"]]
        raise ValueError(f"Metrics label validation failed: {violations}")

    return result["sanitized_labels"]

# Legacy compatibility function
def validate_metric_labels_legacy(labels: dict[str, str]) -> None:
    """Legacy validation function for backward compatibility."""
    try:
        validate_metric_labels(labels)
    except ValueError as e:
        # Convert to legacy exception format
        if "route" in str(e):
            raise ValueError("route label must be a known template, not a concrete path")
        elif "reason" in str(e):
            raise ValueError("invalid reason label")
        else:
            raise

# Export key functions and classes
__all__ = [
    "MetricsLabelGuard",
    "MetricsLabelGuardConfig",
    "CardinalityTracker",
    "validate_metric_labels",
    "validate_metric_labels_legacy",
    "get_metrics_label_guard",
    "CORE_ROUTE_TEMPLATES",
    "ALL_REASON_BUCKETS"
]
