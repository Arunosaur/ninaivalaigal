"""
Redis Hardening for Idempotency Store

Handles Redis outages gracefully with structured warnings, fallback behavior,
and rate-limit protection to prevent duplicate key abuse.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum


class RedisHealthStatus(Enum):
    """Redis connection health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class RedisOutageEvent:
    """Redis outage event for structured logging."""
    timestamp: float
    status: RedisHealthStatus
    error_message: str
    operation: str
    fallback_used: bool
    duration_ms: Optional[float] = None


class HardenedRedisStore:
    """Redis store with graceful outage handling and fallback behavior."""
    
    def __init__(
        self,
        redis_client,
        fallback_store=None,
        health_check_interval: int = 30,
        max_retry_attempts: int = 3,
        circuit_breaker_threshold: int = 5,
        key_prefix: str = "idempotency:"
    ):
        self.redis = redis_client
        self.fallback_store = fallback_store or {}  # In-memory fallback
        self.key_prefix = key_prefix
        
        # Health monitoring
        self.health_status = RedisHealthStatus.HEALTHY
        self.health_check_interval = health_check_interval
        self.last_health_check = 0
        
        # Circuit breaker
        self.failure_count = 0
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_open_until = 0
        
        # Retry configuration
        self.max_retry_attempts = max_retry_attempts
        
        # Logging
        self.logger = logging.getLogger("redis.hardening")
        
        # Metrics
        self.metrics = {
            "operations_total": 0,
            "failures_total": 0,
            "fallback_used_total": 0,
            "circuit_breaker_trips": 0,
            "outage_events": []
        }
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get with graceful Redis outage handling."""
        return await self._execute_with_fallback(
            operation="get",
            redis_operation=lambda: self._redis_get(key),
            fallback_operation=lambda: self._fallback_get(key),
            key=key
        )
    
    async def set(self, key: str, response_data: Dict[str, Any], ttl: int = 3600) -> None:
        """Set with graceful Redis outage handling."""
        await self._execute_with_fallback(
            operation="set",
            redis_operation=lambda: self._redis_set(key, response_data, ttl),
            fallback_operation=lambda: self._fallback_set(key, response_data, ttl),
            key=key
        )
    
    async def exists(self, key: str) -> bool:
        """Check existence with graceful Redis outage handling."""
        result = await self._execute_with_fallback(
            operation="exists",
            redis_operation=lambda: self._redis_exists(key),
            fallback_operation=lambda: self._fallback_exists(key),
            key=key
        )
        return bool(result)
    
    async def _execute_with_fallback(
        self,
        operation: str,
        redis_operation: Callable,
        fallback_operation: Callable,
        key: str
    ) -> Any:
        """Execute operation with Redis fallback handling."""
        self.metrics["operations_total"] += 1
        start_time = time.time()
        
        # Check circuit breaker
        if self._is_circuit_open():
            self.logger.warning(f"Circuit breaker open, using fallback for {operation}")
            self.metrics["fallback_used_total"] += 1
            return await fallback_operation()
        
        # Check Redis health periodically
        await self._check_redis_health()
        
        # Try Redis operation with retries
        for attempt in range(self.max_retry_attempts):
            try:
                result = await redis_operation()
                
                # Reset failure count on success
                if self.failure_count > 0:
                    self.logger.info(f"Redis recovered after {self.failure_count} failures")
                    self.failure_count = 0
                    self.health_status = RedisHealthStatus.HEALTHY
                
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.metrics["failures_total"] += 1
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Log structured outage event
                outage_event = RedisOutageEvent(
                    timestamp=time.time(),
                    status=RedisHealthStatus.DEGRADED if attempt < self.max_retry_attempts - 1 else RedisHealthStatus.UNAVAILABLE,
                    error_message=str(e),
                    operation=operation,
                    fallback_used=attempt == self.max_retry_attempts - 1,
                    duration_ms=duration_ms
                )
                
                self._log_outage_event(outage_event)
                
                if attempt < self.max_retry_attempts - 1:
                    # Exponential backoff
                    await asyncio.sleep(0.1 * (2 ** attempt))
                else:
                    # Final attempt failed, use fallback
                    self._trigger_circuit_breaker()
                    self.metrics["fallback_used_total"] += 1
                    return await fallback_operation()
        
        # Should not reach here
        return await fallback_operation()
    
    async def _redis_get(self, key: str) -> Optional[Dict[str, Any]]:
        """Redis get operation."""
        full_key = f"{self.key_prefix}{key}"
        data = await self.redis.get(full_key)
        
        if data:
            import json
            return json.loads(data)
        return None
    
    async def _redis_set(self, key: str, response_data: Dict[str, Any], ttl: int) -> None:
        """Redis set operation."""
        full_key = f"{self.key_prefix}{key}"
        import json
        serialized_data = json.dumps(response_data, default=str)
        await self.redis.setex(full_key, ttl, serialized_data)
    
    async def _redis_exists(self, key: str) -> bool:
        """Redis exists operation."""
        full_key = f"{self.key_prefix}{key}"
        result = await self.redis.exists(full_key)
        return bool(result)
    
    async def _fallback_get(self, key: str) -> Optional[Dict[str, Any]]:
        """Fallback get operation using in-memory store."""
        return self.fallback_store.get(key)
    
    async def _fallback_set(self, key: str, response_data: Dict[str, Any], ttl: int) -> None:
        """Fallback set operation using in-memory store."""
        self.fallback_store[key] = {
            **response_data,
            "_fallback_created_at": time.time(),
            "_fallback_ttl": ttl
        }
    
    async def _fallback_exists(self, key: str) -> bool:
        """Fallback exists operation using in-memory store."""
        return key in self.fallback_store
    
    async def _check_redis_health(self) -> None:
        """Periodic Redis health check."""
        current_time = time.time()
        
        if current_time - self.last_health_check < self.health_check_interval:
            return
        
        self.last_health_check = current_time
        
        try:
            # Simple ping to check Redis health
            await self.redis.ping()
            
            if self.health_status != RedisHealthStatus.HEALTHY:
                self.logger.info("Redis health check passed, status restored to healthy")
                self.health_status = RedisHealthStatus.HEALTHY
                
        except Exception as e:
            if self.health_status == RedisHealthStatus.HEALTHY:
                self.logger.warning(f"Redis health check failed: {e}")
                self.health_status = RedisHealthStatus.DEGRADED
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.circuit_open_until > time.time():
            return True
        
        # Reset circuit breaker if timeout expired
        if self.circuit_open_until > 0:
            self.logger.info("Circuit breaker timeout expired, attempting Redis operations")
            self.circuit_open_until = 0
        
        return False
    
    def _trigger_circuit_breaker(self) -> None:
        """Trigger circuit breaker after too many failures."""
        if self.failure_count >= self.circuit_breaker_threshold:
            self.circuit_open_until = time.time() + 60  # 1 minute circuit breaker
            self.metrics["circuit_breaker_trips"] += 1
            
            self.logger.error(
                f"Circuit breaker triggered after {self.failure_count} failures, "
                f"Redis operations suspended for 60 seconds"
            )
            
            self.health_status = RedisHealthStatus.UNAVAILABLE
    
    def _log_outage_event(self, event: RedisOutageEvent) -> None:
        """Log structured outage event."""
        self.metrics["outage_events"].append(event)
        
        # Keep only last 100 events
        if len(self.metrics["outage_events"]) > 100:
            self.metrics["outage_events"] = self.metrics["outage_events"][-100:]
        
        # Structured logging for monitoring systems
        log_data = {
            "event_type": "redis_outage",
            "timestamp": event.timestamp,
            "status": event.status.value,
            "operation": event.operation,
            "error": event.error_message,
            "fallback_used": event.fallback_used,
            "duration_ms": event.duration_ms,
            "failure_count": self.failure_count,
            "circuit_breaker_active": self._is_circuit_open()
        }
        
        if event.status == RedisHealthStatus.UNAVAILABLE:
            self.logger.error(f"Redis unavailable: {log_data}")
        else:
            self.logger.warning(f"Redis degraded: {log_data}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current Redis health status."""
        return {
            "status": self.health_status.value,
            "failure_count": self.failure_count,
            "circuit_breaker_active": self._is_circuit_open(),
            "circuit_open_until": self.circuit_open_until,
            "last_health_check": self.last_health_check,
            "metrics": self.metrics.copy()
        }
    
    async def force_health_check(self) -> Dict[str, Any]:
        """Force immediate health check."""
        self.last_health_check = 0  # Reset to force check
        await self._check_redis_health()
        return self.get_health_status()


