"""
Grafana Metrics for Security Middleware

Provides comprehensive metrics collection for redactions, failures, replays,
and security events to enable monitoring and alerting in production.
"""

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MetricType(Enum):
    """Types of security metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class SecurityMetric:
    """Individual security metric with metadata."""
    name: str
    metric_type: MetricType
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    help_text: str = ""


class SecurityMetricsCollector:
    """Collector for security middleware metrics."""

    def __init__(self, max_history: int = 1000):
        self.metrics: dict[str, float] = defaultdict(float)
        self.metric_metadata: dict[str, dict[str, Any]] = {}
        self.metric_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.lock = threading.Lock()

        # Initialize core metrics
        self._initialize_metrics()

    def _initialize_metrics(self):
        """Initialize core security metrics."""
        core_metrics = [
            # Redaction metrics
            ("redactions_applied_total", MetricType.COUNTER, "Total number of redactions applied"),
            ("redaction_failures_total", MetricType.COUNTER, "Total number of redaction failures"),
            ("redaction_duration_seconds", MetricType.HISTOGRAM, "Time spent on redaction operations"),

            # Idempotency metrics
            ("idempotency_replays_total", MetricType.COUNTER, "Total number of idempotency replays"),
            ("idempotency_cache_hits_total", MetricType.COUNTER, "Total idempotency cache hits"),
            ("idempotency_cache_misses_total", MetricType.COUNTER, "Total idempotency cache misses"),

            # Security policy metrics
            ("security_fail_closed_total", MetricType.COUNTER, "Total fail-closed policy triggers"),
            ("security_policy_violations_total", MetricType.COUNTER, "Total security policy violations"),
            ("tier_policy_enforcements_total", MetricType.COUNTER, "Total tier policy enforcements"),

            # RBAC metrics
            ("rbac_access_granted_total", MetricType.COUNTER, "Total RBAC access grants"),
            ("rbac_access_denied_total", MetricType.COUNTER, "Total RBAC access denials"),
            ("rbac_token_verifications_total", MetricType.COUNTER, "Total JWT token verifications"),

            # Multipart metrics
            ("multipart_parts_processed_total", MetricType.COUNTER, "Total multipart parts processed"),
            ("multipart_parts_total", MetricType.COUNTER, "Total multipart parts received"),
            ("multipart_bytes_total", MetricType.COUNTER, "Total multipart bytes processed"),
            ("multipart_reject_total", MetricType.COUNTER, "Total multipart rejections with reason"),
            ("multipart_processing_duration_seconds", MetricType.HISTOGRAM, "Multipart processing duration"),
            ("multipart_content_type_mismatches_total", MetricType.COUNTER, "Total content-type mismatches"),

            # Archive telemetry metrics
            ("archive_ratio_max", MetricType.GAUGE, "Maximum compression ratio detected in archives"),
            ("archive_entries_total", MetricType.COUNTER, "Total archive entries processed"),
            ("strict_mode_flag", MetricType.GAUGE, "Feature flag state for strict mode (0/1)"),
            ("strict_mode_flip_total", MetricType.COUNTER, "Total feature flag flips for annotations"),

            # Redis metrics
            ("redis_operations_total", MetricType.COUNTER, "Total Redis operations"),
            ("redis_failures_total", MetricType.COUNTER, "Total Redis operation failures"),
            ("redis_circuit_breaker_trips_total", MetricType.COUNTER, "Total circuit breaker trips"),

            # Performance metrics
            ("request_processing_duration_seconds", MetricType.HISTOGRAM, "Request processing duration"),
            ("middleware_overhead_seconds", MetricType.HISTOGRAM, "Security middleware overhead"),

            # Health metrics
            ("security_middleware_health", MetricType.GAUGE, "Security middleware health status"),
            ("active_security_contexts", MetricType.GAUGE, "Number of active security contexts"),
        ]

        for name, metric_type, help_text in core_metrics:
            self.metric_metadata[name] = {
                "type": metric_type,
                "help": help_text,
                "created_at": time.time()
            }

    def increment_counter(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None):
        """Increment a counter metric."""
        with self.lock:
            full_name = self._build_metric_name(name, labels)
            self.metrics[full_name] += value

            # Record in history
            self.metric_history[full_name].append({
                "timestamp": time.time(),
                "value": value,
                "labels": labels or {}
            })

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None):
        """Set a gauge metric value."""
        with self.lock:
            full_name = self._build_metric_name(name, labels)
            self.metrics[full_name] = value

            # Record in history
            self.metric_history[full_name].append({
                "timestamp": time.time(),
                "value": value,
                "labels": labels or {}
            })

    def record_histogram(self, name: str, value: float, labels: dict[str, str] | None = None):
        """Record a histogram metric value."""
        # For simplicity, we'll track histogram as multiple metrics
        with self.lock:
            base_name = self._build_metric_name(name, labels)

            # Record count and sum for histogram
            count_name = f"{base_name}_count"
            sum_name = f"{base_name}_sum"

            self.metrics[count_name] += 1
            self.metrics[sum_name] += value

            # Record in history
            self.metric_history[base_name].append({
                "timestamp": time.time(),
                "value": value,
                "labels": labels or {}
            })

    def _build_metric_name(self, name: str, labels: dict[str, str] | None = None) -> str:
        """Build full metric name with labels."""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_metrics(self) -> dict[str, float]:
        """Get all current metric values."""
        with self.lock:
            return self.metrics.copy()

    def get_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        with self.lock:
            # Group metrics by base name
            metric_groups = defaultdict(list)
            for full_name, value in self.metrics.items():
                base_name = full_name.split('{')[0]
                metric_groups[base_name].append((full_name, value))

            for base_name, metric_list in metric_groups.items():
                # Add help text
                help_text = self.metric_metadata.get(base_name, {}).get("help", "")
                if help_text:
                    lines.append(f"# HELP {base_name} {help_text}")

                # Add type
                metric_type = self.metric_metadata.get(base_name, {}).get("type", MetricType.COUNTER)
                lines.append(f"# TYPE {base_name} {metric_type.value}")

                # Add metrics
                for full_name, value in metric_list:
                    lines.append(f"{full_name} {value}")

                lines.append("")  # Empty line between metrics

        return "\n".join(lines)

    def get_grafana_dashboard_json(self) -> dict[str, Any]:
        """Generate Grafana dashboard JSON configuration."""
        return {
            "dashboard": {
                "title": "Ninaivalaigal Security Middleware",
                "tags": ["security", "middleware", "ninaivalaigal"],
                "timezone": "browser",
                "panels": [
                    {
                        "title": "Redaction Operations",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "rate(redactions_applied_total[5m])",
                                "legendFormat": "Redactions/sec"
                            },
                            {
                                "expr": "rate(redaction_failures_total[5m])",
                                "legendFormat": "Failures/sec"
                            }
                        ]
                    },
                    {
                        "title": "RBAC Access Control",
                        "type": "piechart",
                        "targets": [
                            {
                                "expr": "rbac_access_granted_total",
                                "legendFormat": "Granted"
                            },
                            {
                                "expr": "rbac_access_denied_total",
                                "legendFormat": "Denied"
                            }
                        ]
                    },
                    {
                        "title": "Security Policy Violations",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(security_policy_violations_total[5m])",
                                "legendFormat": "Policy Violations/sec"
                            },
                            {
                                "expr": "rate(security_fail_closed_total[5m])",
                                "legendFormat": "Fail-Closed Events/sec"
                            }
                        ]
                    },
                    {
                        "title": "Redis Health",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "redis_operations_total - redis_failures_total",
                                "legendFormat": "Successful Operations"
                            },
                            {
                                "expr": "redis_circuit_breaker_trips_total",
                                "legendFormat": "Circuit Breaker Trips"
                            }
                        ]
                    }
                ]
            }
        }


# Global metrics collector
_metrics_collector = SecurityMetricsCollector()


# Convenience functions for common metrics
def record_redaction_applied(detector_type: str = "default", tier: int = 1):
    """Record a redaction operation."""
    _metrics_collector.increment_counter(
        "redactions_applied_total",
        labels={"detector_type": detector_type, "tier": str(tier)}
    )


def record_redaction_failure(error_type: str, tier: int = 1):
    """Record a redaction failure."""
    _metrics_collector.increment_counter(
        "redaction_failures_total",
        labels={"error_type": error_type, "tier": str(tier)}
    )


def record_idempotency_replay(method: str, path_template: str):
    """Record an idempotency replay."""
    _metrics_collector.increment_counter(
        "idempotency_replays_total",
        labels={"method": method, "path_template": path_template}
    )


def record_rbac_decision(granted: bool, resource: str, permission: str):
    """Record an RBAC access decision."""
    metric_name = "rbac_access_granted_total" if granted else "rbac_access_denied_total"
    _metrics_collector.increment_counter(
        metric_name,
        labels={"resource": resource, "permission": permission}
    )


def record_security_policy_violation(policy_type: str, tier: int):
    """Record a security policy violation."""
    _metrics_collector.increment_counter(
        "security_policy_violations_total",
        labels={"policy_type": policy_type, "tier": str(tier)}
    )


def record_fail_closed_event(tier: int, threshold: int):
    """Record a fail-closed policy trigger."""
    _metrics_collector.increment_counter(
        "security_fail_closed_total",
        labels={"tier": str(tier), "threshold": str(threshold)}
    )


def record_multipart_processing(parts_count: int, bytes_count: int, duration_seconds: float):
    """Record multipart processing statistics."""
    _metrics_collector.increment_counter("multipart_parts_total", value=parts_count)
    _metrics_collector.increment_counter("multipart_bytes_total", value=bytes_count)
    _metrics_collector.record_histogram("multipart_processing_duration_seconds", duration_seconds)


def record_multipart_rejection(reason: str, endpoint: str = "unknown", tenant: str = "unknown"):
    """Record multipart rejection with specific reason."""
    _metrics_collector.increment_counter(
        "multipart_reject_total",
        labels={
            "reason": reason,
            "endpoint": endpoint,
            "tenant": tenant
        }
    )


def record_archive_telemetry(compression_ratio: float, entry_count: int):
    """Record archive compression telemetry for post-incident analysis."""
    _metrics_collector.set_gauge("archive_ratio_max", compression_ratio)
    _metrics_collector.increment_counter("archive_entries_total", value=entry_count)


def update_strict_mode_flag(enabled: bool):
    """Update strict mode feature flag state for monitoring."""
    _metrics_collector.set_gauge("strict_mode_flag", 1.0 if enabled else 0.0)
    _metrics_collector.increment_counter("strict_mode_flip_total")  # For annotations


def record_request_duration(duration_seconds: float, endpoint: str):
    """Record request processing duration."""
    _metrics_collector.record_histogram(
        "request_processing_duration_seconds",
        duration_seconds,
        labels={"endpoint": endpoint}
    )


def set_middleware_health(healthy: bool):
    """Set middleware health status."""
    _metrics_collector.set_gauge("security_middleware_health", 1.0 if healthy else 0.0)


def get_all_metrics() -> dict[str, float]:
    """Get all current metrics."""
    return _metrics_collector.get_metrics()


def get_prometheus_metrics() -> str:
    """Get metrics in Prometheus format."""
    return _metrics_collector.get_prometheus_format()


def get_grafana_dashboard() -> dict[str, Any]:
    """Get Grafana dashboard configuration."""
    return _metrics_collector.get_grafana_dashboard_json()


# Metrics middleware for FastAPI
class MetricsMiddleware:
    """FastAPI middleware to collect security metrics."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        path = scope.get("path", "unknown")
        method = scope.get("method", "unknown")

        # Track active requests
        _metrics_collector.increment_counter("active_security_contexts")

        try:
            await self.app(scope, receive, send)
        finally:
            # Record request duration
            duration = time.time() - start_time
            record_request_duration(duration, f"{method} {path}")

            # Decrement active requests
            _metrics_collector.increment_counter("active_security_contexts", value=-1)


