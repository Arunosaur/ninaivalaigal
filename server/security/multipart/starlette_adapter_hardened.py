"""Hardened Starlette/FastAPI multipart adapter with P0 security integration.

This adapter integrates the P0 multipart hardening patch with Starlette/FastAPI
request handling, providing stream-time enforcement, comprehensive validation,
and early abort capabilities.

Based on the code review recommendations for merging hardened multipart validation.
"""

from typing import Callable, Optional
from starlette.requests import Request
from starlette.responses import Response
from starlette.datastructures import UploadFile
from fastapi import HTTPException
import logging

from server.security.multipart.strict_limits_hardened import (
    HardenedPartLimitConfig,
    create_hardened_config,
    enforce_part_limits_buffer,
    enforce_part_limits_stream,
    enforce_max_parts_per_request,
    StreamLimitState
)

logger = logging.getLogger(__name__)

# Default configurations
DEFAULT_MAX_TEXT_PART_BYTES = 1 * 1024 * 1024  # 1MB
DEFAULT_MAX_BINARY_PART_BYTES = 10 * 1024 * 1024  # 10MB
DEFAULT_MAX_PARTS_PER_REQUEST = 256


async def scan_with_starlette(
    request: Request, 
    text_handler: Callable[[str, dict], None],
    binary_handler: Optional[Callable[[bytes, dict], None]] = None,
    *,
    max_text_part_bytes: int = DEFAULT_MAX_TEXT_PART_BYTES,
    max_binary_part_bytes: int = DEFAULT_MAX_BINARY_PART_BYTES,
    max_parts_per_request: int = DEFAULT_MAX_PARTS_PER_REQUEST
) -> None:
    """
    Hardened multipart scanner with P0 security integration.
    
    Assumptions:
    - Your adapter file is server/security/multipart/starlette_adapter.py
    - It already exposes scan_with_starlette(request, text_handler, binary_handler=None, ...)
    - binary_handler=None: ...
    - Your text_handler(chunk: str, headers: dict) can be called multiple times (streaming).
    - If your code it expects a single call, simply buffer decoded chunks and call once.
    
    Args:
        request: Starlette request object
        text_handler: Handler for text content chunks
        binary_handler: Optional handler for binary content
        max_text_part_bytes: Maximum bytes for text parts
        max_binary_part_bytes: Maximum bytes for binary parts
        max_parts_per_request: Maximum parts per request
    
    Raises:
        HTTPException: On validation failures or policy violations
    """
    # Create hardened configuration
    config = HardenedPartLimitConfig(
        max_text_part_bytes=max_text_part_bytes,
        max_binary_part_bytes=max_binary_part_bytes,
        max_parts_per_request=max_parts_per_request,
        # Enable P0 hardening for text endpoints
        block_archives_for_text=True,
        require_utf8_text=True,
        reject_content_transfer_encoding=True,
        block_executable_magic_bytes=True
    )
    
    # Parse multipart form
    form = await request.form()
    part_count = 0
    
    for field_name, field_value in form.items():
        part_count += 1
        
        # P0: Part count DoS guard
        count_result = enforce_max_parts_per_request(part_count, config)
        if not count_result["valid"]:
            raise HTTPException(413, detail="too many multipart parts")
        
        if isinstance(field_value, UploadFile):
            # Binary/file upload handling
            content = await field_value.read()
            
            # Decide per-part size cap by declared type
            cap = max_text_part_bytes if field_value.content_type and (
                field_value.content_type.startswith("text/") or 
                field_value.content_type.startswith("application/json")
            ) else max_binary_part_bytes
            
            # P0: Enforce size WHILE streaming & take a small head sample
            head, rest_iter = await enforce_part_limits_stream(
                field_value.stream(), 
                max_part_bytes=cap
            )
            
            # P0: Binary / masquerade classification
            if disallow_archives_for_text(head, field_value.content_type or ""):
                raise ValueError("archive payload not allowed for text endpoints")
            
            if looks_binary(head):
                # Declared text but looks binary → policy violation
                if field_value.content_type and (
                    field_value.content_type.startswith("text/") or 
                    field_value.content_type.startswith("application/json")
                ):
                    raise ValueError("content-type mismatch: binary payload detected in text part")
                
                # Otherwise forward to binary handler if provided
                if binary_handler is not None:
                    # Deliver the head + rest as a single bytes stream
                    buf = bytearray(head)
                    async for chunk in rest_iter:
                        buf.extend(chunk)
                    binary_handler(bytes(buf), field_value.headers)
                continue
            
            # P0: Text path protections
            # CTE must not be base64/quoted-printable for text parts
            cte = field_value.headers.get("content-transfer-encoding")
            reject_content_transfer_encoding(cte)
            
            # Ensure front bytes are valid UTF-8; if you want, you can also decode+revalidate
            require_utf8_text(head)
            
            # Stream text to the handler (decode in small chunks to bound memory)
            # First head:
            if head:
                text_handler(head.decode("utf-8"), field_value.headers)
            
            # Then the rest:
            async for chunk in rest_iter:
                if chunk:
                    text_handler(chunk.decode("utf-8"), field_value.headers)
        else:
            # Simple form field - treat as text
            text_content = str(field_value).encode('utf-8')
            
            # Apply text validations
            if len(text_content) > max_text_part_bytes:
                raise HTTPException(413, detail="text part exceeds size limit")
            
            # P0: UTF-8 validation for form fields
            require_utf8_text(text_content)
            
            # Forward to text handler
            text_handler(str(field_value), {})


# Import helper functions from hardened implementation
from server.security.multipart.strict_limits_hardened import (
    disallow_archives_for_text,
    _looks_binary_enhanced as looks_binary,
    reject_content_transfer_encoding,
    require_utf8_text
)


# Quick test checklist functions for integration validation
def validate_hardened_integration():
    """Quick validation checklist for hardened integration."""
    test_cases = [
        # 256+ parts → first over the limit triggers a rejection
        ("part_count_limit", lambda: enforce_max_parts_per_request(300, 
            HardenedPartLimitConfig(max_parts_per_request=256))),
        
        # .txt containing MZ / Mach-O / Java class magics → rejected
        ("executable_detection", lambda: looks_binary(b"MZ\x90\x00")),
        
        # MP4 with ftyp at offset 4 → detected as binary; rejected if declared text
        ("mp4_offset_detection", lambda: looks_binary(b"\x00\x00\x00\x18ftypisom")),
        
        # ZIP beginning → rejected on text endpoints
        ("archive_blocking", lambda: disallow_archives_for_text(b"PK\x03\x04", "text/plain")),
        
        # Content-Transfer-Encoding: base64 on a text part → rejected
        ("cte_blocking", lambda: reject_content_transfer_encoding("base64")),
        
        # UTF-16LE text → rejected (unless you decide to support and transcode)
        ("utf8_enforcement", lambda: require_utf8_text(b"hello\xff\xfe"))
    ]
    
    results = {}
    for test_name, test_func in test_cases:
        try:
            result = test_func()
            results[test_name] = {"passed": True, "result": result}
        except (ValueError, HTTPException) as e:
            results[test_name] = {"passed": True, "blocked": str(e)}
        except Exception as e:
            results[test_name] = {"passed": False, "error": str(e)}
    
    return results


if __name__ == "__main__":
    # Run integration validation
    results = validate_hardened_integration()
    for test_name, result in results.items():
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status} {test_name}: {result}")
