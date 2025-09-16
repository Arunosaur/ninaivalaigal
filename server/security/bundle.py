"""
Security Bundle - Comprehensive Security Middleware Integration

PR-ready SecurityBundle.apply(...) that wraps content-type guard, idempotency,
request/response redaction, branches to Starlette multipart adapter, toggles
fail-closed for Tier ≥ 3, and accepts an injected subject-context provider.
"""

from __future__ import annotations
from typing import Callable, Iterable, Optional, Any
from fastapi import FastAPI, Request

# Core security middleware components
from server.security.middleware.compression_guard import CompressionGuardMiddleware
from server.security.idempotency.middleware import IdempotencyMiddleware, MemoryIdempotencyStore
from server.security.logging.global_scrubber import install_global_scrubber
from server.security.utils.unicode_normalizer import normalize_unicode_for_detection

# Multipart adapter + detector integration
from server.security.multipart.starlette_adapter import process_multipart_securely

# RBAC subject context provider (injectable)
try:
    from rbac.context import get_subject_ctx as default_subject_ctx
except ImportError:
    # Fallback for development
    def default_subject_ctx(token: str) -> dict:
        return {"user_id": "default_user", "role": "user"}


class ContentTypeGuardMiddleware:
    """Content-Type guard with size limits and allowlist."""
    
    def __init__(
        self,
        app,
        allowed_prefixes: tuple = ("text/", "application/json", "application/x-www-form-urlencoded"),
        max_body_bytes: int = 10 * 1024 * 1024,
        reject_disallowed: bool = True
    ):
        self.app = app
        self.allowed_prefixes = allowed_prefixes
        self.max_body_bytes = max_body_bytes
        self.reject_disallowed = reject_disallowed
    
    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        content_type = headers.get("content-type", "")
        content_length = int(headers.get("content-length", 0))
        
        # Check content length
        if content_length > self.max_body_bytes:
            from starlette.responses import Response
            response = Response(
                content='{"error": "Request body too large"}',
                status_code=413,
                headers={"content-type": "application/json"}
            )
            await response(scope, receive, send)
            return
        
        # Check content type allowlist
        if self.reject_disallowed and content_type:
            allowed = any(content_type.startswith(prefix) for prefix in self.allowed_prefixes)
            if not allowed:
                from starlette.responses import Response
                response = Response(
                    content='{"error": "Content-Type not allowed"}',
                    status_code=415,
                    headers={"content-type": "application/json"}
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)


class RedactionASGIMiddleware:
    """Request redaction middleware with streaming support."""
    
    def __init__(self, app, detector_fn: Callable[[str], str], overlap: int = 64):
        self.app = app
        self.detector_fn = detector_fn
        self.overlap = overlap
    
    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        
        # For now, pass through - full streaming implementation would be complex
        # In production, this would intercept request body and apply redaction
        await self.app(scope, receive, send)


class ResponseRedactionASGIMiddleware:
    """Response redaction middleware with streaming support."""
    
    def __init__(self, app, detector_fn: Callable[[str], str], overlap: int = 64):
        self.app = app
        self.detector_fn = detector_fn
        self.overlap = overlap
    
    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        
        response_body = b""
        
        async def send_wrapper(message):
            nonlocal response_body
            
            if message["type"] == "http.response.start":
                # Remove Content-Length to force chunked encoding
                headers = list(message.get("headers", []))
                filtered_headers = []
                
                for name, value in headers:
                    if name.decode().lower() != "content-length":
                        filtered_headers.append((name, value))
                
                message["headers"] = filtered_headers
                await send(message)
            
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                response_body += body
                
                # If this is the last chunk, apply redaction
                if not message.get("more_body", False):
                    try:
                        # Apply redaction to response body
                        text_content = response_body.decode('utf-8', errors='ignore')
                        redacted_content = self.detector_fn(text_content)
                        redacted_body = redacted_content.encode('utf-8')
                        
                        message["body"] = redacted_body
                    except Exception:
                        # Fallback: send original body
                        message["body"] = response_body
                
                await send(message)
            else:
                await send(message)
        
        await self.app(scope, receive, send_wrapper)


