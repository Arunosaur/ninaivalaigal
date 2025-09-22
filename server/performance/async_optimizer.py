"""
Async Operation Optimization
Provides utilities for optimizing async operations and concurrent processing
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


class AsyncBatchProcessor:
    """
    Batch processor for optimizing multiple async operations.

    Features:
    - Automatic batching of similar operations
    - Configurable batch size and timeout
    - Error handling and retry logic
    - Performance monitoring
    """

    def __init__(
        self,
        batch_size: int = 10,
        batch_timeout: float = 0.1,  # 100ms
        max_concurrent: int = 50,
    ):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Performance tracking
        self.stats = {
            "batches_processed": 0,
            "operations_processed": 0,
            "total_time": 0,
            "errors": 0,
        }

    async def process_batch(
        self,
        operations: List[Callable],
        batch_processor: Optional[Callable] = None,
    ) -> List[Any]:
        """Process a batch of operations concurrently."""
        start_time = time.time()

        try:
            async with self.semaphore:
                if batch_processor:
                    # Use custom batch processor if provided
                    results = await batch_processor(operations)
                else:
                    # Default: run operations concurrently
                    tasks = [op() for op in operations]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                # Update statistics
                self.stats["batches_processed"] += 1
                self.stats["operations_processed"] += len(operations)
                self.stats["total_time"] += time.time() - start_time

                logger.debug(
                    "Batch processed",
                    batch_size=len(operations),
                    duration_ms=round((time.time() - start_time) * 1000, 2),
                )

                return results

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(
                "Batch processing failed", error=str(e), batch_size=len(operations)
            )
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics."""
        stats = self.stats.copy()

        if stats["batches_processed"] > 0:
            stats["avg_batch_time"] = stats["total_time"] / stats["batches_processed"]
            stats["avg_operations_per_batch"] = (
                stats["operations_processed"] / stats["batches_processed"]
            )

        return stats


class AsyncCache:
    """
    Async-aware caching with TTL and automatic cleanup.
    """

    def __init__(self, default_ttl: int = 300):
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl
        self._cleanup_task: Optional[asyncio.Task] = None
        self.start_cleanup_task()

    def start_cleanup_task(self):
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())

    async def _cleanup_expired(self):
        """Background task to clean up expired cache entries."""
        while True:
            try:
                current_time = time.time()
                expired_keys = [
                    key
                    for key, (_, expiry) in self.cache.items()
                    if current_time > expiry
                ]

                for key in expired_keys:
                    del self.cache[key]

                if expired_keys:
                    logger.debug("Cache cleanup", expired_keys=len(expired_keys))

                await asyncio.sleep(60)  # Cleanup every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("Cache cleanup error", error=str(e))
                await asyncio.sleep(60)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() <= expiry:
                return value
            else:
                del self.cache[key]
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        self.cache[key] = (value, expiry)

    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[int] = None,
    ) -> Any:
        """Get from cache or set using factory function."""
        value = await self.get(key)
        if value is not None:
            return value

        value = await factory()
        await self.set(key, value, ttl)
        return value

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()

    def stop_cleanup(self):
        """Stop the cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


class AsyncRateLimiter:
    """
    Token bucket rate limiter for async operations.
    """

    def __init__(self, rate: float, burst: int):
        self.rate = rate  # tokens per second
        self.burst = burst  # maximum tokens
        self.tokens = burst
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens from the bucket."""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Add tokens based on elapsed time
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    @asynccontextmanager
    async def limit(self, tokens: int = 1):
        """Context manager for rate limiting."""
        while not await self.acquire(tokens):
            await asyncio.sleep(0.01)  # Wait 10ms before retry

        try:
            yield
        finally:
            pass  # Tokens already consumed


class AsyncOperationOptimizer:
    """
    Main optimizer for async operations with comprehensive performance features.
    """

    def __init__(self):
        self.batch_processor = AsyncBatchProcessor()
        self.cache = AsyncCache()
        self.rate_limiters: Dict[str, AsyncRateLimiter] = {}

        # Performance metrics
        self.metrics = {
            "operations_optimized": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "rate_limited_operations": 0,
        }

    def get_rate_limiter(self, name: str, rate: float, burst: int) -> AsyncRateLimiter:
        """Get or create a rate limiter."""
        if name not in self.rate_limiters:
            self.rate_limiters[name] = AsyncRateLimiter(rate, burst)
        return self.rate_limiters[name]

    async def cached_operation(
        self,
        cache_key: str,
        operation: Callable,
        ttl: Optional[int] = None,
    ) -> Any:
        """Execute operation with caching."""
        cached_result = await self.cache.get(cache_key)

        if cached_result is not None:
            self.metrics["cache_hits"] += 1
            return cached_result

        self.metrics["cache_misses"] += 1
        result = await operation()
        await self.cache.set(cache_key, result, ttl)

        return result

    async def rate_limited_operation(
        self,
        limiter_name: str,
        operation: Callable,
        rate: float = 10.0,
        burst: int = 20,
        tokens: int = 1,
    ) -> Any:
        """Execute operation with rate limiting."""
        limiter = self.get_rate_limiter(limiter_name, rate, burst)

        async with limiter.limit(tokens):
            self.metrics["rate_limited_operations"] += 1
            return await operation()

    async def optimized_operation(
        self,
        operation: Callable,
        cache_key: Optional[str] = None,
        cache_ttl: Optional[int] = None,
        rate_limiter: Optional[str] = None,
        rate_limit_params: Optional[Dict] = None,
    ) -> Any:
        """
        Execute operation with full optimization (caching + rate limiting).
        """
        self.metrics["operations_optimized"] += 1

        # Wrap operation with rate limiting if specified
        if rate_limiter:
            params = rate_limit_params or {}
            operation = lambda: self.rate_limited_operation(
                rate_limiter, operation, **params
            )

        # Wrap with caching if specified
        if cache_key:
            return await self.cached_operation(cache_key, operation, cache_ttl)

        return await operation()

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        stats = {
            "optimizer_metrics": self.metrics,
            "batch_processor_stats": self.batch_processor.get_stats(),
            "cache_stats": {
                "total_entries": len(self.cache.cache),
                "cache_hit_rate": (
                    self.metrics["cache_hits"]
                    / max(1, self.metrics["cache_hits"] + self.metrics["cache_misses"])
                ),
            },
            "rate_limiters": {
                name: {
                    "current_tokens": limiter.tokens,
                    "rate": limiter.rate,
                    "burst": limiter.burst,
                }
                for name, limiter in self.rate_limiters.items()
            },
        }

        return stats

    def cleanup(self):
        """Clean up resources."""
        self.cache.stop_cleanup()
        self.cache.clear()
        self.rate_limiters.clear()


# Global optimizer instance
_async_optimizer: Optional[AsyncOperationOptimizer] = None


def get_async_optimizer() -> AsyncOperationOptimizer:
    """Get the global async optimizer instance."""
    global _async_optimizer

    if _async_optimizer is None:
        _async_optimizer = AsyncOperationOptimizer()

    return _async_optimizer


def cleanup_async_optimizer():
    """Clean up the global async optimizer."""
    global _async_optimizer

    if _async_optimizer:
        _async_optimizer.cleanup()
        _async_optimizer = None
