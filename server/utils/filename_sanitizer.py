"""Filename normalization and sanitization utilities for secure file handling."""

import re
import unicodedata
from pathlib import Path


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename for secure storage and processing.
    
    Args:
        filename: Original filename to sanitize
        max_length: Maximum allowed filename length
        
    Returns:
        Sanitized filename safe for filesystem operations
    """
    if not filename:
        return "unnamed_file"

    # Normalize Unicode to NFC form
    filename = unicodedata.normalize('NFC', filename)

    # Remove or replace dangerous characters
    # Keep alphanumeric, dots, hyphens, underscores
    filename = re.sub(r'[^\w\-_\.]', '_', filename)

    # Remove multiple consecutive dots (path traversal prevention)
    filename = re.sub(r'\.{2,}', '.', filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Handle empty result after stripping or all spaces/underscores
    if not filename or filename.replace('_', '').strip() == '':
        return "unnamed_file"

    # Prevent reserved names (Windows)
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
        'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4',
        'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }

    name_part = Path(filename).stem.upper()
    if name_part in reserved_names:
        filename = f"file_{filename}"

    # Truncate if too long, preserving extension
    if len(filename) > max_length:
        path = Path(filename)
        stem = path.stem
        suffix = path.suffix

        # Reserve space for extension
        max_stem_length = max_length - len(suffix)
        if max_stem_length > 0:
            filename = stem[:max_stem_length] + suffix
        else:
            filename = stem[:max_length]

    # Ensure we have a valid filename
    if not filename or filename in ['.', '..']:
        filename = "unnamed_file"

    return filename


def normalize_content_disposition_filename(content_disposition: str | None) -> str | None:
    """
    Extract and normalize filename from Content-Disposition header.
    
    Args:
        content_disposition: Content-Disposition header value
        
    Returns:
        Normalized filename or None if not found/invalid
    """
    if not content_disposition:
        return None

    # RFC 6266 filename extraction
    # Handle both filename and filename* (RFC 5987 encoded)

    # Try filename* first (encoded)
    filename_star_match = re.search(r"filename\*=([^;]+)", content_disposition)
    if filename_star_match:
        encoded_filename = filename_star_match.group(1)
        # Basic RFC 5987 decoding (charset'lang'value)
        if "'" in encoded_filename:
            parts = encoded_filename.split("'", 2)
            if len(parts) == 3:
                charset, lang, value = parts
                try:
                    # URL decode and charset decode
                    import urllib.parse
                    decoded = urllib.parse.unquote(value, encoding=charset or 'utf-8')
                    return sanitize_filename(decoded)
                except (UnicodeDecodeError, LookupError):
                    pass

    # Try regular filename
    filename_match = re.search(r'filename="([^"]*)"', content_disposition)
    if not filename_match:
        filename_match = re.search(r'filename=([^;]+)', content_disposition)

    if filename_match:
        filename = filename_match.group(1).strip('"')
        return sanitize_filename(filename)

    return None


def is_archive_extension(filename: str) -> bool:
    """
    Check if filename has an archive extension.
    
    Args:
        filename: Filename to check
        
    Returns:
        True if filename has archive extension
    """
    if not filename:
        return False

    archive_extensions = {
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tar.gz',
        '.tar.bz2', '.tar.xz', '.tgz', '.tbz2', '.txz', '.jar', '.war',
        '.ear', '.apk', '.ipa', '.deb', '.rpm', '.dmg', '.iso'
    }

    filename_lower = filename.lower()
    return any(filename_lower.endswith(ext) for ext in archive_extensions)


def validate_filename_safety(filename: str, allow_archives: bool = False) -> dict:
    """
    Validate filename for security issues.
    
    Args:
        filename: Filename to validate
        allow_archives: Whether to allow archive files
        
    Returns:
        Validation result with safety status and issues
    """
    result = {
        "safe": True,
        "issues": [],
        "sanitized_filename": None
    }

    if not filename:
        result["safe"] = False
        result["issues"].append("Empty filename")
        return result

    # Check for path traversal
    if '..' in filename or filename.startswith('/') or '\\' in filename:
        result["safe"] = False
        result["issues"].append("Path traversal attempt detected")

    # Check for null bytes
    if '\x00' in filename:
        result["safe"] = False
        result["issues"].append("Null byte in filename")

    # Check for control characters
    if any(ord(c) < 32 for c in filename if c not in '\t\n\r'):
        result["safe"] = False
        result["issues"].append("Control characters in filename")

    # Check archive extensions if not allowed
    if not allow_archives and is_archive_extension(filename):
        result["safe"] = False
        result["issues"].append("Archive file not allowed")

    # Check length
    if len(filename) > 255:
        result["issues"].append("Filename too long")

    # Provide sanitized version
    result["sanitized_filename"] = sanitize_filename(filename)

    return result
