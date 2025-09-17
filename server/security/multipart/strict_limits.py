from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Enhanced magic byte signatures for comprehensive detection
MAGIC_BYTE_SIGNATURES = {
    # Executables
    b"MZ": "application/x-msdownload",  # PE executable
    b"\x7fELF": "application/x-executable",  # ELF executable
    b"\xca\xfe\xba\xbe": "application/java-vm",  # Java class
    
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
    b"\x00\x00\x00\x18ftypmp4": "video/mp4",
    b"\x00\x00\x00 ftypM4A": "audio/mp4",
    
    # Archives
    b"\x1f\x8b\x08": "application/gzip",
    b"7z\xbc\xaf\x27\x1c": "application/x-7z-compressed",
    b"Rar!\x1a\x07\x00": "application/x-rar-compressed",
}

@dataclass
class PartLimitConfig:
    """Configuration for multipart per-part limits."""
    max_part_bytes: int = 10 * 1024 * 1024  # 10MB default
    max_text_part_bytes: int = 1 * 1024 * 1024  # 1MB for text
    max_binary_part_bytes: int = 10 * 1024 * 1024  # 10MB for binary
    enforce_magic_byte_checks: bool = True
    block_executable_magic_bytes: bool = True
    printable_threshold: float = 0.30

@dataclass
class MagicByteResult:
    """Result of magic byte detection."""
    detected: bool
    detected_type: Optional[str]
    signature: Optional[bytes]
    is_executable: bool
    confidence: float

def detect_magic_bytes(payload: bytes, max_check_bytes: int = 512) -> MagicByteResult:
    """
    Enhanced magic byte detection with executable identification.
    
    Args:
        payload: Content bytes to check
        max_check_bytes: Maximum bytes to check from start of payload
    
    Returns:
        MagicByteResult with detection details
    """
    if not payload:
        return MagicByteResult(
            detected=False,
            detected_type=None,
            signature=None,
            is_executable=False,
            confidence=0.0
        )
    
    check_bytes = payload[:max_check_bytes]
    
    # Check for exact magic byte matches
    for signature, file_type in MAGIC_BYTE_SIGNATURES.items():
        if check_bytes.startswith(signature):
            is_executable = file_type in [
                "application/x-msdownload",
                "application/x-executable", 
                "application/java-vm"
            ]
            
            return MagicByteResult(
                detected=True,
                detected_type=file_type,
                signature=signature,
                is_executable=is_executable,
                confidence=0.95
            )
    
    # No magic bytes detected
    return MagicByteResult(
        detected=False,
        detected_type=None,
        signature=None,
        is_executable=False,
        confidence=0.0
    )

def looks_binary(payload: bytes, *, printable_threshold: float = 0.30) -> bool:
    """
    Enhanced binary detection with magic byte awareness.
    
    Args:
        payload: Content bytes to check
        printable_threshold: Threshold for printable character ratio
    
    Returns:
        True if payload appears to be binary content
    """
    if not payload:
        return False
    
    # Check for null bytes (strong binary indicator)
    if b"\x00" in payload:
        return True
    
    # Check magic bytes
    magic_result = detect_magic_bytes(payload)
    if magic_result.detected:
        return True
    
    # Check printable character ratio
    nonprint = sum((b < 9) or (13 < b < 32) for b in payload)
    ratio = nonprint / max(1, len(payload))
    return ratio > printable_threshold

# Import hardened implementation functions
from server.security.multipart.strict_limits_hardened import (
    HardenedPartLimitConfig,
    enforce_part_limits_stream,
    looks_binary as hardened_looks_binary,
    disallow_archives_for_text,
    reject_content_transfer_encoding,
    require_utf8_text,
    DEFAULT_MAX_TEXT_PART_BYTES,
    DEFAULT_MAX_BINARY_PART_BYTES,
    DEFAULT_MAX_PARTS_PER_REQUEST,
)

