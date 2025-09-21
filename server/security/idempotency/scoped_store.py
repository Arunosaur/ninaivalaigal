"""
Scoped Idempotency Store

Implements idempotency key scoping with path template and subject_user_id
to prevent cross-route collisions and enhance security isolation.
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class IdempotencyScope:
    """Scoping context for idempotency keys."""

    method: str
    path_template: str
    subject_user_id: str
    organization_id: str | None = None
    additional_context: dict[str, str] | None = None


class ScopedIdempotencyStore(Protocol):
    """Protocol for scoped idempotency key storage."""

    async def get_scoped(
        self, key: str, scope: IdempotencyScope
    ) -> dict[str, Any] | None:
        """Get stored response for scoped idempotency key."""
        ...

    async def set_scoped(
        self,
        key: str,
        scope: IdempotencyScope,
        response_data: dict[str, Any],
        ttl: int = 3600,
    ) -> None:
        """Store response data for scoped idempotency key."""
        ...

    async def exists_scoped(self, key: str, scope: IdempotencyScope) -> bool:
        """Check if scoped idempotency key exists."""
        ...


class IdempotencyKeyGenerator:
    """Enhanced idempotency key generator with scoping."""

    @staticmethod
    def generate_scoped_key(base_key: str, scope: IdempotencyScope) -> str:
        """
        Generate scoped idempotency key to prevent cross-route collisions.

        Format: {method}:{path_template}:{user_id}:{org_id}:{base_key_hash}
        """
        # Create scope components
        scope_parts = [
            scope.method.upper(),
            scope.path_template,
            scope.subject_user_id,
            scope.organization_id or "global",
        ]

        # Add additional context if provided
        if scope.additional_context:
            context_str = json.dumps(scope.additional_context, sort_keys=True)
            scope_parts.append(hashlib.sha256(context_str.encode()).hexdigest()[:8])

        # Hash the base key for consistent length
        base_key_hash = hashlib.sha256(base_key.encode()).hexdigest()[:16]
        scope_parts.append(base_key_hash)

        # Join with separator that won't appear in components
        scoped_key = ":".join(scope_parts)

        # Final hash to ensure consistent key length and prevent injection
        return hashlib.sha256(scoped_key.encode()).hexdigest()

    @staticmethod
    def extract_path_template(
        path: str, route_patterns: dict[str, str] | None = None
    ) -> str:
        """
        Extract path template from actual path for consistent scoping.

        Examples:
        /api/v1/users/123/memories -> /api/v1/users/{user_id}/memories
        /api/v1/orgs/456/teams/789 -> /api/v1/orgs/{org_id}/teams/{team_id}
        """
        if route_patterns:
            # Use provided route patterns for exact matching
            for pattern, template in route_patterns.items():
                if pattern in path:
                    return template

        # Fallback: simple ID replacement
        import re

        # Replace numeric IDs
        path_template = re.sub(r"/\d+", "/{id}", path)

        # Replace UUID patterns
        uuid_pattern = r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        path_template = re.sub(
            uuid_pattern, "/{uuid}", path_template, flags=re.IGNORECASE
        )

        # Replace common ID patterns
        path_template = re.sub(r"/[a-zA-Z0-9_-]{20,}", "/{long_id}", path_template)

        return path_template

    @staticmethod
    def create_scope_from_request(
        method: str,
        path: str,
        subject_user_id: str,
        organization_id: str | None = None,
        route_patterns: dict[str, str] | None = None,
        additional_context: dict[str, str] | None = None,
    ) -> IdempotencyScope:
        """Create idempotency scope from request context."""
        path_template = IdempotencyKeyGenerator.extract_path_template(
            path, route_patterns
        )

        return IdempotencyScope(
            method=method,
            path_template=path_template,
            subject_user_id=subject_user_id,
            organization_id=organization_id,
            additional_context=additional_context,
        )


class ScopedMemoryStore:
    """In-memory scoped idempotency store for development."""

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    async def get_scoped(
        self, key: str, scope: IdempotencyScope
    ) -> dict[str, Any] | None:
        scoped_key = IdempotencyKeyGenerator.generate_scoped_key(key, scope)
        return self._store.get(scoped_key)

    async def set_scoped(
        self,
        key: str,
        scope: IdempotencyScope,
        response_data: dict[str, Any],
        ttl: int = 3600,
    ) -> None:
        scoped_key = IdempotencyKeyGenerator.generate_scoped_key(key, scope)
        self._store[scoped_key] = {
            **response_data,
            "_scope": scope.__dict__,
            "_created_at": __import__("time").time(),
        }

    async def exists_scoped(self, key: str, scope: IdempotencyScope) -> bool:
        scoped_key = IdempotencyKeyGenerator.generate_scoped_key(key, scope)
        return scoped_key in self._store

    def get_stats(self) -> dict[str, Any]:
        """Get store statistics."""
        return {
            "total_keys": len(self._store),
            "scopes": list(
                set(
                    data.get("_scope", {}).get("path_template", "unknown")
                    for data in self._store.values()
                )
            ),
        }


class ScopedRedisStore:
    """Redis-backed scoped idempotency store."""

    def __init__(self, redis_client, key_prefix: str = "scoped_idempotency:"):
        self.redis = redis_client
        self.key_prefix = key_prefix

    async def get_scoped(
        self, key: str, scope: IdempotencyScope
    ) -> dict[str, Any] | None:
        try:
            scoped_key = IdempotencyKeyGenerator.generate_scoped_key(key, scope)
            full_key = f"{self.key_prefix}{scoped_key}"

            data = await self.redis.get(full_key)
            if data:
                return json.loads(data)
            return None

        except Exception:
            return None

    async def set_scoped(
        self,
        key: str,
        scope: IdempotencyScope,
        response_data: dict[str, Any],
        ttl: int = 3600,
    ) -> None:
        try:
            scoped_key = IdempotencyKeyGenerator.generate_scoped_key(key, scope)
            full_key = f"{self.key_prefix}{scoped_key}"

            # Add scope metadata
            enriched_data = {
                **response_data,
                "_scope": scope.__dict__,
                "_scoped_key": scoped_key,
            }

            serialized_data = json.dumps(enriched_data, default=str)
            await self.redis.setex(full_key, ttl, serialized_data)

        except Exception:
            pass  # Fail silently for idempotency

    async def exists_scoped(self, key: str, scope: IdempotencyScope) -> bool:
        try:
            scoped_key = IdempotencyKeyGenerator.generate_scoped_key(key, scope)
            full_key = f"{self.key_prefix}{scoped_key}"

            result = await self.redis.exists(full_key)
            return bool(result)

        except Exception:
            return False

    async def get_scope_stats(self, subject_user_id: str) -> dict[str, Any]:
        """Get statistics for user's idempotency usage."""
        try:
            pattern = f"{self.key_prefix}*:{subject_user_id}:*"
            keys = []

            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key.decode())

            return {
                "user_id": subject_user_id,
                "active_keys": len(keys),
                "sample_keys": keys[:5],  # First 5 for debugging
            }

        except Exception:
            return {"user_id": subject_user_id, "active_keys": 0, "error": True}


