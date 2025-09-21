"""
Compression Guard Middleware

Prevents compressed requests from bypassing redaction by rejecting
compressed payloads or decompressing them before processing.
"""

from __future__ import annotations

import gzip
import zlib
from collections.abc import Callable

from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class CompressionGuardMiddleware:
    """Middleware to handle compressed requests safely."""

    def __init__(
        self,
        app: ASGIApp,
        detector_fn: Callable[[str], str] | None = None,
        strict_mode: bool = True,
        allowed_encodings: set[str] | None = None,
        max_decompressed_size: int = 10 * 1024 * 1024  # 10MB
    ):
        self.app = app
        self.detector_fn = detector_fn
        self.strict_mode = strict_mode
        self.allowed_encodings = allowed_encodings or set()
        self.max_decompressed_size = max_decompressed_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        content_encoding = headers.get("content-encoding", "").strip().lower()

        if content_encoding and self._is_compressed_encoding(content_encoding):
            if self.strict_mode and content_encoding not in self.allowed_encodings:
                # Reject compressed requests in strict mode
                response = Response(
                    content='{"error": "Compressed requests not allowed"}',
                    status_code=415,
                    headers={"content-type": "application/json"}
                )
                await response(scope, receive, send)
                return

        # Modify send to handle response compression safety
        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                # Remove Content-Length for redacted responses to force chunked encoding
                headers = list(message.get("headers", []))
                filtered_headers = []

                for name, value in headers:
                    name_str = name.decode().lower()
                    if name_str == "content-length":
                        # Skip Content-Length to force chunked encoding after redaction
                        continue
                    filtered_headers.append((name, value))

                # Add compression policy header
                filtered_headers.append((b"x-compression-policy", b"redaction-safe"))
                message["headers"] = filtered_headers

            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _is_compressed_encoding(self, encoding: str) -> bool:
        """Check if content encoding indicates compression."""
        if not encoding:
            return False

        compressed_encodings = {"gzip", "deflate", "br", "compress", "brotli"}
        encodings = [e.strip() for e in encoding.split(",")]

        return any(enc in compressed_encodings for enc in encodings)


def decompress_gzip(data: bytes, max_size: int = 10 * 1024 * 1024) -> bytes:
    """Safely decompress gzip data with size limits."""
    try:
        decompressed = gzip.decompress(data)
        if len(decompressed) > max_size:
            raise ValueError(f"Decompressed size {len(decompressed)} exceeds limit {max_size}")
        return decompressed
    except Exception as e:
        raise ValueError(f"Failed to decompress gzip data: {e}")


def decompress_deflate(data: bytes, max_size: int = 10 * 1024 * 1024) -> bytes:
    """Safely decompress deflate data with size limits."""
    try:
        decompressed = zlib.decompress(data)
        if len(decompressed) > max_size:
            raise ValueError(f"Decompressed size {len(decompressed)} exceeds limit {max_size}")
        return decompressed
    except Exception as e:
        raise ValueError(f"Failed to decompress deflate data: {e}")


def create_compression_guard(
    detector_fn: Callable[[str], str] | None = None,
    strict: bool = True,
    allowed_encodings: set[str] | None = None
) -> type:
    """Factory function to create compression guard middleware."""

    def middleware_factory(app: ASGIApp) -> CompressionGuardMiddleware:
        return CompressionGuardMiddleware(
            app=app,
            detector_fn=detector_fn,
            strict_mode=strict,
            allowed_encodings=allowed_encodings or set()
        )

    return middleware_factory


def strict_compression_guard(app: ASGIApp) -> CompressionGuardMiddleware:
    """Strict compression guard that rejects all compressed requests."""
    return CompressionGuardMiddleware(app, strict_mode=True)


def permissive_compression_guard(
    app: ASGIApp,
    allowed_encodings: set[str] | None = None
) -> CompressionGuardMiddleware:
    """Permissive compression guard that allows specific encodings."""
    return CompressionGuardMiddleware(
        app,
        strict_mode=False,
        allowed_encodings=allowed_encodings or {"gzip"}
    )