class RateLimitedRedisStore(HardenedRedisStore):
    """Redis store with rate limiting to prevent abuse."""
    
    def __init__(self, *args, rate_limit_per_minute: int = 1000, **kwargs):
        super().__init__(*args, **kwargs)
        self.rate_limit_per_minute = rate_limit_per_minute
        self.request_timestamps = []
    
    async def _check_rate_limit(self, operation: str) -> None:
        """Check rate limit before operation."""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        cutoff_time = current_time - 60
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > cutoff_time]
        
        # Check if rate limit exceeded
        if len(self.request_timestamps) >= self.rate_limit_per_minute:
            self.logger.warning(
                f"Rate limit exceeded for {operation}: "
                f"{len(self.request_timestamps)} requests in last minute"
            )
            raise Exception(f"Rate limit exceeded: {self.rate_limit_per_minute} requests/minute")
        
        # Add current request
        self.request_timestamps.append(current_time)
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get with rate limiting."""
        await self._check_rate_limit("get")
        return await super().get(key)
    
    async def set(self, key: str, response_data: Dict[str, Any], ttl: int = 3600) -> None:
        """Set with rate limiting."""
        await self._check_rate_limit("set")
        await super().set(key, response_data, ttl)


def create_hardened_redis_store(
    redis_url: str,
    enable_rate_limiting: bool = True,
    rate_limit_per_minute: int = 1000,
    **kwargs
) -> HardenedRedisStore:
    """Create hardened Redis store with outage handling."""
    try:
        import redis.asyncio as redis
        redis_client = redis.from_url(redis_url)
        
        if enable_rate_limiting:
            return RateLimitedRedisStore(
                redis_client,
                rate_limit_per_minute=rate_limit_per_minute,
                **kwargs
            )
        else:
            return HardenedRedisStore(redis_client, **kwargs)
            
    except ImportError:
        raise ImportError("redis package required for HardenedRedisStore")


# Monitoring utilities
async def monitor_redis_health(store: HardenedRedisStore, interval: int = 60) -> None:
    """Background task to monitor Redis health."""
    while True:
        try:
            health_status = await store.force_health_check()
            
            if health_status["status"] != "healthy":
                logging.getLogger("redis.monitor").warning(
                    f"Redis health check: {health_status}"
                )
            
            await asyncio.sleep(interval)
            
        except Exception as e:
            logging.getLogger("redis.monitor").error(f"Health monitoring error: {e}")
            await asyncio.sleep(interval)


def get_redis_metrics(store: HardenedRedisStore) -> Dict[str, Any]:
    """Get Redis store metrics for Grafana."""
    health_status = store.get_health_status()
    
    return {
        "redis_operations_total": health_status["metrics"]["operations_total"],
        "redis_failures_total": health_status["metrics"]["failures_total"],
        "redis_fallback_used_total": health_status["metrics"]["fallback_used_total"],
        "redis_circuit_breaker_trips_total": health_status["metrics"]["circuit_breaker_trips"],
        "redis_health_status": 1 if health_status["status"] == "healthy" else 0,
        "redis_failure_count": health_status["failure_count"],
        "redis_circuit_breaker_active": 1 if health_status["circuit_breaker_active"] else 0
    }
