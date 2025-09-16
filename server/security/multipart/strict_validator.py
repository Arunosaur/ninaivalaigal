"""
Strict Multipart Validator

Enforces MIME subtype allowlist and rejects filename/content-type mismatches
to prevent multipart-based security bypasses and evasion attacks.
"""

import re
from typing import Dict, List, Optional, Set, Any
import re
import mimetypes
from dataclasses import dataclass
from .binary_masquerade_guard import looks_binary
from starlette.datastructures import UploadFile


@dataclass
class MultipartPolicy:
    """Multipart validation policy configuration."""
    allowed_text_types: Set[str]
    allowed_binary_types: Set[str]
    max_filename_length: int = 255
    require_content_type_match: bool = True
    block_executable_extensions: bool = True
    max_parts: int = 100


class StrictMultipartValidator:
    """Strict validator for multipart/form-data with security policies."""
    
    # Default allowed MIME types per external review
    DEFAULT_TEXT_TYPES = {
        "text/plain",
        "application/json", 
        "application/x-www-form-urlencoded"
    }
    
    DEFAULT_BINARY_TYPES = {
        "image/jpeg",
        "image/png", 
        "image/gif",
        "application/pdf"
    }
    
    # Dangerous file extensions to block
    EXECUTABLE_EXTENSIONS = {
        ".exe", ".bat", ".cmd", ".com", ".scr", ".pif", ".vbs", ".js", ".jar",
        ".sh", ".py", ".pl", ".php", ".asp", ".jsp", ".dll", ".so", ".dylib"
    }
    
    def __init__(self, policy: Optional[MultipartPolicy] = None):
        self.policy = policy or MultipartPolicy(
            allowed_text_types=self.DEFAULT_TEXT_TYPES.copy(),
            allowed_binary_types=self.DEFAULT_BINARY_TYPES.copy()
        )
        
        # Compile regex patterns for efficiency
        self._filename_pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
        self._content_type_pattern = re.compile(r'^([a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_]*)/([a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_]*)$')
    
    def validate_part(self, field_name: str, content_type: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate individual multipart part against policy.
        
        Returns validation result with details.
        """
        result = {
            "field_name": field_name,
            "valid": True,
            "violations": [],
            "content_type": content_type,
            "filename": filename,
            "part_type": None
        }
        
        # Validate content type format
        if not self._content_type_pattern.match(content_type):
            result["valid"] = False
            result["violations"].append("invalid_content_type_format")
            return result
        
        # Determine if text or binary part
        is_text_type = content_type in self.policy.allowed_text_types
        is_binary_type = content_type in self.policy.allowed_binary_types
        
        if is_text_type:
            result["part_type"] = "text"
        elif is_binary_type:
            result["part_type"] = "binary"
        else:
            result["valid"] = False
            result["violations"].append("content_type_not_allowed")
            result["part_type"] = "unknown"
        
        # Validate filename if present
        if filename:
            filename_validation = self._validate_filename(filename, content_type)
            if not filename_validation["valid"]:
                result["valid"] = False
                result["violations"].extend(filename_validation["violations"])
        
        return result
    
    def _validate_filename(self, filename: str, content_type: str) -> Dict[str, Any]:
        """Validate filename against security policies."""
        result = {"valid": True, "violations": []}
        
        # Check filename length
        if len(filename) > self.policy.max_filename_length:
            result["valid"] = False
            result["violations"].append("filename_too_long")
        
        # Check for dangerous characters
        if not self._filename_pattern.match(filename):
            result["valid"] = False
            result["violations"].append("filename_invalid_characters")
        
        # Check for executable extensions
        if self._is_executable_extension(filename):
            violations.append({
                "type": "executable_extension",
                "message": f"Executable file extension not allowed: {filename}",
                "severity": "high"
            })
        
        # Check for binary masquerade
        if content and looks_binary(content, content_type, filename):
            violations.append({
                "type": "binary_masquerade",
                "message": f"Binary content masquerading as {content_type}",
                "severity": "high"
            })
        
        result["violations"].extend(violations)
        
        # Check filename/content-type mismatch
        if self.policy.require_content_type_match:
            mismatch = self._detect_content_type_mismatch(filename, content_type)
            if mismatch:
                result["valid"] = False
                result["violations"].append("filename_content_type_mismatch")
                result["mismatch_details"] = mismatch
        
        return result
    
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension in lowercase."""
        if '.' not in filename:
            return ""
        return "." + filename.split('.')[-1].lower()
    
    def _detect_content_type_mismatch(self, filename: str, content_type: str) -> Optional[Dict[str, str]]:
        """
        Detect filename/content-type mismatches that could indicate evasion.
        
        Returns mismatch details if detected, None otherwise.
        """
        file_ext = self._get_file_extension(filename)
        
        # Common extension to content-type mappings
        extension_mappings = {
            ".txt": "text/plain",
            ".json": "application/json",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg", 
            ".png": "image/png",
            ".gif": "image/gif",
            ".pdf": "application/pdf",
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".xml": "application/xml"
        }
        
        expected_type = extension_mappings.get(file_ext)
        if expected_type and expected_type != content_type:
            return {
                "filename": filename,
                "file_extension": file_ext,
                "declared_content_type": content_type,
                "expected_content_type": expected_type
            }
        
        return None
    
    def validate_multipart_request(self, parts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate entire multipart request against policy.
        
        Args:
            parts: List of part dictionaries with keys: field_name, content_type, filename
        """
        result = {
            "valid": True,
            "total_parts": len(parts),
            "violations": [],
            "part_results": [],
            "summary": {
                "text_parts": 0,
                "binary_parts": 0,
                "invalid_parts": 0
            }
        }
        
        # Check total parts limit
        if len(parts) > self.policy.max_parts:
            result["valid"] = False
            result["violations"].append("too_many_parts")
        
        # Validate each part
        for part in parts:
            part_result = self.validate_part(
                part["field_name"],
                part["content_type"], 
                part.get("filename")
            )
            
            result["part_results"].append(part_result)
            
            if not part_result["valid"]:
                result["valid"] = False
                result["summary"]["invalid_parts"] += 1
            elif part_result["part_type"] == "text":
                result["summary"]["text_parts"] += 1
            elif part_result["part_type"] == "binary":
                result["summary"]["binary_parts"] += 1
        
        return result
    
    def create_security_report(self, validation_result: Dict[str, Any]) -> str:
        """Create human-readable security validation report."""
        if validation_result["valid"]:
            return f"✅ Multipart validation passed: {validation_result['total_parts']} parts validated"
        
        violations = []
        for part_result in validation_result["part_results"]:
            if not part_result["valid"]:
                part_violations = ", ".join(part_result["violations"])
                violations.append(f"Field '{part_result['field_name']}': {part_violations}")
        
        global_violations = validation_result.get("violations", [])
        if global_violations:
            violations.extend([f"Global: {v}" for v in global_violations])
        
        return f"❌ Multipart validation failed:\n" + "\n".join(f"  - {v}" for v in violations)


def create_strict_policy(
    allow_binary: bool = False,
    custom_text_types: Optional[Set[str]] = None,
    custom_binary_types: Optional[Set[str]] = None
) -> MultipartPolicy:
    """Create strict multipart policy for production."""
    
    text_types = custom_text_types or StrictMultipartValidator.DEFAULT_TEXT_TYPES
    binary_types = custom_binary_types or (StrictMultipartValidator.DEFAULT_BINARY_TYPES if allow_binary else set())
    
    return MultipartPolicy(
        allowed_text_types=text_types,
        allowed_binary_types=binary_types,
        require_content_type_match=True,
        block_executable_extensions=True,
        max_parts=50  # Strict limit
    )


def create_permissive_policy() -> MultipartPolicy:
    """Create permissive policy for development."""
    return MultipartPolicy(
        allowed_text_types=StrictMultipartValidator.DEFAULT_TEXT_TYPES | {
            "text/html", "text/css", "application/javascript", "application/xml"
        },
        allowed_binary_types=StrictMultipartValidator.DEFAULT_BINARY_TYPES | {
            "image/svg+xml", "application/zip", "text/csv"
        },
        require_content_type_match=False,
        block_executable_extensions=True,
        max_parts=100
    )


# Integration with Starlette
async def validate_starlette_multipart(request, policy: Optional[MultipartPolicy] = None) -> Dict[str, Any]:
    """Validate Starlette multipart request."""
    validator = StrictMultipartValidator(policy)
    
    # Extract parts information from request
    form = await request.form()
    parts = []
    
    for field_name, field_value in form.items():
        if isinstance(field_value, UploadFile):
            parts.append({
                "field_name": field_name,
                "content_type": field_value.content_type or "application/octet-stream",
                "filename": field_value.filename
            })
        else:
            # Text field
            parts.append({
                "field_name": field_name,
                "content_type": "text/plain",
                "filename": None
            })
    
    return validator.validate_multipart_request(parts)


# Test utilities
def test_multipart_validation():
    """Test multipart validation functionality."""
    validator = StrictMultipartValidator()
    
    # Test cases
    test_parts = [
        {
            "field_name": "document",
            "content_type": "application/pdf",
            "filename": "report.pdf"
        },
        {
            "field_name": "malicious",
            "content_type": "text/plain", 
            "filename": "script.exe"  # Mismatch!
        },
        {
            "field_name": "data",
            "content_type": "application/json",
            "filename": None
        }
    ]
    
    result = validator.validate_multipart_request(test_parts)
    report = validator.create_security_report(result)
    
    return {
        "validation_result": result,
        "security_report": report,
        "test_passed": not result["valid"]  # Should fail due to mismatch
    }


def test_content_type_mismatch():
    """Test content-type mismatch detection."""
    validator = StrictMultipartValidator()
    
    test_cases = [
        ("document.pdf", "application/pdf", False),  # Match
        ("image.jpg", "image/jpeg", False),          # Match  
        ("script.js", "text/plain", True),           # Mismatch
        ("data.json", "application/pdf", True),      # Mismatch
        ("file.txt", "text/plain", False),           # Match
    ]
    
    results = []
    for filename, content_type, should_mismatch in test_cases:
        mismatch = validator._detect_content_type_mismatch(filename, content_type)
        detected_mismatch = mismatch is not None
        
        results.append({
            "filename": filename,
            "content_type": content_type,
            "expected_mismatch": should_mismatch,
            "detected_mismatch": detected_mismatch,
            "correct": should_mismatch == detected_mismatch,
            "mismatch_details": mismatch
        })
    
    return results