# Metrics export endpoint
async def metrics_endpoint():
    """FastAPI endpoint to export Prometheus metrics."""
    from starlette.responses import PlainTextResponse

    metrics_text = get_prometheus_metrics()
    return PlainTextResponse(
        metrics_text,
        headers={"Content-Type": "text/plain; version=0.0.4; charset=utf-8"}
    )


# Background metrics reporter
import asyncio


async def metrics_reporter(interval: int = 60):
    """Background task to report metrics periodically."""
    import logging
    logger = logging.getLogger("metrics.reporter")

    while True:
        try:
            metrics = get_all_metrics()

            # Log key metrics
            logger.info(f"Security metrics: {len(metrics)} total metrics collected")

            # Report critical metrics
            critical_metrics = {
                k: v for k, v in metrics.items()
                if any(keyword in k for keyword in ["failure", "violation", "denied", "error"])
            }

            if critical_metrics:
                logger.warning(f"Critical security metrics: {critical_metrics}")

            await asyncio.sleep(interval)

        except Exception as e:
            logger.error(f"Metrics reporting error: {e}")
            await asyncio.sleep(interval)


# Test utilities
def generate_test_metrics():
    """Generate test metrics for dashboard validation."""
    import random

    # Simulate various security events
    for _ in range(100):
        record_redaction_applied("aws_key", random.randint(1, 5))
        record_rbac_decision(random.choice([True, False]), "memory", "read")

        if random.random() < 0.1:  # 10% failure rate
            record_redaction_failure("detector_error", random.randint(3, 5))

        if random.random() < 0.05:  # 5% policy violations
            record_security_policy_violation("tier_threshold", random.randint(3, 5))

    return get_all_metrics()