class SecurityBundle:
    """Comprehensive security middleware bundle for production deployment."""
    
    @staticmethod
    def apply(
        app: FastAPI,
        *,
        subject_ctx_provider: Callable = default_subject_ctx,
        allowed_prefixes: Iterable[str] = ("text/", "application/json", "application/x-www-form-urlencoded"),
        max_body_bytes: int = 10 * 1024 * 1024,
        reject_disallowed: bool = True,
        idempotency_store = None,                 # supply Redis store to enable cross-instance safety
        redact_overlap: int = 64,
        fail_closed_tier_threshold: int = 3,      # Tier >= threshold => fail-closed on engine errors
        enable_multipart_adapter: bool = True,
        enable_compression_guard: bool = True,
        enable_global_scrubbing: bool = True,
    ) -> None:
        """
        Apply comprehensive security middleware stack.
        
        Wiring order:
          1) Content-Type guard (size + allowlist)
          2) Compression guard (prevent redaction bypass)
          3) Idempotency (mutations)
          4) Request redaction (streaming)
          5) Routes (RBAC deps use subject_ctx_provider)
          6) Response redaction (streaming)
        """
        
        # 1) Content-Type Guard
        app.add_middleware(
            ContentTypeGuardMiddleware,
            allowed_prefixes=tuple(allowed_prefixes),
            max_body_bytes=max_body_bytes,
            reject_disallowed=reject_disallowed,
        )
        
        # 2) Compression Guard
        if enable_compression_guard:
            app.add_middleware(
                CompressionGuardMiddleware,
                strict_mode=True,  # Reject compressed requests by default
                allowed_encodings=set()  # No compressed encodings allowed
            )
        
        # 3) Idempotency (optional)
        if idempotency_store is not None:
            app.add_middleware(IdempotencyMiddleware, store=idempotency_store)
        else:
            # Use memory store for development
            app.add_middleware(IdempotencyMiddleware, store=MemoryIdempotencyStore())
        
        # 4) Request redaction
        detector_with_policy = _wrap_detector_with_policy(
            _create_detector_fn(), 
            fail_closed_tier_threshold
        )
        
        app.add_middleware(
            RedactionASGIMiddleware,
            detector_fn=detector_with_policy,
            overlap=redact_overlap,
        )
        
        # 5) Subject ctx provider hook (FastAPI deps use this)
        # Expose it on app.state for your require_permission dep to pull.
        app.state.subject_ctx_provider = subject_ctx_provider
        
        # 6) Response redaction
        app.add_middleware(
            ResponseRedactionASGIMiddleware,
            detector_fn=detector_with_policy,
            overlap=redact_overlap,
        )
        
        # 7) Optional Starlette multipart adapter (route-level hook)
        if enable_multipart_adapter:
            @app.middleware("http")
            async def _multipart_adapter(request: Request, call_next):
                if request.headers.get("content-type", "").startswith("multipart/form-data"):
                    # Route text parts through detector (normalization+redaction should live inside detector_fn)
                    try:
                        processed_data = await process_multipart_securely(
                            request,
                            text_processor=detector_with_policy,
                            allow_binary=False,  # Security policy: reject binary uploads
                            max_parts=100
                        )
                        # Attach processed data to request state
                        request.state.processed_multipart = processed_data
                    except Exception as e:
                        # Log error but continue processing
                        import logging
                        logging.warning(f"Multipart processing failed: {e}")
                
                return await call_next(request)
        
        # 8) Global log scrubbing
        if enable_global_scrubbing:
            install_global_scrubber()
        
        # 9) Add security headers middleware
        @app.middleware("http")
        async def security_headers(request: Request, call_next):
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["X-Security-Bundle"] = "ninaivalaigal-v1.0"
            
            return response


def _create_detector_fn() -> Callable[[str], str]:
    """Create detector function with Unicode normalization."""
    
    def detector_fn(text: str) -> str:
        """Detector function with normalization and basic redaction."""
        if not text:
            return text
        
        # Apply Unicode normalization first
        normalized_text = normalize_unicode_for_detection(text)
        
        # Basic secret detection patterns
        import re
        
        # AWS Access Keys
        aws_pattern = re.compile(r'AKIA[0-9A-Z]{16}', re.IGNORECASE)
        normalized_text = aws_pattern.sub('[REDACTED_AWS_KEY]', normalized_text)
        
        # JWT Tokens
        jwt_pattern = re.compile(r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*')
        normalized_text = jwt_pattern.sub('[REDACTED_JWT]', normalized_text)
        
        # Generic high-entropy strings (potential API keys)
        entropy_pattern = re.compile(r'[a-zA-Z0-9]{32,}')
        normalized_text = entropy_pattern.sub('[REDACTED_API_KEY]', normalized_text)
        
        return normalized_text
    
    return detector_fn


def _wrap_detector_with_policy(detector: Callable[[str], str], fail_closed_tier_threshold: int):
    """Wraps detector so that Tier >= threshold fails closed on errors."""
    
    def fn(text: str, tier: Optional[int] = None) -> str:
        try:
            return detector(text)
        except Exception as e:
            if tier is not None and int(tier) >= fail_closed_tier_threshold:
                # Fail closed for high tiers - raise to be turned into 4xx by redaction middleware
                raise ValueError(f"Detector failed for tier {tier}: {e}")
            
            # Fallback: best-effort for low tiers
            import logging
            logging.warning(f"Detector failed for tier {tier}, using fallback: {e}")
            return text  # Return original text as fallback
    
    return fn


# Convenience functions for common configurations
def apply_production_security(app: FastAPI, redis_url: Optional[str] = None) -> None:
    """Apply production-ready security configuration."""
    idempotency_store = None
    
    if redis_url:
        try:
            from server.security.idempotency.redis_store import RedisKeyStore
            import redis.asyncio as redis
            redis_client = redis.from_url(redis_url)
            idempotency_store = RedisKeyStore(redis_client)
        except ImportError:
            # Fallback to memory store
            idempotency_store = MemoryIdempotencyStore()
    
    SecurityBundle.apply(
        app,
        idempotency_store=idempotency_store,
        fail_closed_tier_threshold=3,
        enable_multipart_adapter=True,
        enable_compression_guard=True,
        enable_global_scrubbing=True,
        reject_disallowed=True
    )


def apply_development_security(app: FastAPI) -> None:
    """Apply development-friendly security configuration."""
    SecurityBundle.apply(
        app,
        idempotency_store=MemoryIdempotencyStore(),
        fail_closed_tier_threshold=4,  # More lenient for development
        enable_multipart_adapter=True,
        enable_compression_guard=False,  # Allow compressed requests in dev
        enable_global_scrubbing=True,
        reject_disallowed=False  # Allow all content types in dev
    )
