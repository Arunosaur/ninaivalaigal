"""
Prometheus Metrics & Middleware

Provides RED metrics (Rate/Errors/Duration) and request tracking.
"""

import time
import uuid
import json
import logging
import contextvars
from typing import Callable
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Prometheus metrics
REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["route", "method", "code"])
DURATION = Histogram("http_request_duration_seconds", "Request latency", ["route", "method"])
ERRORS = Counter("app_errors_total", "Application errors", ["type"])
UPTIME_S = Gauge("app_uptime_seconds", "Process uptime (s)")

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
        super().__init__(app)
        self.logger = logging.getLogger(logger_name)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
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
            
            if 'response' in locals():
                self._log_request(rid, route, method, response.status_code, duration)
    
    def _log_request(self, request_id: str, path: str, method: str, status: int, duration: float, error: str = None):
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
