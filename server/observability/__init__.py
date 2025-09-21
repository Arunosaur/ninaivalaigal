"""
Observability & Telemetry Module

Provides health checks, metrics, structured logging, and optional tracing
for the ninaivalaigal API server.
"""

from .health import router as health_router
from .metrics import MetricsMiddleware
from .metrics import router as metrics_router

__all__ = [
    'health_router',
    'metrics_router',
    'MetricsMiddleware'
]
