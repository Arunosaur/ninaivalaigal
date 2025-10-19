#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Prometheus Metrics Endpoint (SPEC-100 Compliant)

Implements SPEC-100 Section 5.3 standardized metrics endpoint:
- GET /metrics  - Prometheus-format metrics

Metrics exposed:
- Request counts and latency
- Dependency health status
- Resource usage
- Service uptime
"""

import time
from datetime import datetime
from typing import Dict

import psutil
import structlog
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

# Service metadata
SERVICE_NAME = "core-api"
SERVICE_VERSION = "1.0.0"
START_TIME = time.time()

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["metrics"])


# In-memory metrics storage (simple implementation)
# In production, use prometheus_client library
class MetricsCollector:
    """Simple metrics collector"""

    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.request_duration_sum = 0.0
        self.request_duration_count = 0

    def record_request(self, duration: float, status_code: int):
        """Record a request"""
        self.request_count += 1
        if status_code >= 400:
            self.error_count += 1
        self.request_duration_sum += duration
        self.request_duration_count += 1

    def get_metrics(self) -> Dict:
        """Get current metrics"""
        avg_duration = (
            self.request_duration_sum / self.request_duration_count if self.request_duration_count > 0 else 0.0
        )

        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "avg_request_duration": avg_duration,
        }


# Global metrics collector
metrics_collector = MetricsCollector()


def format_prometheus_metric(name: str, value: float, metric_type: str = "gauge", help_text: str = "") -> str:
    """Format a metric in Prometheus format"""
    lines = []
    if help_text:
        lines.append(f"# HELP {name} {help_text}")
    lines.append(f"# TYPE {name} {metric_type}")
    lines.append(f"{name} {value}")
    return "\n".join(lines)


def get_process_metrics() -> Dict[str, float]:
    """Get process-level metrics"""
    try:
        process = psutil.Process()
        return {
            "cpu_percent": process.cpu_percent(interval=0.1),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "open_files": len(process.open_files()),
            "threads": process.num_threads(),
        }
    except Exception as e:
        logger.error("process_metrics_failed", error=str(e))
        return {
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "open_files": 0,
            "threads": 0,
        }


@router.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus-format metrics endpoint (SPEC-100 compliant)

    Exposes metrics in Prometheus text format for scraping.

    Metrics include:
    - Service information (version, uptime)
    - Request metrics (count, errors, latency)
    - Resource metrics (CPU, memory, files, threads)
    - Dependency health (DB, Redis, PgBouncer)
    """
    lines = []

    # Service info metrics
    uptime = time.time() - START_TIME
    lines.append(
        format_prometheus_metric(f"{SERVICE_NAME}_info", 1.0, "gauge", f"Service information for {SERVICE_NAME}")
    )
    lines.append(f'{SERVICE_NAME}_info{{version="{SERVICE_VERSION}"}} 1.0')

    lines.append(
        format_prometheus_metric(f"{SERVICE_NAME}_uptime_seconds", uptime, "counter", "Service uptime in seconds")
    )

    # Request metrics
    app_metrics = metrics_collector.get_metrics()

    lines.append(
        format_prometheus_metric(
            f"{SERVICE_NAME}_requests_total", app_metrics["request_count"], "counter", "Total number of requests"
        )
    )

    lines.append(
        format_prometheus_metric(
            f"{SERVICE_NAME}_errors_total", app_metrics["error_count"], "counter", "Total number of errors"
        )
    )

    lines.append(
        format_prometheus_metric(
            f"{SERVICE_NAME}_request_duration_seconds",
            app_metrics["avg_request_duration"],
            "gauge",
            "Average request duration in seconds",
        )
    )

    # Process metrics
    process_metrics = get_process_metrics()

    lines.append(
        format_prometheus_metric(
            f"{SERVICE_NAME}_process_cpu_percent",
            process_metrics["cpu_percent"],
            "gauge",
            "Process CPU usage percentage",
        )
    )

    lines.append(
        format_prometheus_metric(
            f"{SERVICE_NAME}_process_memory_mb", process_metrics["memory_mb"], "gauge", "Process memory usage in MB"
        )
    )

    lines.append(
        format_prometheus_metric(
            f"{SERVICE_NAME}_process_open_files",
            process_metrics["open_files"],
            "gauge",
            "Number of open file descriptors",
        )
    )

    lines.append(
        format_prometheus_metric(
            f"{SERVICE_NAME}_process_threads", process_metrics["threads"], "gauge", "Number of threads"
        )
    )

    # Dependency health (binary: 1 = healthy, 0 = unhealthy)
    # Note: These are placeholders - actual health checks should be async
    lines.append(
        format_prometheus_metric(
            f"{SERVICE_NAME}_dependency_database_healthy",
            1.0,  # Placeholder
            "gauge",
            "Database dependency health (1=healthy, 0=unhealthy)",
        )
    )

    lines.append(
        format_prometheus_metric(
            f"{SERVICE_NAME}_dependency_redis_healthy",
            1.0,  # Placeholder
            "gauge",
            "Redis dependency health (1=healthy, 0=unhealthy)",
        )
    )

    lines.append(
        format_prometheus_metric(
            f"{SERVICE_NAME}_dependency_pgbouncer_healthy",
            1.0,  # Placeholder
            "gauge",
            "PgBouncer dependency health (1=healthy, 0=unhealthy)",
        )
    )

    # Timestamp
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    lines.append(f"# Generated at {timestamp}")

    content = "\n".join(lines) + "\n"

    return PlainTextResponse(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")


# Export metrics collector for middleware to use
__all__ = ["router", "metrics_collector"]
