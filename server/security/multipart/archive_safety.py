"""Archive safety guards for binary endpoints with size and entry limits."""

import zipfile
import tarfile
import io
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ArchiveLimits:
    """Configuration for archive safety limits."""
    max_uncompressed_size: int = 100 * 1024 * 1024  # 100MB
    max_entries: int = 1000  # 1k files
    max_nesting_depth: int = 3  # Prevent zip bombs
    block_nested_archives: bool = True


def validate_archive_safety(
    content: bytes, 
    content_type: str,
    limits: Optional[ArchiveLimits] = None
) -> Dict[str, Any]:
    """
    Validate archive safety for binary endpoints.
    
    Args:
        content: Archive content bytes
        content_type: MIME content type
        limits: Archive safety limits configuration
        
    Returns:
        Validation result with safety status and metrics
    """
    if limits is None:
        limits = ArchiveLimits()
    
    result = {
        "safe": True,
        "violations": [],
        "metrics": {
            "entries": 0,
            "uncompressed_size": 0,
            "compression_ratio": 0.0,
            "nesting_depth": 0
        },
        "archive_type": None
    }
    
    # Detect archive type
    if content.startswith(b'PK\x03\x04') or content.startswith(b'PK\x05\x06'):
        result["archive_type"] = "ZIP"
        return _validate_zip_safety(content, limits, result)
    elif content.startswith(b'ustar') or b'ustar' in content[:512]:
        result["archive_type"] = "TAR"
        return _validate_tar_safety(content, limits, result)
    elif content.startswith(b'\x1f\x8b'):
        result["archive_type"] = "GZIP"
        # For GZIP, try to extract and validate inner content
        try:
            import gzip
            decompressed = gzip.decompress(content)
            if len(decompressed) > limits.max_uncompressed_size:
                result["safe"] = False
                result["violations"].append({
                    "type": "size_limit_exceeded",
                    "message": f"Decompressed size {len(decompressed)} exceeds limit {limits.max_uncompressed_size}",
                    "severity": "high"
                })
            result["metrics"]["uncompressed_size"] = len(decompressed)
            result["metrics"]["compression_ratio"] = len(content) / len(decompressed) if decompressed else 0
        except Exception as e:
            result["safe"] = False
            result["violations"].append({
                "type": "decompression_error",
                "message": f"Failed to decompress GZIP: {e}",
                "severity": "medium"
            })
    
    return result


