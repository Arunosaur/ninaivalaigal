#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Prometheus Metrics & Middleware

Provides RED metrics (Rate/Errors/Duration) and request tracking.
"""

import contextvars
import json
import logging
import time
import uuid
from collections.abc import Callable

from fastapi import APIRouter, Request, Response

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create mock classes for when prometheus_client is not available
    class Counter:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def inc(self, *args, **kwargs):
            pass
    
    class Gauge:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def set(self, *args, **kwargs):
            pass
    
    class Histogram:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def observe(self, *args, **kwargs):
            pass
    
    def generate_latest():
        return b"# Prometheus metrics not available\n"
    
    CONTENT_TYPE_LATEST = "text/plain"

from starlette.middleware.base import BaseHTTPMiddleware

# Prometheus metrics with SLO-aware buckets (only if available)
if PROMETHEUS_AVAILABLE:
    REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["route", "method", "code"])
    DURATION = Histogram(
        "http_request_duration_seconds",
        "Request latency with SLO buckets",
        ["route", "method"],
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.5, 1.0, 2.5, 5.0, 10.0],  # SLO: <200ms = 0.2s
    )
    ERRORS = Counter("app_errors_total", "Application errors", ["type"])
    UPTIME_S = Gauge("app_uptime_seconds", "Process uptime (s)")

    # SLO-specific metrics
    SLO_REQUEST_DURATION = Histogram(
        "slo_request_duration_seconds",
        "SLO request duration tracking",
        ["endpoint_category"],
        buckets=[0.01, 0.025, 0.05, 0.1, 0.2, 0.5, 1.0],  # Focus on <200ms range
    )
    SLO_ERROR_COUNTER = Counter("slo_errors_total", "SLO-tracked errors", ["endpoint_category"])
    SLO_SUCCESS_COUNTER = Counter("slo_success_total", "SLO-tracked successes", ["endpoint_category"])
else:
    # Fallback no-op metrics when prometheus_client is not available
    REQUESTS = Counter()
    DURATION = Histogram()
    ERRORS = Counter()
    UPTIME_S = Gauge()
    SLO_REQUEST_DURATION = Histogram()
    SLO_ERROR_COUNTER = Counter()
    SLO_SUCCESS_COUNTER = Counter()

# Context for request tracking
request_id_ctx = contextvars.ContextVar("request_id", default="-")

router = APIRouter()


@router.get("/metrics")
def metrics() -> Response:
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track request metrics and structured logging with SLO integration"""

    def __init__(self, app, logger_name: str = "app"):
        """Initialize instance."""
        super().__init__(app)
        self.logger = logging.getLogger(logger_name)

    def _get_endpoint_category(self, route: str) -> str:
        """Categorize endpoints for SLO tracking"""
        if route.startswith("/health") or route.startswith("/ready"):
            return "health"
        elif route.startswith("/auth"):
            return "auth"
        elif route.startswith("/memory"):
            return "memory"
        elif route.startswith("/team"):
            return "team"
        elif route.startswith("/user"):
            return "user"
        elif route.startswith("/admin"):
            return "admin"
        elif route.startswith("/metrics"):
            return "metrics"
        else:
            return "other"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Dispatch method with SLO tracking."""
        # Generate request ID
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx.set(rid)

        # Start timing
        start_time = time.perf_counter()

        # Extract route info
        route = request.url.path
        method = request.method
        endpoint_category = self._get_endpoint_category(route)

        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code

            # Record success metrics
            REQUESTS.labels(route=route, method=method, code=status_code).inc()

            # Track SLO metrics
            duration = time.perf_counter() - start_time
            is_error = status_code >= 500
            is_available = status_code < 503  # Consider 503 as unavailable

            # Record duration histogram (for latency dashboards)
            DURATION.labels(route=route, method=method).observe(duration)

            # Record SLO metrics
            SLO_REQUEST_DURATION.labels(endpoint_category=endpoint_category).observe(duration)

            if is_error:
                SLO_ERROR_COUNTER.labels(endpoint_category=endpoint_category).inc()
            else:
                SLO_SUCCESS_COUNTER.labels(endpoint_category=endpoint_category).inc()

            # Update SLO tracker if available
            try:
                from .slo_monitoring import record_slo_request

                record_slo_request(duration, is_error, is_available)
            except ImportError:
                # SLO monitoring not available - skip
                pass

            return response

        except Exception as e:
            # Record error metrics
            duration = time.perf_counter() - start_time
            is_error = True
            is_available = False

            ERRORS.labels(type=type(e).__name__).inc()
            REQUESTS.labels(route=route, method=method, code=500).inc()

            # Record duration histogram even for errors
            DURATION.labels(route=route, method=method).observe(duration)

            # Track SLO metrics for exceptions
            SLO_REQUEST_DURATION.labels(endpoint_category=endpoint_category).observe(duration)
            SLO_ERROR_COUNTER.labels(endpoint_category=endpoint_category).inc()

            # Update SLO tracker
            try:
                from .slo_monitoring import record_slo_request

                record_slo_request(duration, is_error, is_available)
            except ImportError:
                pass

            # Log error
            self._log_request(rid, route, method, 500, duration, error=str(e))
            raise

        finally:
            # Record duration and log request
            if "response" in locals():
                duration = time.perf_counter() - start_time
                self._log_request(rid, route, method, response.status_code, duration)

    def _log_request(
        self,
        request_id: str,
        path: str,
        method: str,
        status: int,
        duration: float,
        error: str = None,
    ):
        """Log structured request information"""
        log_data = {
            "ts": time.time(),
            "level": "error" if error else "info",
            "msg": "request",
            "path": path,
            "method": method,
            "status": status,
            "request_id": request_id,
            "duration_ms": int(duration * 1000),
        }

        if error:
            log_data["error"] = error

        self.logger.info(json.dumps(log_data))
