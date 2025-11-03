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
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware

# Prometheus metrics


def _get_or_create_metric(name: str, factory, *args, **kwargs):
    """Reuse existing collector when module imports multiple times during tests."""

    registry = kwargs.pop("registry", REGISTRY)
    existing = registry._names_to_collectors.get(name)  # type: ignore[attr-defined]
    if existing is not None:
        return existing

    kwargs["registry"] = registry
    return factory(name, *args, **kwargs)


REQUESTS = _get_or_create_metric(
    "http_requests_total",
    Counter,
    "Total HTTP requests",
    ["route", "method", "code"],
)
DURATION = _get_or_create_metric(
    "http_request_duration_seconds",
    Histogram,
    "Request latency",
    ["route", "method"],
)
ERRORS = _get_or_create_metric("app_errors_total", Counter, "Application errors", ["type"])
UPTIME_S = _get_or_create_metric("app_uptime_seconds", Gauge, "Process uptime (s)")

# Context for request tracking
request_id_ctx = contextvars.ContextVar("request_id", default="-")

router = APIRouter()


@router.get("/metrics")
def metrics() -> Response:
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track request metrics and structured logging"""

    def __init__(self, app, logger_name: str = "app"):
        """Initialize instance."""
        super().__init__(app)
        self.logger = logging.getLogger(logger_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Dispatch method."""
        # Generate request ID
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx.set(rid)

        # Start timing
        start_time = time.perf_counter()

        # Extract route info
        route = request.url.path
        method = request.method

        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code

            # Record success metrics
            REQUESTS.labels(route=route, method=method, code=status_code).inc()

            return response

        except Exception as e:
            # Record error metrics
            ERRORS.labels(type=type(e).__name__).inc()
            REQUESTS.labels(route=route, method=method, code=500).inc()

            # Log error
            self._log_request(rid, route, method, 500, time.perf_counter() - start_time, error=str(e))
            raise

        finally:
            # Record duration and log request
            duration = time.perf_counter() - start_time
            DURATION.labels(route=route, method=method).observe(duration)

            if "response" in locals():
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
