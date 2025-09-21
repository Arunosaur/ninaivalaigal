"""
Negative Cache for JWKS Unknown Kid

Implements negative caching for unknown kid values in JWKS rotation
to avoid thundering herds when many simultaneous requests hit an unknown kid.
"""

import asyncio
import time
from dataclasses import dataclass


@dataclass
class NegativeCacheEntry:
    """Negative cache entry for unknown kid."""
    kid: str
    cached_at: float
    ttl_seconds: int = 300  # 5 minutes default

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() > (self.cached_at + self.ttl_seconds)


class JWKSNegativeCache:
    """Negative cache for unknown kid values in JWKS rotation."""

    def __init__(self, default_ttl: int = 300, max_entries: int = 1000):
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        self._cache: dict[str, NegativeCacheEntry] = {}
        self._lock = asyncio.Lock()

    async def is_kid_unknown(self, kid: str) -> bool:
        """
        Check if kid is in negative cache (known to be unknown).
        
        Returns True if kid is cached as unknown and not expired.
        """
        async with self._lock:
            entry = self._cache.get(kid)

            if entry is None:
                return False

            if entry.is_expired:
                # Remove expired entry
                del self._cache[kid]
                return False

            return True

    async def cache_unknown_kid(self, kid: str, ttl: int | None = None):
        """
        Cache a kid as unknown for the specified TTL.
        
        Args:
            kid: The unknown kid to cache
            ttl: Time to live in seconds (uses default if None)
        """
        async with self._lock:
            # Evict expired entries if cache is full
            if len(self._cache) >= self.max_entries:
                await self._evict_expired()

            # If still full after eviction, remove oldest entry
            if len(self._cache) >= self.max_entries:
                oldest_kid = min(self._cache.keys(), key=lambda k: self._cache[k].cached_at)
                del self._cache[oldest_kid]

            # Add new entry
            entry = NegativeCacheEntry(
                kid=kid,
                cached_at=time.time(),
                ttl_seconds=ttl or self.default_ttl
            )
            self._cache[kid] = entry

    async def remove_kid(self, kid: str):
        """
        Remove a kid from negative cache.
        
        Used when a previously unknown kid becomes available.
        """
        async with self._lock:
            self._cache.pop(kid, None)

    async def clear_expired(self):
        """Clear all expired entries from cache."""
        async with self._lock:
            await self._evict_expired()

    async def _evict_expired(self):
        """Internal method to evict expired entries."""
        current_time = time.time()
        expired_kids = [
            kid for kid, entry in self._cache.items()
            if current_time > (entry.cached_at + entry.ttl_seconds)
        ]

        for kid in expired_kids:
            del self._cache[kid]

    async def get_cache_stats(self) -> dict[str, any]:
        """Get cache statistics."""
        async with self._lock:
            await self._evict_expired()  # Clean up first

            return {
                "total_entries": len(self._cache),
                "max_entries": self.max_entries,
                "default_ttl": self.default_ttl,
                "cached_kids": list(self._cache.keys()),
                "oldest_entry_age": (
                    time.time() - min((entry.cached_at for entry in self._cache.values()), default=time.time())
                    if self._cache else 0
                )
            }


# Enhanced JWKS Verifier with negative caching
class JWKSVerifierWithNegativeCache:
    """JWKS Verifier enhanced with negative caching for unknown kids."""

    def __init__(self, jwks_client, negative_cache_ttl: int = 300):
        self.jwks_client = jwks_client
        self.negative_cache = JWKSNegativeCache(default_ttl=negative_cache_ttl)
        self._refresh_lock = asyncio.Lock()

    async def verify_jwt_with_negative_cache(self, token: str, kid: str) -> dict[str, any]:
        """
        Verify JWT with negative caching for unknown kids.
        
        Returns verification result with caching information.
        """
        result = {
            "verified": False,
            "payload": None,
            "error": None,
            "cache_hit": False,
            "cache_action": None
        }

        # Check negative cache first
        if await self.negative_cache.is_kid_unknown(kid):
            result["cache_hit"] = True
            result["error"] = f"Kid {kid} is cached as unknown"
            return result

        try:
            # Attempt verification with existing keys
            key = self.jwks_client.get_signing_key(kid)
            # Verify JWT here (implementation depends on JWT library)
            result["verified"] = True
            result["payload"] = {"kid": kid, "verified": True}  # Placeholder

        except Exception:
            # Kid not found, check if we should refresh
            async with self._refresh_lock:
                # Double-check negative cache after acquiring lock
                if await self.negative_cache.is_kid_unknown(kid):
                    result["cache_hit"] = True
                    result["error"] = f"Kid {kid} is cached as unknown (double-check)"
                    return result

                try:
                    # Force refresh of JWKS
                    self.jwks_client.get_signing_key(kid, refresh=True)
                    # Try verification again after refresh
                    key = self.jwks_client.get_signing_key(kid)
                    result["verified"] = True
                    result["payload"] = {"kid": kid, "verified_after_refresh": True}

                except Exception as refresh_error:
                    # Still unknown after refresh, cache it
                    await self.negative_cache.cache_unknown_kid(kid)
                    result["cache_action"] = "cached_unknown"
                    result["error"] = f"Kid {kid} unknown after refresh: {refresh_error}"

        return result


def test_negative_cache():
    """Test JWKS negative cache functionality."""

    async def run_test():
        cache = JWKSNegativeCache(default_ttl=2, max_entries=3)  # Short TTL for testing

        # Test caching unknown kid
        await cache.cache_unknown_kid("unknown_kid_1")
        assert await cache.is_kid_unknown("unknown_kid_1") == True
        assert await cache.is_kid_unknown("unknown_kid_2") == False

        # Test TTL expiration
        await asyncio.sleep(2.1)  # Wait for TTL to expire
        assert await cache.is_kid_unknown("unknown_kid_1") == False

        # Test cache eviction
        await cache.cache_unknown_kid("kid_1")
        await cache.cache_unknown_kid("kid_2")
        await cache.cache_unknown_kid("kid_3")
        await cache.cache_unknown_kid("kid_4")  # Should evict oldest

        stats = await cache.get_cache_stats()
        assert stats["total_entries"] <= 3

        # Test manual removal
        await cache.cache_unknown_kid("test_kid")
        assert await cache.is_kid_unknown("test_kid") == True
        await cache.remove_kid("test_kid")
        assert await cache.is_kid_unknown("test_kid") == False

        return {
            "test_passed": True,
            "final_stats": stats
        }

    return asyncio.run(run_test())


if __name__ == "__main__":
    # Run test
    results = test_negative_cache()
    print("JWKS Negative Cache Test Results:")
    print(f"✅ Test passed: {results['test_passed']}")
    print(f"Final cache stats: {results['final_stats']}")
