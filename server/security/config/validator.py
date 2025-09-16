"""
Centralized Security Config Validator

Loads security configuration from environment variables and validates
production requirements with safe /healthz/config endpoint for SREs.
"""

from __future__ import annotations
import os
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException


@dataclass
class SecurityConfig:
    """Security configuration loaded from environment variables."""
    env: str
    jwks_url: Optional[str]
    jwt_aud: Optional[str]
    jwt_iss: Optional[str]
    redis_url: Optional[str]
    fail_closed_tier_threshold: int
    guard_profile: str
    max_body_bytes: int
    enable_compression_guard: bool
    enable_multipart_adapter: bool
    enable_global_scrubbing: bool
    idempotency_ttl_seconds: int


def load_security_config() -> SecurityConfig:
    """Load security configuration from environment variables."""
    env = os.getenv("APP_ENV", "development").lower()
    
    return SecurityConfig(
        env=env,
        jwks_url=os.getenv("NINAIVALAIGAL_JWKS_URL"),
        jwt_aud=os.getenv("NINAIVALAIGAL_JWT_AUDIENCE"),
        jwt_iss=os.getenv("NINAIVALAIGAL_JWT_ISSUER"),
        redis_url=os.getenv("REDIS_URL"),
        fail_closed_tier_threshold=int(os.getenv("FAIL_CLOSED_TIER_THRESHOLD", "3")),
        guard_profile=os.getenv("SECURITY_GUARD_PROFILE", "edge-decompress"),
        max_body_bytes=int(os.getenv("MAX_BODY_BYTES", str(10 * 1024 * 1024))),  # 10MB default
        enable_compression_guard=os.getenv("ENABLE_COMPRESSION_GUARD", "true").lower() == "true",
        enable_multipart_adapter=os.getenv("ENABLE_MULTIPART_ADAPTER", "true").lower() == "true",
        enable_global_scrubbing=os.getenv("ENABLE_GLOBAL_SCRUBBING", "true").lower() == "true",
        idempotency_ttl_seconds=int(os.getenv("IDEMPOTENCY_TTL_SECONDS", "3600")),  # 1 hour default
    )


class ConfigError(Exception):
    """Configuration validation error."""
    pass


def validate_or_raise(cfg: SecurityConfig) -> None:
    """
    Validate security configuration and raise ConfigError for unsafe prod configs.
    
    Fails fast on app startup if required production variables are missing
    or if dangerous configuration combinations are detected.
    """
    errors = []
    warnings = []
    
    # Production-specific validations
    if cfg.env == "production":
        # Required production settings
        if not cfg.jwks_url:
            errors.append("NINAIVALAIGAL_JWKS_URL required in production")
        elif not _is_valid_url(cfg.jwks_url):
            errors.append("NINAIVALAIGAL_JWKS_URL must be valid HTTPS URL")
        
        if not cfg.jwt_aud:
            errors.append("NINAIVALAIGAL_JWT_AUDIENCE required in production")
        
        if not cfg.jwt_iss:
            errors.append("NINAIVALAIGAL_JWT_ISSUER required in production")
        
        if not cfg.redis_url:
            errors.append("REDIS_URL required for distributed idempotency in production")
        elif not _is_valid_redis_url(cfg.redis_url):
            errors.append("REDIS_URL must be valid redis:// or rediss:// URL")
        
        # Security thresholds
        if cfg.fail_closed_tier_threshold < 3:
            errors.append("FAIL_CLOSED_TIER_THRESHOLD must be >= 3 in production (current: {})".format(
                cfg.fail_closed_tier_threshold
            ))
        
        # Body size limits
        if cfg.max_body_bytes > 50 * 1024 * 1024:  # 50MB
            warnings.append("MAX_BODY_BYTES > 50MB may impact performance")
        
        # Security guards
        if not cfg.enable_compression_guard:
            warnings.append("ENABLE_COMPRESSION_GUARD=false reduces security in production")
        
        if not cfg.enable_global_scrubbing:
            warnings.append("ENABLE_GLOBAL_SCRUBBING=false may leak secrets in logs")
    
    # Environment-agnostic validations
    if cfg.fail_closed_tier_threshold < 1 or cfg.fail_closed_tier_threshold > 5:
        errors.append("FAIL_CLOSED_TIER_THRESHOLD must be between 1-5")
    
    if cfg.max_body_bytes < 1024:  # 1KB minimum
        errors.append("MAX_BODY_BYTES must be at least 1024 bytes")
    
    if cfg.idempotency_ttl_seconds < 60:  # 1 minute minimum
        errors.append("IDEMPOTENCY_TTL_SECONDS must be at least 60 seconds")
    
    # Guard profile validation
    valid_profiles = ["edge-decompress", "reject-encoding", "content-type-strict", "multipart-strict"]
    if cfg.guard_profile not in valid_profiles:
        errors.append(f"SECURITY_GUARD_PROFILE must be one of: {valid_profiles}")
    
    # Raise errors if any found
    if errors:
        raise ConfigError("Security configuration errors: " + "; ".join(errors))
    
    # Log warnings (in real implementation, use proper logging)
    if warnings:
        import logging
        for warning in warnings:
            logging.warning(f"Security config warning: {warning}")


def _is_valid_url(url: str) -> bool:
    """Validate URL format for JWKS endpoints."""
    url_pattern = re.compile(
        r'^https://[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?(?::\d+)?(?:/[^\s]*)?$'
    )
    return bool(url_pattern.match(url))


