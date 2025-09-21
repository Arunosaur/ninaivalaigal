"""
Config Validator Test

Proves that production boot fails when required environment variables are missing
and validates security configuration enforcement.
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.security.config.validator import (
    ConfigError,
    load_security_config,
    make_health_router,
    validate_or_raise,
)


def test_production_requires_core_envs():
    """Test that production validation fails when required vars are missing."""

    # Save original environment
    original_env = {}
    required_vars = [
        "APP_ENV", "NINAIVALAIGAL_JWKS_URL", "NINAIVALAIGAL_JWT_AUDIENCE",
        "NINAIVALAIGAL_JWT_ISSUER", "REDIS_URL", "FAIL_CLOSED_TIER_THRESHOLD"
    ]

    for var in required_vars:
        original_env[var] = os.environ.get(var)

    try:
        # Set production environment with missing required vars
        os.environ["APP_ENV"] = "production"
        for var in required_vars[1:]:  # Skip APP_ENV
            if var in os.environ:
                del os.environ[var]

        cfg = load_security_config()

        # Should raise ConfigError
        with pytest.raises(ConfigError) as exc_info:
            validate_or_raise(cfg)

        error_msg = str(exc_info.value)
        assert "NINAIVALAIGAL_JWKS_URL required" in error_msg
        assert "REDIS_URL required" in error_msg
        assert "JWT_AUDIENCE required" in error_msg
        assert "JWT_ISSUER required" in error_msg

        return True

    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]


def test_development_allows_missing_vars():
    """Test that development environment is more lenient."""

    # Save original environment
    original_env = {}
    test_vars = ["APP_ENV", "NINAIVALAIGAL_JWKS_URL", "REDIS_URL"]

    for var in test_vars:
        original_env[var] = os.environ.get(var)

    try:
        # Set development environment
        os.environ["APP_ENV"] = "development"

        # Remove optional vars
        for var in test_vars[1:]:
            if var in os.environ:
                del os.environ[var]

        cfg = load_security_config()

        # Should NOT raise ConfigError in development
        validate_or_raise(cfg)  # Should pass without exception

        assert cfg.env == "development"
        assert cfg.jwks_url is None  # Allowed in development
        assert cfg.redis_url is None  # Allowed in development

        return True

    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]


def test_invalid_urls_rejected():
    """Test that invalid URLs are rejected in production."""

    original_env = {}
    test_vars = ["APP_ENV", "NINAIVALAIGAL_JWKS_URL", "REDIS_URL"]

    for var in test_vars:
        original_env[var] = os.environ.get(var)

    try:
        # Set production with invalid URLs
        os.environ.update({
            "APP_ENV": "production",
            "NINAIVALAIGAL_JWKS_URL": "not-a-valid-url",
            "NINAIVALAIGAL_JWT_AUDIENCE": "test-audience",
            "NINAIVALAIGAL_JWT_ISSUER": "test-issuer",
            "REDIS_URL": "invalid-redis-url"
        })

        cfg = load_security_config()

        # Should raise ConfigError for invalid URLs
        with pytest.raises(ConfigError) as exc_info:
            validate_or_raise(cfg)

        error_msg = str(exc_info.value)
        assert "valid HTTPS URL" in error_msg
        assert "valid redis://" in error_msg

        return True

    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]


def test_tier_threshold_validation():
    """Test fail-closed tier threshold validation."""

    original_env = {}
    test_vars = ["APP_ENV", "FAIL_CLOSED_TIER_THRESHOLD"]

    for var in test_vars:
        original_env[var] = os.environ.get(var)

    try:
        # Test invalid tier threshold in production
        os.environ.update({
            "APP_ENV": "production",
            "NINAIVALAIGAL_JWKS_URL": "https://auth.example.com/.well-known/jwks.json",
            "NINAIVALAIGAL_JWT_AUDIENCE": "test-audience",
            "NINAIVALAIGAL_JWT_ISSUER": "https://auth.example.com",
            "REDIS_URL": "redis://localhost:6379/0",
            "FAIL_CLOSED_TIER_THRESHOLD": "1"  # Too low for production
        })

        cfg = load_security_config()

        # Should raise ConfigError for low threshold in production
        with pytest.raises(ConfigError) as exc_info:
            validate_or_raise(cfg)

        error_msg = str(exc_info.value)
        assert "must be >= 3 in production" in error_msg

        # Test valid threshold
        os.environ["FAIL_CLOSED_TIER_THRESHOLD"] = "3"
        cfg = load_security_config()
        validate_or_raise(cfg)  # Should pass

        return True

    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]


def test_health_router_endpoints():
    """Test health check router endpoints."""

    # Create test config
    original_env = {}
    test_vars = ["APP_ENV", "NINAIVALAIGAL_JWKS_URL", "REDIS_URL"]

    for var in test_vars:
        original_env[var] = os.environ.get(var)

    try:
        # Set test environment
        os.environ.update({
            "APP_ENV": "development",
            "NINAIVALAIGAL_JWKS_URL": "https://auth.example.com/.well-known/jwks.json",
            "REDIS_URL": "redis://localhost:6379/0",
            "SECURITY_GUARD_PROFILE": "edge-decompress"
        })

        cfg = load_security_config()
        health_router = make_health_router(cfg)

        # Create test app
        app = FastAPI()
        app.include_router(health_router)

        client = TestClient(app)

        # Test /healthz/config endpoint
        response = client.get("/healthz/config")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["env"] == "development"
        assert data["security_config"]["jwks_url_configured"] == True
        assert data["security_config"]["redis_configured"] == True
        assert data["security_config"]["guard_profile"] == "edge-decompress"
        assert "jwks_url_domain" in data["security_config"]

        # Ensure no secrets are exposed
        config_str = str(data)
        assert "auth.example.com" in config_str  # Domain is OK
        assert ".well-known/jwks.json" not in config_str  # Full URL is hidden

        # Test /healthz/config/validate endpoint
        response = client.get("/healthz/config/validate")
        assert response.status_code == 200

        data = response.json()
        assert data["validation_passed"] == True
        assert data["env"] == "development"
        assert len(data["errors"]) == 0

        return True

    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]


def test_config_loading_defaults():
    """Test configuration loading with default values."""

    original_env = {}
    all_vars = [
        "APP_ENV", "NINAIVALAIGAL_JWKS_URL", "NINAIVALAIGAL_JWT_AUDIENCE",
        "NINAIVALAIGAL_JWT_ISSUER", "REDIS_URL", "FAIL_CLOSED_TIER_THRESHOLD",
        "SECURITY_GUARD_PROFILE", "MAX_BODY_BYTES", "ENABLE_COMPRESSION_GUARD",
        "ENABLE_MULTIPART_ADAPTER", "ENABLE_GLOBAL_SCRUBBING", "IDEMPOTENCY_TTL_SECONDS"
    ]

    for var in all_vars:
        original_env[var] = os.environ.get(var)

    try:
        # Clear all security-related env vars
        for var in all_vars:
            if var in os.environ:
                del os.environ[var]

        cfg = load_security_config()

        # Check defaults
        assert cfg.env == "development"  # Default
        assert cfg.fail_closed_tier_threshold == 3  # Default
        assert cfg.guard_profile == "edge-decompress"  # Default
        assert cfg.max_body_bytes == 10 * 1024 * 1024  # 10MB default
        assert cfg.enable_compression_guard == True  # Default
        assert cfg.enable_multipart_adapter == True  # Default
        assert cfg.enable_global_scrubbing == True  # Default
        assert cfg.idempotency_ttl_seconds == 3600  # 1 hour default

        return True

    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]


def run_all_config_tests():
    """Run all configuration validator tests."""

    tests = [
        ("Production Requires Core Envs", test_production_requires_core_envs),
        ("Development Allows Missing Vars", test_development_allows_missing_vars),
        ("Invalid URLs Rejected", test_invalid_urls_rejected),
        ("Tier Threshold Validation", test_tier_threshold_validation),
        ("Health Router Endpoints", test_health_router_endpoints),
        ("Config Loading Defaults", test_config_loading_defaults),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed, None))
        except Exception as e:
            results.append((test_name, False, str(e)))

    return results


if __name__ == "__main__":
    # Run all tests
    test_results = run_all_config_tests()

    print("Config Validator Test Results:")
    print("=" * 60)

    passed_count = 0
    total_count = len(test_results)

    for test_name, passed, error in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} {test_name}")

        if error:
            print(f"   Error: {error}")

        if passed:
            passed_count += 1

    print("=" * 60)
    print(f"Overall: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("🎉 All config validation tests passed!")
    else:
        print("⚠️  Some tests failed - check implementation")
