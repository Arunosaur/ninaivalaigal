"""
Middleware Resilience Utilities

SPEC-092: Middleware resilience framework for timeout handling, fallback mechanisms,
and circuit breakers.
"""

from lib.middleware.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerManager,
    CircuitState,
    circuit_breaker_middleware,
    get_breaker_manager,
)
from lib.middleware.circuit_breaker_middleware import CircuitBreakerMiddleware
from lib.middleware.health import MiddlewareHealthMonitor, get_middleware_health_monitor
from lib.middleware.redis_fallback import RedisFallback, get_redis_fallback
from lib.middleware.timeout_handler import (
    DEFAULT_MIDDLEWARE_TIMEOUT,
    DEFAULT_REDIS_TIMEOUT,
    DEFAULT_REQUEST_TIMEOUT,
    RequestTimeoutMiddleware,
    TimeoutError,
    safe_async_call,
    timeout_middleware_wrapper,
    with_timeout,
)

__all__ = [
    "RequestTimeoutMiddleware",
    "CircuitBreakerMiddleware",
    "RedisFallback",
    "get_redis_fallback",
    "CircuitBreaker",
    "CircuitBreakerManager",
    "get_breaker_manager",
    "CircuitBreakerError",
    "CircuitState",
    "circuit_breaker_middleware",
    "MiddlewareHealthMonitor",
    "get_middleware_health_monitor",
    "with_timeout",
    "safe_async_call",
    "timeout_middleware_wrapper",
    "TimeoutError",
    "DEFAULT_MIDDLEWARE_TIMEOUT",
    "DEFAULT_REDIS_TIMEOUT",
    "DEFAULT_REQUEST_TIMEOUT",
]