def _validate_zip_safety(content: bytes, limits: ArchiveLimits, result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate ZIP archive safety."""
    try:
        with zipfile.ZipFile(io.BytesIO(content), 'r') as zf:
            entries = zf.infolist()
            result["metrics"]["entries"] = len(entries)
            
            # Check entry count
            if len(entries) > limits.max_entries:
                result["safe"] = False
                result["violations"].append({
                    "type": "too_many_entries",
                    "message": f"Archive contains {len(entries)} entries, exceeds limit {limits.max_entries}",
                    "severity": "high"
                })
            
            total_uncompressed = 0
            max_nesting = 0
            
            for entry in entries:
                # Check individual file size
                if entry.file_size > limits.max_uncompressed_size:
                    result["safe"] = False
                    result["violations"].append({
                        "type": "file_too_large",
                        "message": f"File {entry.filename} size {entry.file_size} exceeds limit",
                        "severity": "high"
                    })
                
                total_uncompressed += entry.file_size
                
                # Check path traversal
                if '..' in entry.filename or entry.filename.startswith('/'):
                    result["safe"] = False
                    result["violations"].append({
                        "type": "path_traversal",
                        "message": f"Suspicious path in archive: {entry.filename}",
                        "severity": "critical"
                    })
                
                # Check nesting depth
                depth = entry.filename.count('/')
                max_nesting = max(max_nesting, depth)
                
                # Check for nested archives
                if limits.block_nested_archives:
                    filename_lower = entry.filename.lower()
                    if any(filename_lower.endswith(ext) for ext in ['.zip', '.tar', '.gz', '.rar', '.7z']):
                        result["safe"] = False
                        result["violations"].append({
                            "type": "nested_archive",
                            "message": f"Nested archive detected: {entry.filename}",
                            "severity": "high"
                        })
            
            # Check total uncompressed size
            if total_uncompressed > limits.max_uncompressed_size:
                result["safe"] = False
                result["violations"].append({
                    "type": "total_size_exceeded",
                    "message": f"Total uncompressed size {total_uncompressed} exceeds limit {limits.max_uncompressed_size}",
                    "severity": "high"
                })
            
            # Check nesting depth
            if max_nesting > limits.max_nesting_depth:
                result["safe"] = False
                result["violations"].append({
                    "type": "excessive_nesting",
                    "message": f"Directory nesting depth {max_nesting} exceeds limit {limits.max_nesting_depth}",
                    "severity": "medium"
                })
            
            result["metrics"]["uncompressed_size"] = total_uncompressed
            result["metrics"]["nesting_depth"] = max_nesting
            result["metrics"]["compression_ratio"] = len(content) / total_uncompressed if total_uncompressed > 0 else 0
            
    except zipfile.BadZipFile:
        result["safe"] = False
        result["violations"].append({
            "type": "corrupted_archive",
            "message": "Invalid or corrupted ZIP archive",
            "severity": "medium"
        })
    except Exception as e:
        result["safe"] = False
        result["violations"].append({
            "type": "processing_error",
            "message": f"Error processing ZIP archive: {e}",
            "severity": "medium"
        })
    
    return result


def _validate_tar_safety(content: bytes, limits: ArchiveLimits, result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate TAR archive safety."""
    try:
        with tarfile.open(fileobj=io.BytesIO(content), mode='r:*') as tf:
            members = tf.getmembers()
            result["metrics"]["entries"] = len(members)
            
            # Check entry count
            if len(members) > limits.max_entries:
                result["safe"] = False
                result["violations"].append({
                    "type": "too_many_entries",
                    "message": f"Archive contains {len(members)} entries, exceeds limit {limits.max_entries}",
                    "severity": "high"
                })
            
            total_uncompressed = 0
            max_nesting = 0
            
            for member in members:
                # Check individual file size
                if member.size > limits.max_uncompressed_size:
                    result["safe"] = False
                    result["violations"].append({
                        "type": "file_too_large",
                        "message": f"File {member.name} size {member.size} exceeds limit",
                        "severity": "high"
                    })
                
                total_uncompressed += member.size
                
                # Check path traversal
                if '..' in member.name or member.name.startswith('/'):
                    result["safe"] = False
                    result["violations"].append({
                        "type": "path_traversal",
                        "message": f"Suspicious path in archive: {member.name}",
                        "severity": "critical"
                    })
                
                # Check nesting depth
                depth = member.name.count('/')
                max_nesting = max(max_nesting, depth)
                
                # Check for nested archives
                if limits.block_nested_archives:
                    name_lower = member.name.lower()
                    if any(name_lower.endswith(ext) for ext in ['.zip', '.tar', '.gz', '.rar', '.7z']):
                        result["safe"] = False
                        result["violations"].append({
                            "type": "nested_archive",
                            "message": f"Nested archive detected: {member.name}",
                            "severity": "high"
                        })
            
            # Check total uncompressed size
            if total_uncompressed > limits.max_uncompressed_size:
                result["safe"] = False
                result["violations"].append({
                    "type": "total_size_exceeded",
                    "message": f"Total uncompressed size {total_uncompressed} exceeds limit {limits.max_uncompressed_size}",
                    "severity": "high"
                })
            
            # Check nesting depth
            if max_nesting > limits.max_nesting_depth:
                result["safe"] = False
                result["violations"].append({
                    "type": "excessive_nesting",
                    "message": f"Directory nesting depth {max_nesting} exceeds limit {limits.max_nesting_depth}",
                    "severity": "medium"
                })
            
            result["metrics"]["uncompressed_size"] = total_uncompressed
            result["metrics"]["nesting_depth"] = max_nesting
            result["metrics"]["compression_ratio"] = len(content) / total_uncompressed if total_uncompressed > 0 else 0
            
    except tarfile.TarError:
        result["safe"] = False
        result["violations"].append({
            "type": "corrupted_archive",
            "message": "Invalid or corrupted TAR archive",
            "severity": "medium"
        })
    except Exception as e:
        result["safe"] = False
        result["violations"].append({
            "type": "processing_error",
            "message": f"Error processing TAR archive: {e}",
            "severity": "medium"
        })
    
    return result