def _is_valid_redis_url(url: str) -> bool:
    """Validate Redis URL format."""
    redis_pattern = re.compile(
        r'^rediss?://(?:[^:@]+:[^@]+@)?[a-zA-Z0-9.-]+(?::\d+)?(?:/\d+)?$'
    )
    return bool(redis_pattern.match(url))


def make_health_router(cfg: SecurityConfig) -> APIRouter:
    """
    Create health check router with safe config endpoint.
    
    Returns configuration snapshot without exposing secrets for SRE debugging.
    """
    router = APIRouter()
    
    @router.get("/healthz/config")
    def healthz_config() -> Dict[str, Any]:
        """Safe configuration snapshot for SRE debugging (no secrets exposed)."""
        return {
            "status": "healthy",
            "env": cfg.env,
            "security_config": {
                "jwks_url_configured": bool(cfg.jwks_url),
                "jwks_url_domain": _extract_domain(cfg.jwks_url) if cfg.jwks_url else None,
                "jwt_aud_configured": bool(cfg.jwt_aud),
                "jwt_iss_configured": bool(cfg.jwt_iss),
                "redis_configured": bool(cfg.redis_url),
                "redis_scheme": _extract_scheme(cfg.redis_url) if cfg.redis_url else None,
                "fail_closed_tier_threshold": cfg.fail_closed_tier_threshold,
                "guard_profile": cfg.guard_profile,
                "max_body_mb": round(cfg.max_body_bytes / (1024 * 1024), 2),
                "compression_guard_enabled": cfg.enable_compression_guard,
                "multipart_adapter_enabled": cfg.enable_multipart_adapter,
                "global_scrubbing_enabled": cfg.enable_global_scrubbing,
                "idempotency_ttl_hours": round(cfg.idempotency_ttl_seconds / 3600, 2),
            },
            "validation_status": "passed"
        }
    
    @router.get("/healthz/config/validate")
    def healthz_config_validate() -> Dict[str, Any]:
        """Validate current configuration and return status."""
        try:
            validate_or_raise(cfg)
            return {
                "status": "valid",
                "env": cfg.env,
                "validation_passed": True,
                "errors": [],
                "timestamp": _get_timestamp()
            }
        except ConfigError as e:
            return {
                "status": "invalid",
                "env": cfg.env,
                "validation_passed": False,
                "errors": str(e).split("; "),
                "timestamp": _get_timestamp()
            }
    
    return router


def _extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL for safe logging."""
    if not url:
        return None
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.split('@')[-1]  # Remove auth info if present
    except Exception:
        return "invalid_url"


def _extract_scheme(url: str) -> Optional[str]:
    """Extract scheme from URL for safe logging."""
    if not url:
        return None
    
    try:
        from urllib.parse import urlparse
        return urlparse(url).scheme
    except Exception:
        return "invalid_url"


def _get_timestamp() -> str:
    """Get current timestamp for health checks."""
    import datetime
    return datetime.datetime.utcnow().isoformat() + "Z"


def test_config_validator():
    """Test security config validator functionality."""
    
    # Test valid production config
    os.environ.update({
        "APP_ENV": "production",
        "NINAIVALAIGAL_JWKS_URL": "https://auth.example.com/.well-known/jwks.json",
        "NINAIVALAIGAL_JWT_AUDIENCE": "ninaivalaigal-api",
        "NINAIVALAIGAL_JWT_ISSUER": "https://auth.example.com",
        "REDIS_URL": "redis://localhost:6379/0",
        "FAIL_CLOSED_TIER_THRESHOLD": "3"
    })
    
    try:
        cfg = load_security_config()
        validate_or_raise(cfg)
        production_test_passed = True
    except ConfigError:
        production_test_passed = False
    
    # Test invalid production config
    os.environ["NINAIVALAIGAL_JWKS_URL"] = ""  # Remove required setting
    
    try:
        cfg = load_security_config()
        validate_or_raise(cfg)
        validation_test_passed = False  # Should have failed
    except ConfigError:
        validation_test_passed = True  # Correctly caught error
    
    # Test development config (more lenient)
    os.environ["APP_ENV"] = "development"
    
    try:
        cfg = load_security_config()
        validate_or_raise(cfg)
        development_test_passed = True
    except ConfigError:
        development_test_passed = False
    
    # Clean up environment
    for key in ["APP_ENV", "NINAIVALAIGAL_JWKS_URL", "NINAIVALAIGAL_JWT_AUDIENCE", 
                "NINAIVALAIGAL_JWT_ISSUER", "REDIS_URL", "FAIL_CLOSED_TIER_THRESHOLD"]:
        os.environ.pop(key, None)
    
    return {
        "production_validation_passed": production_test_passed,
        "error_detection_passed": validation_test_passed,
        "development_validation_passed": development_test_passed,
        "all_tests_passed": all([production_test_passed, validation_test_passed, development_test_passed])
    }


if __name__ == "__main__":
    # Run tests
    results = test_config_validator()
    print("Security Config Validator Test Results:")
    print(f"✅ Production validation: {results['production_validation_passed']}")
    print(f"✅ Error detection: {results['error_detection_passed']}")
    print(f"✅ Development validation: {results['development_validation_passed']}")
    print(f"Overall: {'✅ PASSED' if results['all_tests_passed'] else '❌ FAILED'}")