# Re-export for compatibility
__all__ = [
    'enforce_part_limits_stream',
    'looks_binary', 
    'disallow_archives_for_text',
    'reject_content_transfer_encoding',
    'require_utf8_text',
    'DEFAULT_MAX_TEXT_PART_BYTES',
    'DEFAULT_MAX_BINARY_PART_BYTES', 
    'DEFAULT_MAX_PARTS_PER_REQUEST',
]

def enforce_part_limits(
    content: bytes, 
    content_type: str,
    filename: Optional[str] = None,
    config: Optional[PartLimitConfig] = None
) -> Dict[str, Any]:
    """
    Enhanced per-part limit enforcement with magic byte checks.
    
    Args:
        content: Part content bytes
        content_type: Declared content type
        filename: Optional filename
        config: Limit configuration
    
    Returns:
        Validation result dictionary
    
    Raises:
        ValueError: If part exceeds limits or violates policies
    """
    if config is None:
        config = PartLimitConfig()
    
    result = {
        "valid": True,
        "size_bytes": len(content),
        "violations": [],
        "magic_byte_result": None,
        "is_binary": False,
        "content_type": content_type,
        "filename": filename
    }
    
    # Basic size check
    if len(content) > config.max_part_bytes:
        result["valid"] = False
        result["violations"].append({
            "type": "size_exceeded",
            "message": f"Part size {len(content)} exceeds limit {config.max_part_bytes}",
            "severity": "high"
        })
        raise ValueError(f"multipart part exceeds per-part limit: {len(content)} > {config.max_part_bytes}")
    
    # Magic byte detection
    if config.enforce_magic_byte_checks:
        magic_result = detect_magic_bytes(content)
        result["magic_byte_result"] = magic_result
        
        # Block executable magic bytes
        if config.block_executable_magic_bytes and magic_result.is_executable:
            result["valid"] = False
            result["violations"].append({
                "type": "executable_magic_bytes",
                "message": f"Executable file detected: {magic_result.detected_type}",
                "severity": "critical",
                "signature": magic_result.signature.hex() if magic_result.signature else None
            })
            raise ValueError(f"Executable content blocked: {magic_result.detected_type}")
        
        # Check for content type mismatch with magic bytes
        if magic_result.detected and magic_result.detected_type:
            declared_main = content_type.split('/')[0].lower()
            detected_main = magic_result.detected_type.split('/')[0].lower()
            
            # Text content should not have binary magic bytes
            if declared_main == 'text' and detected_main in ['image', 'audio', 'video', 'application']:
                result["violations"].append({
                    "type": "content_type_magic_mismatch",
                    "message": f"Text content-type but binary magic bytes detected: {magic_result.detected_type}",
                    "severity": "high",
                    "declared_type": content_type,
                    "detected_type": magic_result.detected_type
                })
                logger.warning(
                    "Content-type mismatch detected",
                    extra={
                        "declared_type": content_type,
                        "detected_type": magic_result.detected_type,
                        "file_name": filename,  # Use file_name instead of filename to avoid LogRecord conflict
                        "signature": magic_result.signature.hex() if magic_result.signature else None
                    }
                )
    
    # Binary detection
    result["is_binary"] = looks_binary(content, printable_threshold=config.printable_threshold)
    
    # Type-specific size limits
    if result["is_binary"] or (result["magic_byte_result"] and result["magic_byte_result"].detected):
        if len(content) > config.max_binary_part_bytes:
            result["valid"] = False
            result["violations"].append({
                "type": "binary_size_exceeded",
                "message": f"Binary part size {len(content)} exceeds limit {config.max_binary_part_bytes}",
                "severity": "medium"
            })
            raise ValueError(f"Binary part exceeds size limit: {len(content)} > {config.max_binary_part_bytes}")
    else:
        # Text content
        if len(content) > config.max_text_part_bytes:
            result["valid"] = False
            result["violations"].append({
                "type": "text_size_exceeded",
                "message": f"Text part size {len(content)} exceeds limit {config.max_text_part_bytes}",
                "severity": "medium"
            })
            raise ValueError(f"Text part exceeds size limit: {len(content)} > {config.max_text_part_bytes}")
    
    return result
