"""
Redis-backed Idempotency Store

Provides distributed idempotency key storage with TTL, set-if-absent,
status tracking, and multi-instance consistency support.
"""

import json
import asyncio
from typing import Optional, Dict, Any
try:
    import redis.asyncio as redis
except ImportError:
    redis = None


class RedisKeyStore:
    """Redis-backed idempotency store for multi-instance deployments."""
    
    def __init__(self, redis_client, key_prefix: str = "idempotency:"):
        if redis is None:
            raise ImportError("redis package required for RedisKeyStore")
        
        self.redis = redis_client
        self.key_prefix = key_prefix
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get stored response for idempotency key."""
        try:
            full_key = f"{self.key_prefix}{key}"
            data = await self.redis.get(full_key)
            
            if data:
                return json.loads(data)
            return None
        
        except Exception:
            # Fallback: treat as cache miss
            return None
    
    async def set(self, key: str, response_data: Dict[str, Any], ttl: int = 3600) -> None:
        """Store response data for idempotency key with TTL."""
        try:
            full_key = f"{self.key_prefix}{key}"
            serialized_data = json.dumps(response_data, default=str)
            
            await self.redis.setex(full_key, ttl, serialized_data)
        
        except Exception:
            # Fail silently - idempotency is best-effort
            pass
    
    async def exists(self, key: str) -> bool:
        """Check if idempotency key exists."""
        try:
            full_key = f"{self.key_prefix}{key}"
            result = await self.redis.exists(full_key)
            return bool(result)
        
        except Exception:
            return False
    
    async def set_if_absent(self, key: str, response_data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set key only if it doesn't exist. Returns True if set, False if already exists."""
        try:
            full_key = f"{self.key_prefix}{key}"
            serialized_data = json.dumps(response_data, default=str)
            
            # Use SET with NX (only if not exists) and EX (expiry)
            result = await self.redis.set(full_key, serialized_data, nx=True, ex=ttl)
            return bool(result)
        
        except Exception:
            return False
    
    async def mark_processing(self, key: str, ttl: int = 300) -> bool:
        """Mark key as being processed to prevent concurrent processing."""
        try:
            processing_key = f"{self.key_prefix}processing:{key}"
            result = await self.redis.set(processing_key, "processing", nx=True, ex=ttl)
            return bool(result)
        
        except Exception:
            return False
    
    async def unmark_processing(self, key: str) -> None:
        """Remove processing marker."""
        try:
            processing_key = f"{self.key_prefix}processing:{key}"
            await self.redis.delete(processing_key)
        
        except Exception:
            pass
    
    async def is_processing(self, key: str) -> bool:
        """Check if key is currently being processed."""
        try:
            processing_key = f"{self.key_prefix}processing:{key}"
            result = await self.redis.exists(processing_key)
            return bool(result)
        
        except Exception:
            return False
    
    async def cleanup_expired(self) -> int:
        """Clean up expired keys (Redis handles this automatically, but useful for monitoring)."""
        # Redis automatically handles TTL cleanup, but we can scan for monitoring
        try:
            pattern = f"{self.key_prefix}*"
            keys = []
            
            async for key in self.redis.scan_iter(match=pattern):
                ttl = await self.redis.ttl(key)
                if ttl == -2:  # Key doesn't exist
                    keys.append(key)
            
            return len(keys)
        
        except Exception:
            return 0


def create_redis_store(redis_url: str, **kwargs) -> RedisKeyStore:
    """Create Redis store from URL."""
    if redis is None:
        raise ImportError("redis package required for RedisKeyStore")
    
    redis_client = redis.from_url(redis_url, **kwargs)
    return RedisKeyStore(redis_client)


async def test_redis_connectivity(redis_url: str) -> bool:
    """Test Redis connectivity."""
    try:
        if redis is None:
            return False
        
        client = redis.from_url(redis_url)
        await client.ping()
        await client.close()
        return True
    
    except Exception:
        return False
