"""
Enhanced Multipart Security with P0 Hardening Fixes

Implements critical security enhancements identified in external review:
- Stream-time per-part enforcement (abort early while streaming)
- Mach-O and Java class magic detection (blocks macOS executables)
- MP4/ISO-BMFF detection via ftyp within first 12 bytes (offset-aware)
- Archive blocking for text-only endpoints
- UTF-8 only policy for text parts
- Content-Transfer-Encoding guard (rejects base64/quoted-printable)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Enhanced magic byte signatures with P0 additions
ENHANCED_MAGIC_SIGNATURES = {
    # Executables (P0: Added Mach-O variants)
    b"MZ": "application/x-msdownload",  # PE executable
    b"\x7fELF": "application/x-executable",  # ELF executable
    b"\xca\xfe\xba\xbe": "application/java-vm",  # Java class (P0)
    b"\xcf\xfa\xed\xfe": "application/x-mach-binary",  # Mach-O 32-bit (P0)
    b"\xce\xfa\xed\xfe": "application/x-mach-binary",  # Mach-O 32-bit reverse (P0)
    b"\xfe\xed\xfa\xcf": "application/x-mach-binary",  # Mach-O 32-bit big-endian (P0)
    b"\xfe\xed\xfa\xce": "application/x-mach-binary",  # Mach-O 32-bit big-endian reverse (P0)
    b"\xcf\xfa\xed\xfe": "application/x-mach-binary",  # Mach-O 64-bit (P0)
    b"\xcf\xfa\xed\xfe": "application/x-mach-binary",  # Mach-O 64-bit reverse (P0)
    # Documents
    b"%PDF": "application/pdf",
    b"PK\x03\x04": "application/zip",  # ZIP/Office docs
    b"PK\x05\x06": "application/zip",  # Empty ZIP
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1": "application/msword",  # MS Office
    # Images
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"BM": "image/bmp",
    b"\x00\x00\x01\x00": "image/x-icon",
    # Audio/Video
    b"RIFF": "audio/wav",
    b"ID3": "audio/mpeg",
    b"\xff\xfb": "audio/mpeg",
    # MP4/ISO-BMFF handled separately with offset detection
    # Archives (P0: Enhanced for blocking)
    b"\x1f\x8b\x08": "application/gzip",
    b"7z\xbc\xaf\x27\x1c": "application/x-7z-compressed",
    b"Rar!\x1a\x07\x00": "application/x-rar-compressed",
}

# Archive types to block for text-only endpoints (P0)
ARCHIVE_TYPES = {
    "application/zip",
    "application/gzip",
    "application/x-7z-compressed",
    "application/x-rar-compressed",
}

# Executable types (P0: Enhanced with Mach-O and Java)
EXECUTABLE_TYPES = {
    "application/x-msdownload",
    "application/x-executable",
    "application/java-vm",
    "application/x-mach-binary",
}

# Default constants for adapter compatibility
DEFAULT_MAX_TEXT_PART_BYTES = 1 * 1024 * 1024  # 1MB for text
DEFAULT_MAX_BINARY_PART_BYTES = 10 * 1024 * 1024  # 10MB for binary
DEFAULT_MAX_PARTS_PER_REQUEST = 256  # P0: Part count DoS prevention


@dataclass
class HardenedPartLimitConfig:
    """Enhanced configuration with P0 hardening options."""

    max_part_bytes: int = 10 * 1024 * 1024  # 10MB default
    max_text_part_bytes: int = DEFAULT_MAX_TEXT_PART_BYTES
    max_binary_part_bytes: int = DEFAULT_MAX_BINARY_PART_BYTES
    max_parts_per_request: int = DEFAULT_MAX_PARTS_PER_REQUEST

    # Magic byte detection
    enforce_magic_byte_checks: bool = True
    block_executable_magic_bytes: bool = True
    block_archives_for_text: bool = True  # P0: Block archives on text endpoints

    # Text validation (P0)
    require_utf8_text: bool = True  # P0: UTF-8 only policy
    reject_content_transfer_encoding: bool = True  # P0: Block base64/quoted-printable

    # Detection thresholds
    printable_threshold: float = 0.30
    mp4_scan_bytes: int = 32  # P0: MP4 offset detection within first 32 bytes


@dataclass
class StreamLimitState:
    """State for stream-time per-part limit enforcement."""

    bytes_seen: int = 0
    limit_exceeded: bool = False
    part_number: int = 0


def detect_mp4_iso_bmff(payload: bytes, max_scan_bytes: int = 32) -> bool:
    """
    P0: Enhanced MP4/ISO-BMFF detection with offset awareness.

    MP4 magic sits at offset 4 (ftyp box), not byte 0. Scan first 32 bytes
    to catch various MP4 container formats.
    """
    if len(payload) < 12:
        return False

    scan_window = payload[:max_scan_bytes]

    # Look for 'ftyp' signature within scan window
    for i in range(len(scan_window) - 4):
        if scan_window[i : i + 4] == b"ftyp":
            return True

    return False


def detect_enhanced_magic_bytes(
    payload: bytes, max_check_bytes: int = 512
) -> dict[str, Any]:
    """
    P0: Enhanced magic byte detection with Mach-O, Java, and MP4 offset detection.
    """
    if not payload:
        return {
            "detected": False,
            "detected_type": None,
            "signature": None,
            "is_executable": False,
            "is_archive": False,
            "confidence": 0.0,
        }

    check_bytes = payload[:max_check_bytes]

    # Check standard magic byte signatures
    for signature, file_type in ENHANCED_MAGIC_SIGNATURES.items():
        if check_bytes.startswith(signature):
            return {
                "detected": True,
                "detected_type": file_type,
                "signature": signature,
                "is_executable": file_type in EXECUTABLE_TYPES,
                "is_archive": file_type in ARCHIVE_TYPES,
                "confidence": 0.95,
            }

    # P0: Special case for MP4/ISO-BMFF (offset detection)
    if detect_mp4_iso_bmff(check_bytes):
        return {
            "detected": True,
            "detected_type": "video/mp4",
            "signature": b"ftyp",  # Logical signature
            "is_executable": False,
            "is_archive": False,
            "confidence": 0.90,
        }

    # No magic bytes detected
    return {
        "detected": False,
        "detected_type": None,
        "signature": None,
        "is_executable": False,
        "is_archive": False,
        "confidence": 0.0,
    }


def require_utf8_text(content: bytes) -> dict[str, Any]:
    """
    P0: UTF-8 only policy for text parts.

    Explicitly reject non-UTF-8 text to prevent encoding-based bypasses.
    """
    result = {"valid": True, "encoding": "utf-8", "violations": []}

    # Check for UTF-16 BOM first (common bypass attempt)
    if content.startswith(b"\xff\xfe") or content.startswith(b"\xfe\xff"):
        result["valid"] = False
        result["violations"].append(
            {
                "type": "utf16_bom_detected",
                "message": "UTF-16 BOM detected in text part",
                "severity": "high",
            }
        )
        result["encoding"] = "utf-16"
        return result

    # Check for UTF-16LE without BOM (common case)
    if len(content) >= 2 and content[1:2] == b"\x00" and content[0:1] != b"\x00":
        result["valid"] = False
        result["violations"].append(
            {
                "type": "utf16_detected",
                "message": "UTF-16LE encoding detected in text part",
                "severity": "high",
            }
        )
        result["encoding"] = "utf-16le"
        return result

    try:
        # Attempt UTF-8 decode
        decoded = content.decode("utf-8")

    except UnicodeDecodeError as e:
        result["valid"] = False
        result["violations"].append(
            {
                "type": "invalid_utf8",
                "message": f"Invalid UTF-8 encoding: {e}",
                "severity": "high",
            }
        )
        result["encoding"] = "unknown"

    return result


def reject_content_transfer_encoding(cte_header: str | None) -> dict[str, Any]:
    """
    P0: Content-Transfer-Encoding guard.

    Reject base64/quoted-printable encoding for text parts to prevent
    bypass of content inspection.
    """
    result = {"valid": True, "violations": []}

    if not cte_header:
        return result

    cte_lower = cte_header.lower().strip()

    # Block problematic encodings
    blocked_encodings = {"base64", "quoted-printable", "7bit", "8bit"}

    if cte_lower in blocked_encodings:
        result["valid"] = False
        result["violations"].append(
            {
                "type": "blocked_content_transfer_encoding",
                "message": f"Content-Transfer-Encoding '{cte_header}' not allowed for text parts",
                "severity": "high",
                "encoding": cte_header,
            }
        )

    return result


def disallow_archives_for_text(
    magic_result: dict[str, Any], declared_content_type: str
) -> dict[str, Any]:
    """
    P0: Archive blocking for text-only endpoints.

    Reject ZIP/7z/RAR/GZIP when content-type suggests text endpoint.
    """
    result = {"valid": True, "violations": []}

    if not magic_result.get("detected") or not magic_result.get("is_archive"):
        return result

    # Check if declared as text type
    declared_main = declared_content_type.split("/")[0].lower()

    if declared_main == "text" or declared_content_type.lower() in [
        "application/json",
        "application/xml",
    ]:
        result["valid"] = False
        result["violations"].append(
            {
                "type": "archive_blocked_for_text",
                "message": f"Archive content ({magic_result['detected_type']}) not allowed for text endpoint",
                "severity": "high",
                "detected_type": magic_result["detected_type"],
                "declared_type": declared_content_type,
            }
        )

    return result


def enforce_part_limits_stream(
    stream_state: StreamLimitState, chunk_bytes: int, config: HardenedPartLimitConfig
) -> dict[str, Any]:
    """
    P0: Stream-time per-part limit enforcement.

    Abort early while streaming to prevent memory exhaustion.
    Call this for each chunk received during streaming.
    """
    result = {
        "valid": True,
        "should_abort": False,
        "bytes_seen": stream_state.bytes_seen,
        "violations": [],
    }

    # Update stream state
    stream_state.bytes_seen += chunk_bytes

    # Check if limit exceeded
    if stream_state.bytes_seen > config.max_part_bytes:
        stream_state.limit_exceeded = True
        result["valid"] = False
        result["should_abort"] = True
        result["violations"].append(
            {
                "type": "stream_part_limit_exceeded",
                "message": f"Part {stream_state.part_number} exceeded {config.max_part_bytes} bytes during streaming",
                "severity": "critical",
                "bytes_seen": stream_state.bytes_seen,
                "limit": config.max_part_bytes,
            }
        )

    result["bytes_seen"] = stream_state.bytes_seen
    return result


def enforce_part_limits_buffer(
    content: bytes,
    content_type: str,
    filename: str | None = None,
    config: HardenedPartLimitConfig | None = None,
    cte_header: str | None = None,
) -> dict[str, Any]:
    """
    P0: Enhanced buffer-time limit enforcement with hardening.

    Comprehensive validation after content is buffered.
    """
    if config is None:
        config = HardenedPartLimitConfig()

    result = {
        "valid": True,
        "size_bytes": len(content),
        "violations": [],
        "magic_result": None,
        "is_binary": False,
        "content_type": content_type,
        "filename": filename,
    }

    # Basic size check
    if len(content) > config.max_part_bytes:
        result["valid"] = False
        result["violations"].append(
            {
                "type": "buffer_size_exceeded",
                "message": f"Part size {len(content)} exceeds limit {config.max_part_bytes}",
                "severity": "critical",
            }
        )
        return result  # Early return on size violation

    # P0: Enhanced magic byte detection
    if config.enforce_magic_byte_checks:
        magic_result = detect_enhanced_magic_bytes(content, config.mp4_scan_bytes)
        result["magic_result"] = magic_result

        # P0: Block executables (including Mach-O and Java)
        if config.block_executable_magic_bytes and magic_result.get("is_executable"):
            result["valid"] = False
            result["violations"].append(
                {
                    "type": "executable_blocked",
                    "message": f"Executable content blocked: {magic_result['detected_type']}",
                    "severity": "critical",
                    "detected_type": magic_result["detected_type"],
                }
            )

        # P0: Block archives for text endpoints
        if config.block_archives_for_text:
            archive_check = disallow_archives_for_text(magic_result, content_type)
            if not archive_check["valid"]:
                result["valid"] = False
                result["violations"].extend(archive_check["violations"])

    # Determine if content is binary
    result["is_binary"] = _looks_binary_enhanced(content, config.printable_threshold)

    # P0: Text-specific validations (check content-type, not binary detection)
    if content_type.startswith("text/") or content_type in [
        "application/json",
        "application/xml",
    ]:
        # P0: UTF-8 validation
        if config.require_utf8_text:
            utf8_check = require_utf8_text(content)
            if not utf8_check["valid"]:
                result["valid"] = False
                result["violations"].extend(utf8_check["violations"])

        # P0: Content-Transfer-Encoding validation
        if config.reject_content_transfer_encoding and cte_header:
            cte_check = reject_content_transfer_encoding(cte_header)
            if not cte_check["valid"]:
                result["valid"] = False
                result["violations"].extend(cte_check["violations"])

    # Type-specific size limits
    if result["is_binary"]:
        if len(content) > config.max_binary_part_bytes:
            result["valid"] = False
            result["violations"].append(
                {
                    "type": "binary_size_exceeded",
                    "message": f"Binary part size {len(content)} exceeds limit {config.max_binary_part_bytes}",
                    "severity": "medium",
                }
            )
    else:
        if len(content) > config.max_text_part_bytes:
            result["valid"] = False
            result["violations"].append(
                {
                    "type": "text_size_exceeded",
                    "message": f"Text part size {len(content)} exceeds limit {config.max_text_part_bytes}",
                    "severity": "medium",
                }
            )

    return result


def _looks_binary_enhanced(payload: bytes, printable_threshold: float = 0.30) -> bool:
    """Enhanced binary detection with magic byte awareness."""
    if not payload:
        return False

    # Check for null bytes (strong binary indicator)
    if b"\x00" in payload:
        return True

    # Check enhanced magic bytes
    magic_result = detect_enhanced_magic_bytes(payload)
    if magic_result.get("detected"):
        return True

    # Check printable character ratio
    nonprint = sum((b < 9) or (13 < b < 32) for b in payload)
    ratio = nonprint / max(1, len(payload))
    return ratio > printable_threshold


def enforce_max_parts_per_request(
    part_count: int, config: HardenedPartLimitConfig
) -> dict[str, Any]:
    """
    P0: Part count DoS prevention.

    Simple counter to prevent attacks via thousands of tiny parts.
    """
    result = {"valid": True, "part_count": part_count, "violations": []}

    if part_count > config.max_parts_per_request:
        result["valid"] = False
        result["violations"].append(
            {
                "type": "too_many_parts",
                "message": f"Request has {part_count} parts, exceeds limit of {config.max_parts_per_request}",
                "severity": "high",
                "part_count": part_count,
                "limit": config.max_parts_per_request,
            }
        )

    return result


# Convenience functions for integration
def create_hardened_config(
    text_only_endpoint: bool = False, max_upload_size: int = 10 * 1024 * 1024
) -> HardenedPartLimitConfig:
    """Create hardened configuration for production use."""
    return HardenedPartLimitConfig(
        max_part_bytes=max_upload_size,
        max_text_part_bytes=min(1 * 1024 * 1024, max_upload_size),
        max_binary_part_bytes=max_upload_size,
        max_parts_per_request=256,
        enforce_magic_byte_checks=True,
        block_executable_magic_bytes=True,
        block_archives_for_text=text_only_endpoint,
        require_utf8_text=text_only_endpoint,
        reject_content_transfer_encoding=text_only_endpoint,
    )


def validate_multipart_headers(headers: dict[str, str]) -> dict[str, Any]:
    """Validate multipart headers for security issues."""
    result = {"valid": True, "violations": []}

    # Check Content-Transfer-Encoding
    cte = headers.get("content-transfer-encoding")
    if cte:
        cte_check = reject_content_transfer_encoding(cte)
        if not cte_check["valid"]:
            result["valid"] = False
            result["violations"].extend(cte_check["violations"])

    return result
