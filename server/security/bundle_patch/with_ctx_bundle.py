"""
Security Bundle with Explicit Subject Context Provider

Enhanced SecurityBundle.apply() with explicit subject_ctx_provider injection
maintaining same middleware chain order with fail-closed tier logic.
"""

from __future__ import annotations

from collections.abc import Iterable

from fastapi import FastAPI, Request

from server.security.idempotency.middleware import IdempotencyMiddleware
from server.security.logging.global_scrubber import install_global_scrubber
from server.security.middleware.compression_guard import CompressionGuardMiddleware
from server.security.middleware.content_type_guard import ContentTypeGuardMiddleware
from server.security.middleware.redaction_middleware import RedactionASGIMiddleware
from server.security.middleware.response_redaction import (
    ResponseRedactionASGIMiddleware,
)
from server.security.multipart.starlette_adapter import MultipartStarletteAdapter
from server.security.rbac.context_provider import (
    SubjectContextProvider,
    install_subject_ctx_provider,
)
from server.security.redaction.detector_glue import detector_fn


def apply_security_bundle_with_ctx(
    app: FastAPI,
    *,
    subject_ctx_provider: SubjectContextProvider,
    allowed_prefixes: Iterable[str] = (
        "text/",
        "application/json",
        "application/x-www-form-urlencoded",
    ),
    max_body_bytes: int = 10 * 1024 * 1024,
    reject_disallowed: bool = True,
    enable_compression_guard: bool = True,
    idempotency_store=None,
    redact_overlap: int = 64,
    fail_closed_tier_threshold: int = 3,
    enable_multipart_adapter: bool = True,
    enable_global_scrubbing: bool = True,
) -> None:
    """
    Apply security bundle with explicit subject context provider.

    Same middleware chain as SecurityBundle.apply() but with explicit
    subject_ctx_provider injection for deterministic RBAC context.

    Args:
        app: FastAPI application
        subject_ctx_provider: Explicit subject context provider function
        **kwargs: Same configuration options as SecurityBundle.apply()
    """

    # 1) Content-Type guard middleware
    app.add_middleware(
        ContentTypeGuardMiddleware,
        allowed_prefixes=tuple(allowed_prefixes),
        max_body_bytes=max_body_bytes,
        reject_disallowed=reject_disallowed,
    )

    # 2) Compression guard middleware
    if enable_compression_guard:
        app.add_middleware(CompressionGuardMiddleware)

    # 3) Idempotency middleware
    if idempotency_store is not None:
        app.add_middleware(IdempotencyMiddleware, store=idempotency_store)

    # 4) Request redaction middleware with tier-aware fail-closed logic
    def tier_aware_detector(text: str, tier: int | None = None) -> str:
        """Detector function with fail-closed tier enforcement."""
        try:
            return detector_fn(text)
        except Exception:
            if tier is not None and int(tier) >= fail_closed_tier_threshold:
                raise  # Fail closed for sensitive tiers
            return text  # Return original text for lower tiers

    app.add_middleware(
        RedactionASGIMiddleware, detector_fn=tier_aware_detector, overlap=redact_overlap
    )

    # 5) Install subject context provider (explicit injection point)
    install_subject_ctx_provider(app, subject_ctx_provider)

    # 6) Response redaction middleware
    app.add_middleware(
        ResponseRedactionASGIMiddleware,
        detector_fn=tier_aware_detector,
        overlap=redact_overlap,
    )

    # 7) Multipart adapter middleware
    if enable_multipart_adapter:
        multipart_adapter = MultipartStarletteAdapter(
            text_handler=lambda text, headers: detector_fn(text), binary_handler=None
        )
        app.add_middleware(type(multipart_adapter), adapter=multipart_adapter)

    # 8) Global log scrubbing
    if enable_global_scrubbing:
        install_global_scrubber()

    # 9) Security headers middleware
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Security-Bundle"] = "ninaivalaigal-with-ctx-v1.0"

        return response
