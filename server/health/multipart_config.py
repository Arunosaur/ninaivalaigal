"""Multipart configuration health checks for /healthz/config endpoint."""

from typing import Dict, Any, List
from server.security.multipart.strict_limits_hardened import (
    DEFAULT_MAX_TEXT_PART_BYTES,
    DEFAULT_MAX_BINARY_PART_BYTES,
    DEFAULT_MAX_PARTS_PER_REQUEST,
)
from server.security.feature_flags import get_feature_flag_health


def get_multipart_config_health() -> Dict[str, Any]:
    """
    Get multipart configuration for health endpoint.
    
    Returns:
        Configuration status and limits for monitoring
    """
    config = {
        "status": "healthy",
        "limits": {
            "max_text_part_bytes": DEFAULT_MAX_TEXT_PART_BYTES,
            "max_binary_part_bytes": DEFAULT_MAX_BINARY_PART_BYTES,
            "max_parts_per_request": DEFAULT_MAX_PARTS_PER_REQUEST,
        },
        "security_features": {
            "part_count_limiting": True,
            "size_enforcement": True,
            "binary_masquerade_detection": True,
            "archive_blocking": True,
            "utf8_validation": True,
            "cte_guards": True,
            "magic_byte_detection": True,
        },
        "rejection_reasons": [
            "engine_error",
            "policy_denied", 
            "magic_mismatch",
            "part_too_large",
            "too_many_parts",
            "invalid_encoding",
            "archive_blocked"
        ],
        "boundary_limits": {
            "max_boundary_length": 200,  # chars
            "max_header_lines": 8192     # lines per part
        }
    }
    
    # Validate configuration sanity
    issues = []
    
    if DEFAULT_MAX_TEXT_PART_BYTES <= 0:
        issues.append("Invalid max_text_part_bytes: must be positive")
        config["status"] = "degraded"
    
    if DEFAULT_MAX_BINARY_PART_BYTES <= 0:
        issues.append("Invalid max_binary_part_bytes: must be positive")
        config["status"] = "degraded"
        
    if DEFAULT_MAX_PARTS_PER_REQUEST <= 0:
        issues.append("Invalid max_parts_per_request: must be positive")
        config["status"] = "degraded"
    
    # Check for reasonable limits
    if DEFAULT_MAX_TEXT_PART_BYTES > 100 * 1024 * 1024:  # 100MB
        issues.append("max_text_part_bytes unusually large (>100MB)")
        
    if DEFAULT_MAX_PARTS_PER_REQUEST > 1000:
        issues.append("max_parts_per_request unusually large (>1000)")
    
    if issues:
        config["issues"] = issues
        if config["status"] == "healthy":
            config["status"] = "warning"
    
    # Add feature flag status
    config["feature_flags"] = get_feature_flag_health()
    
    return config


def validate_multipart_boot_config() -> Dict[str, Any]:
    """
    Validate multipart configuration at boot time.
    
    Returns:
        Boot validation results with actionable messages
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "actionable_messages": []
    }
    
    try:
        # Test imports
        from server.security.multipart.starlette_adapter import scan_with_starlette
        from server.security.multipart.strict_limits_hardened import (
            detect_enhanced_magic_bytes,
            require_utf8_text,
            reject_content_transfer_encoding
        )
        
    except ImportError as e:
        result["valid"] = False
        result["errors"].append(f"Failed to import multipart modules: {e}")
        result["actionable_messages"].append(
            "Check that all multipart security modules are installed and accessible"
        )
        return result
    
    # Validate configuration values
    config_health = get_multipart_config_health()
    
    if config_health["status"] == "degraded":
        result["valid"] = False
        result["errors"].extend(config_health.get("issues", []))
        result["actionable_messages"].append(
            "Fix multipart configuration limits in strict_limits_hardened.py"
        )
    
    elif config_health["status"] == "warning":
        result["warnings"].extend(config_health.get("issues", []))
        result["actionable_messages"].append(
            "Review multipart configuration limits for production suitability"
        )
    
    # Test basic functionality
    try:
        # Test magic byte detection
        test_result = detect_enhanced_magic_bytes(b"MZ\x90\x00")
        if not test_result.get("detected"):
            result["warnings"].append("Magic byte detection may not be working correctly")
            
        # Test UTF-8 validation
        utf8_result = require_utf8_text(b"hello world")
        if not utf8_result.get("valid"):
            result["warnings"].append("UTF-8 validation may not be working correctly")
            
    except Exception as e:
        result["warnings"].append(f"Multipart function test failed: {e}")
        result["actionable_messages"].append(
            "Run multipart security tests to verify functionality"
        )
    
    return result
