# server/security/multipart/starlette_adapter.py
from __future__ import annotations
from typing import Callable, Optional

from fastapi import HTTPException, status
from starlette.requests import Request
from starlette.formparsers import MultiPartParser

from server.security.multipart.strict_limits_hardened import (
    DEFAULT_MAX_TEXT_PART_BYTES,
    DEFAULT_MAX_BINARY_PART_BYTES,
    DEFAULT_MAX_PARTS_PER_REQUEST,
    HardenedPartLimitConfig,
    StreamLimitState,
    _looks_binary_enhanced as looks_binary,
    detect_enhanced_magic_bytes,
    require_utf8_text,
    reject_content_transfer_encoding,
    disallow_archives_for_text,
)

REASON_ENGINE_ERROR = "engine_error"
REASON_POLICY_DENIED = "policy_denied"
REASON_MAGIC_MISMATCH = "magic_mismatch"
REASON_PART_TOO_LARGE = "part_too_large"
REASON_TOO_MANY_PARTS = "too_many_parts"
REASON_INVALID_ENCODING = "invalid_encoding"
REASON_ARCHIVE_BLOCKED = "archive_blocked"

def _emit_multipart_reject(reason: str) -> None:
    return

async def scan_with_starlette(
    request: Request,
    text_handler: Callable[[str, dict], None],
    binary_handler: Optional[Callable[[bytes, dict], None]] = None,
    *,
    max_text_part_bytes: int = DEFAULT_MAX_TEXT_PART_BYTES,
    max_binary_part_bytes: int = DEFAULT_MAX_BINARY_PART_BYTES,
    max_parts_per_request: int = DEFAULT_MAX_PARTS_PER_REQUEST,
) -> None:
    try:
        parser = MultiPartParser(headers=request.headers, stream=request.stream())
    except Exception as e:
        _emit_multipart_reject(REASON_ENGINE_ERROR)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"invalid multipart: {e}") from e

    part_count = 0

    async for part in parser.parse():
        part_count += 1
        if part_count > max_parts_per_request:
            _emit_multipart_reject(REASON_TOO_MANY_PARTS)
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                detail="too many multipart parts")

        headers = dict(part.headers or {})
        ctype = (headers.get("content-type") or "").lower()
        cte   = headers.get("content-transfer-encoding")

        is_textish = ctype.startswith("text/") or ctype.startswith("application/json") or ctype.startswith("application/x-www-form-urlencoded")
        cap = max_text_part_bytes if is_textish else max_binary_part_bytes

        # Collect part data with size limits
        try:
            head = b""
            total_size = 0
            async for chunk in part.stream():
                total_size += len(chunk)
                if total_size > cap:
                    _emit_multipart_reject(REASON_PART_TOO_LARGE)
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                        detail="multipart part exceeds size limit")
                head += chunk
        except HTTPException:
            raise
        except Exception:
            _emit_multipart_reject(REASON_ENGINE_ERROR)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="failed to process multipart stream")

        # Check for archives on text endpoints
        magic_result = detect_enhanced_magic_bytes(head)
        if is_textish and magic_result.get("detected") and "zip" in magic_result.get("mime_type", "").lower():
            _emit_multipart_reject(REASON_ARCHIVE_BLOCKED)
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                                detail="archive payload not allowed for text endpoints")

        if looks_binary(head):
            if is_textish:
                _emit_multipart_reject(REASON_MAGIC_MISMATCH)
                raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                                    detail="content-type mismatch: binary payload in text part")
            if binary_handler is not None:
                binary_handler(head, headers)
            continue

        # Check Content-Transfer-Encoding
        cte_result = reject_content_transfer_encoding(cte)
        if not cte_result.get("valid", True):
            _emit_multipart_reject(REASON_INVALID_ENCODING)
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                                detail="unsupported Content-Transfer-Encoding for text part")

        # Check UTF-8 validity
        utf8_result = require_utf8_text(head)
        if not utf8_result.get("valid", True):
            _emit_multipart_reject(REASON_INVALID_ENCODING)
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                                detail="text parts must be UTF-8")

        if head:
            try:
                text_handler(head.decode("utf-8"), headers)
            except UnicodeDecodeError:
                _emit_multipart_reject(REASON_INVALID_ENCODING)
                raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                                    detail="text parts must be UTF-8")
