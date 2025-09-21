"""
Idempotency Middleware

Provides idempotency protection for mutating HTTP endpoints to prevent
replay attacks and duplicate operations.
"""

import hashlib
import json
from typing import Any, Protocol

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class IdempotencyStore(Protocol):
    """Protocol for idempotency key storage backends."""

    async def get(self, key: str) -> dict[str, Any] | None:
        """Get stored response for idempotency key."""
        ...

    async def set(self, key: str, response_data: dict[str, Any], ttl: int = 3600) -> None:
        """Store response data for idempotency key."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if idempotency key exists."""
        ...


class MemoryIdempotencyStore:
    """In-memory idempotency store for development."""

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    async def get(self, key: str) -> dict[str, Any] | None:
        return self._store.get(key)

    async def set(self, key: str, response_data: dict[str, Any], ttl: int = 3600) -> None:
        self._store[key] = response_data

    async def exists(self, key: str) -> bool:
        return key in self._store


class IdempotencyMiddleware:
    """Middleware to handle idempotency for mutating operations."""

    def __init__(
        self,
        app: ASGIApp,
        store: IdempotencyStore,
        header_name: str = "Idempotency-Key",
        ttl: int = 3600,
        methods: set | None = None
    ):
        self.app = app
        self.store = store
        self.header_name = header_name
        self.ttl = ttl
        self.methods = methods or {"POST", "PUT", "PATCH", "DELETE"}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "").upper()
        if method not in self.methods:
            await self.app(scope, receive, send)
            return

        # Extract idempotency key from headers
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        idempotency_key = headers.get(self.header_name.lower())

        if not idempotency_key:
            # No idempotency key provided, proceed normally
            await self.app(scope, receive, send)
            return

        # Generate storage key
        storage_key = self._generate_storage_key(scope, idempotency_key)

        # Check if we have a cached response
        cached_response = await self.store.get(storage_key)
        if cached_response:
            # Return cached response
            await self._send_cached_response(cached_response, send)
            return

        # Capture response for caching
        response_data = {"status": 200, "headers": [], "body": b""}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_data["status"] = message["status"]
                response_data["headers"] = list(message.get("headers", []))
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                response_data["body"] += body

                # If this is the last chunk, cache the response
                if not message.get("more_body", False):
                    await self.store.set(storage_key, response_data, self.ttl)

            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _generate_storage_key(self, scope: Scope, idempotency_key: str) -> str:
        """Generate storage key from scope and idempotency key."""
        path = scope.get("path", "")
        method = scope.get("method", "")

        # Create a hash of the request context
        context = f"{method}:{path}:{idempotency_key}"
        return hashlib.sha256(context.encode()).hexdigest()

    async def _send_cached_response(self, response_data: dict[str, Any], send: Send) -> None:
        """Send cached response."""
        # Add idempotency header
        headers = list(response_data.get("headers", []))
        headers.append((b"x-idempotency-replay", b"true"))

        await send({
            "type": "http.response.start",
            "status": response_data.get("status", 200),
            "headers": headers
        })

        await send({
            "type": "http.response.body",
            "body": response_data.get("body", b"")
        })


def create_idempotency_middleware(
    store: IdempotencyStore | None = None,
    header_name: str = "Idempotency-Key",
    ttl: int = 3600
) -> type:
    """Factory function to create idempotency middleware."""

    def middleware_factory(app: ASGIApp) -> IdempotencyMiddleware:
        return IdempotencyMiddleware(
            app=app,
            store=store or MemoryIdempotencyStore(),
            header_name=header_name,
            ttl=ttl
        )

    return middleware_factory


def memory_idempotency_middleware(app: ASGIApp) -> IdempotencyMiddleware:
    """Create idempotency middleware with memory store."""
    return IdempotencyMiddleware(app, MemoryIdempotencyStore())


class IdempotencyKeyGenerator:
    """Utility to generate idempotency keys."""

    @staticmethod
    def generate_key(request_data: Any = None) -> str:
        """Generate idempotency key from request data."""
        if request_data:
            if isinstance(request_data, dict):
                data_str = json.dumps(request_data, sort_keys=True)
            else:
                data_str = str(request_data)
            return hashlib.sha256(data_str.encode()).hexdigest()
        else:
            import uuid
            return str(uuid.uuid4())

    @staticmethod
    def generate_from_content(content: str) -> str:
        """Generate idempotency key from content."""
        return hashlib.sha256(content.encode()).hexdigest()[:32]
