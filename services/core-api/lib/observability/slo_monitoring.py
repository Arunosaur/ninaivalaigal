#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
SLO Monitoring & Compliance Tracking

Implements SPEC-018 Service Level Objectives monitoring:
- Availability tracking (99.9% target)
- Response time P95 monitoring (<200ms target)
- Error rate monitoring (<0.1% target)
- SLO compliance calculation and alerting
"""

import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import structlog
from prometheus_client import Counter, Gauge, Histogram

logger = structlog.get_logger(__name__)

# SLO Targets
SLO_TARGETS = {
    "availability": 0.999,  # 99.9%
    "response_time_p95": 0.2,  # 200ms
    "error_rate": 0.001,  # 0.1%
}

# Prometheus metrics for SLO tracking
SLO_UPTIME_RATIO = Gauge("slo_uptime_ratio", "Service availability ratio", ["window"])
SLO_RESPONSE_TIME_P95 = Gauge("slo_response_time_p95_seconds", "95th percentile response time", ["window"])
SLO_ERROR_RATE = Gauge("slo_error_rate", "Error rate ratio", ["window"])
SLO_COMPLIANCE = Gauge("slo_compliance", "SLO compliance status", ["slo_type", "window"])


# Request tracking for SLO calculations
class SLOTracker:
    """Tracks service metrics for SLO compliance"""

    def __init__(self, max_samples: int = 10000):
        self.max_samples = max_samples

        # Response time tracking (last hour)
        self.response_times = deque(maxlen=max_samples)

        # Error tracking (last hour)
        self.total_requests = deque(maxlen=max_samples)
        self.error_requests = deque(maxlen=max_samples)

        # Availability tracking (last 24h)
        self.uptime_periods = deque(maxlen=86400)  # 24h of seconds
        self.downtime_periods = deque(maxlen=86400)

        # Last cleanup time
        self.last_cleanup = time.time()

    def record_request(self, response_time: float, is_error: bool, is_available: bool = True):
        """Record a request for SLO tracking"""
        now = time.time()

        # Clean old data (older than 1 hour for response times, 24h for availability)
        self._cleanup_old_data(now)

        # Track response times (last hour)
        self.response_times.append((now, response_time))

        # Track errors (last hour)
        self.total_requests.append((now, 1))
        if is_error:
            self.error_requests.append((now, 1))

        # Track availability (last 24h)
        if is_available:
            self.uptime_periods.append(now)
        else:
            self.downtime_periods.append(now)

    def _cleanup_old_data(self, now: float):
        """Remove data older than tracking windows"""
        # Clean response times and errors (older than 1 hour)
        one_hour_ago = now - 3600

        while self.response_times and self.response_times[0][0] < one_hour_ago:
            self.response_times.popleft()

        while self.total_requests and self.total_requests[0][0] < one_hour_ago:
            self.total_requests.popleft()

        while self.error_requests and self.error_requests[0][0] < one_hour_ago:
            self.error_requests.popleft()

        # Clean availability data (older than 24 hours)
        one_day_ago = now - 86400

        while self.uptime_periods and self.uptime_periods[0] < one_day_ago:
            self.uptime_periods.popleft()

        while self.downtime_periods and self.downtime_periods[0] < one_day_ago:
            self.downtime_periods.popleft()

    def calculate_slo_metrics(self, window: str = "1h") -> Dict[str, float]:
        """Calculate current SLO metrics"""
        now = time.time()

        if window == "1h":
            # Use last hour of data
            cutoff = now - 3600
            response_times = [rt for ts, rt in self.response_times if ts >= cutoff]
            total_requests = sum(1 for ts, _ in self.total_requests if ts >= cutoff)
            error_requests = sum(1 for ts, _ in self.error_requests if ts >= cutoff)
        elif window == "24h":
            # Use last 24 hours for availability, last hour for performance
            cutoff_24h = now - 86400
            cutoff_1h = now - 3600

            response_times = [rt for ts, rt in self.response_times if ts >= cutoff_1h]
            total_requests = sum(1 for ts, _ in self.total_requests if ts >= cutoff_1h)
            error_requests = sum(1 for ts, _ in self.error_requests if ts >= cutoff_1h)
        elif window == "7d":
            # Use last 7 days for availability, last hour for performance
            cutoff_7d = now - 604800
            cutoff_1h = now - 3600

            response_times = [rt for ts, rt in self.response_times if ts >= cutoff_1h]
            total_requests = sum(1 for ts, _ in self.total_requests if ts >= cutoff_1h)
            error_requests = sum(1 for ts, _ in self.error_requests if ts >= cutoff_1h)
        else:
            raise ValueError(f"Unsupported window: {window}")

        # Calculate metrics
        metrics = {}

        # Availability (based on last 24h)
        if window == "24h":
            uptime_count = len([ts for ts in self.uptime_periods if ts >= cutoff_24h])
            downtime_count = len([ts for ts in self.downtime_periods if ts >= cutoff_24h])
            total_periods = uptime_count + downtime_count

            if total_periods > 0:
                metrics["availability"] = uptime_count / total_periods
            else:
                metrics["availability"] = 1.0  # Assume available if no data
        else:
            # For 1h window, use recent availability
            metrics["availability"] = 1.0 if len(self.downtime_periods) == 0 else 0.99

        # Response time P95
        if response_times:
            sorted_times = sorted(response_times)
            p95_index = int(len(sorted_times) * 0.95)
            metrics["response_time_p95"] = sorted_times[min(p95_index, len(sorted_times) - 1)]
        else:
            metrics["response_time_p95"] = 0.0

        # Error rate
        if total_requests > 0:
            metrics["error_rate"] = error_requests / total_requests
        else:
            metrics["error_rate"] = 0.0

        return metrics

    def check_slo_compliance(self, window: str = "1h") -> Dict[str, bool]:
        """Check SLO compliance status"""
        metrics = self.calculate_slo_metrics(window)

        compliance = {}

        # Check availability
        compliance["availability"] = metrics["availability"] >= SLO_TARGETS["availability"]

        # Check response time
        compliance["response_time_p95"] = metrics["response_time_p95"] <= SLO_TARGETS["response_time_p95"]

        # Check error rate
        compliance["error_rate"] = metrics["error_rate"] <= SLO_TARGETS["error_rate"]

        # Overall compliance
        compliance["overall"] = all(compliance.values())

        return compliance

    def update_prometheus_metrics(self):
        """Update Prometheus metrics with current SLO values"""
        for window in ["1h", "24h"]:
            try:
                metrics = self.calculate_slo_metrics(window)
                compliance = self.check_slo_compliance(window)

                # Update Gauges
                SLO_UPTIME_RATIO.labels(window=window).set(metrics["availability"])
                SLO_RESPONSE_TIME_P95.labels(window=window).set(metrics["response_time_p95"])
                SLO_ERROR_RATE.labels(window=window).set(metrics["error_rate"])

                # Update compliance metrics
                for slo_type, is_compliant in compliance.items():
                    if slo_type != "overall":
                        SLO_COMPLIANCE.labels(slo_type=slo_type, window=window).set(1.0 if is_compliant else 0.0)

            except Exception as e:
                logger.error("slo_prometheus_update_failed", window=window, error=str(e))


# Global SLO tracker instance
slo_tracker = SLOTracker()


def get_slo_status(window: str = "1h") -> Dict:
    """Get comprehensive SLO status for health endpoints"""
    try:
        metrics = slo_tracker.calculate_slo_metrics(window)
        compliance = slo_tracker.check_slo_compliance(window)

        return {
            "window": window,
            "targets": SLO_TARGETS,
            "current": metrics,
            "compliance": compliance,
            "overall_status": "healthy" if compliance["overall"] else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("slo_status_calculation_failed", error=str(e))
        return {
            "window": window,
            "overall_status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


def record_slo_request(response_time: float, is_error: bool, is_available: bool = True):
    """Record a request for SLO tracking (called by middleware)"""
    slo_tracker.record_request(response_time, is_error, is_available)
    slo_tracker.update_prometheus_metrics()


def get_slo_summary() -> Dict:
    """Get SLO summary for monitoring dashboards"""
    summary = {}

    for window in ["1h", "24h"]:
        try:
            status = get_slo_status(window)
            summary[window] = {
                "overall_status": status["overall_status"],
                "availability": status["current"]["availability"],
                "response_time_p95": status["current"]["response_time_p95"],
                "error_rate": status["current"]["error_rate"],
                "compliance": status["compliance"]["overall"],
            }
        except Exception as e:
            summary[window] = {"error": str(e)}

    return summary
