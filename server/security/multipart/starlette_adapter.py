# server/security/multipart/starlette_adapter.py
from __future__ import annotations

from collections.abc import Callable

from fastapi import HTTPException, status
from starlette.formparsers import MultiPartParser
from starlette.requests import Request

from server.security.multipart.strict_limits_hardened import (
    DEFAULT_MAX_BINARY_PART_BYTES,
    DEFAULT_MAX_PARTS_PER_REQUEST,
    DEFAULT_MAX_TEXT_PART_BYTES,
    detect_enhanced_magic_bytes,
    require_utf8_text,
)

REASON_ENGINE_ERROR = "engine_error"
REASON_POLICY_DENIED = "policy_denied"
REASON_MAGIC_MISMATCH = "magic_mismatch"
REASON_PART_TOO_LARGE = "part_too_large"
REASON_TOO_MANY_PARTS = "too_many_parts"
REASON_INVALID_ENCODING = "invalid_encoding"
REASON_ARCHIVE_BLOCKED = "archive_blocked"


def _emit_multipart_reject(reason: str) -> None:
    """Emit multipart rejection metrics with bounded reasons."""
    # Wire to metrics counter: multipart_reject_total{reason}
    # Bounded reasons: engine_error, policy_denied, magic_mismatch,
    # part_too_large, too_many_parts, invalid_encoding, archive_blocked
    try:
        from server.observability.metrics_label_guard import validate_reason_bucket

        validated_reason = validate_reason_bucket(reason)
        # TODO: Wire to actual metrics system
        # metrics.counter("multipart_reject_total", tags={"reason": validated_reason}).increment()
        pass
    except ImportError:
        pass


async def scan_with_starlette(
    request: Request,
    text_handler: Callable[[str, dict], None],
    binary_handler: Callable[[bytes, dict], None] | None = None,
    *,
    max_text_part_bytes: int = DEFAULT_MAX_TEXT_PART_BYTES,
    max_binary_part_bytes: int = DEFAULT_MAX_BINARY_PART_BYTES,
    max_parts_per_request: int = DEFAULT_MAX_PARTS_PER_REQUEST,
) -> None:
    try:
        parser = MultiPartParser(headers=request.headers, stream=request.stream())
    except Exception as e:
        _emit_multipart_reject(REASON_ENGINE_ERROR)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"invalid multipart: {e}"
        ) from e

    part_count = 0

    async for part in parser.parse():
        part_count += 1
        if part_count >= max_parts_per_request:
            _emit_multipart_reject(REASON_TOO_MANY_PARTS)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Too many parts in multipart request",
            )

        headers = dict(part.headers or {})
        ctype = (headers.get("content-type") or "").lower()
        cte = headers.get("content-transfer-encoding")

        is_textish = (
            ctype.startswith("text/")
            or ctype.startswith("application/json")
            or ctype.startswith("application/x-www-form-urlencoded")
        )
        cap = max_text_part_bytes if is_textish else max_binary_part_bytes

        # Collect part data with size limits
        try:
            head = b""
            total_size = 0
            async for chunk in part.stream():
                total_size += len(chunk)
                if total_size > cap:
                    _emit_multipart_reject(REASON_PART_TOO_LARGE)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="multipart part exceeds size limit",
                    )
                head += chunk
        except HTTPException:
            raise
        except Exception:
            _emit_multipart_reject(REASON_ENGINE_ERROR)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="multipart processing error",
            )

        # Security validations
        if cte:
            _emit_multipart_reject(REASON_INVALID_ENCODING)
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Content-Transfer-Encoding not allowed",
            )

        if is_textish:
            # UTF-8 validation for text parts
            utf8_result = require_utf8_text(head)
            if not utf8_result.get("valid"):
                _emit_multipart_reject(REASON_INVALID_ENCODING)
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Text parts must be valid UTF-8",
                )

            # Binary masquerade detection
            magic_result = detect_enhanced_magic_bytes(head)
            if magic_result.get("detected"):
                _emit_multipart_reject(REASON_MAGIC_MISMATCH)
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Binary content detected in text part",
                )

            # Archive blocking on text endpoints
            if binary_handler is None:  # Text-only endpoint
                archive_result = detect_enhanced_magic_bytes(head)
                if archive_result.get("detected") and archive_result.get("format") in [
                    "ZIP",
                    "RAR",
                    "7Z",
                    "TAR",
                ]:
                    _emit_multipart_reject(REASON_ARCHIVE_BLOCKED)
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail="Archive uploads not allowed on text endpoints",
                    )

            # Process text part
            text_content = head.decode("utf-8")
            await text_handler(text_content, headers)

        else:
            # Binary part processing
            if binary_handler is None:
                _emit_multipart_reject(REASON_POLICY_DENIED)
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Binary uploads not supported on this endpoint",
                )

            await binary_handler(head, headers)