# Route pattern registry for common API patterns
DEFAULT_ROUTE_PATTERNS = {
    "/api/v1/users/": "/api/v1/users/{user_id}",
    "/api/v1/orgs/": "/api/v1/orgs/{org_id}",
    "/api/v1/teams/": "/api/v1/teams/{team_id}",
    "/api/v1/memories/": "/api/v1/memories/{memory_id}",
    "/api/v1/contexts/": "/api/v1/contexts/{context_id}",
}


def create_scoped_store(redis_client=None) -> ScopedIdempotencyStore:
    """Create appropriate scoped store based on available backend."""
    if redis_client:
        return ScopedRedisStore(redis_client)
    else:
        return ScopedMemoryStore()


# Test utilities
def test_key_scoping():
    """Test idempotency key scoping functionality."""

    # Test scope creation
    scope1 = IdempotencyScope(
        method="POST",
        path_template="/api/v1/users/{user_id}/memories",
        subject_user_id="user_123",
        organization_id="org_456",
    )

    scope2 = IdempotencyScope(
        method="POST",
        path_template="/api/v1/users/{user_id}/memories",
        subject_user_id="user_789",  # Different user
        organization_id="org_456",
    )

    # Test key generation
    base_key = "idempotency-key-123"

    key1 = IdempotencyKeyGenerator.generate_scoped_key(base_key, scope1)
    key2 = IdempotencyKeyGenerator.generate_scoped_key(base_key, scope2)

    # Keys should be different for different users
    assert key1 != key2, "Keys should differ for different users"

    # Same scope should generate same key
    key1_repeat = IdempotencyKeyGenerator.generate_scoped_key(base_key, scope1)
    assert key1 == key1_repeat, "Same scope should generate same key"

    return {
        "scope1_key": key1,
        "scope2_key": key2,
        "keys_different": key1 != key2,
        "deterministic": key1 == key1_repeat,
    }


def test_path_template_extraction():
    """Test path template extraction."""
    test_cases = [
        ("/api/v1/users/123/memories", "/api/v1/users/{id}/memories"),
        ("/api/v1/orgs/456/teams/789", "/api/v1/orgs/{id}/teams/{id}"),
        ("/api/v1/contexts/uuid-123-456", "/api/v1/contexts/{long_id}"),
        ("/static/path", "/static/path"),  # No IDs to replace
    ]

    results = []
    for path, expected in test_cases:
        template = IdempotencyKeyGenerator.extract_path_template(path)
        results.append(
            {
                "path": path,
                "template": template,
                "expected": expected,
                "matches": template == expected,
            }
        )

    return results
