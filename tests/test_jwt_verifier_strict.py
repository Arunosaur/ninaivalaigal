import time

import jwt
import pytest

from server.security.jwt.verifier_strict import (
    JWTValidationError,
    StrictJWTConfig,
    create_production_jwt_config,
    verify_jwt_strict,
)

SECRET = "dev-secret-key-for-testing-purposes-only"


def mk(
    aud="test-audience",
    iss="https://test.issuer.com",
    iat=None,
    exp=None,
    nbf=None,
    sub="test-user",
    jti=None,
    **extra_claims,
):
    """Create test JWT token."""
    now = int(time.time())
    payload = {
        "sub": sub,
        "aud": aud,
        "iss": iss,
        "iat": iat or now,
        "exp": exp or now + 600,
        **extra_claims,
    }
    if nbf is not None:
        payload["nbf"] = nbf
    if jti is not None:
        payload["jti"] = jti
    return jwt.encode(payload, SECRET, algorithm="HS256")


def test_basic_strict_validation():
    """Test basic strict JWT validation with allowlists."""
    token = mk()
    config = StrictJWTConfig(
        audience_allowlist={"test-audience"},
        issuer_allowlist={"https://test.issuer.com"},
    )
    claims = verify_jwt_strict(token, key=SECRET, config=config)
    assert claims["sub"] == "test-user"
    assert claims["aud"] == "test-audience"
    assert claims["iss"] == "https://test.issuer.com"


def test_legacy_parameter_compatibility():
    """Test backward compatibility with legacy parameters."""
    token = mk()
    claims = verify_jwt_strict(
        token,
        key=SECRET,
        audience_allowlist={"test-audience"},
        issuer_allowlist={"https://test.issuer.com"},
    )
    assert claims["sub"] == "test-user"


def test_audience_allowlist_validation():
    """Test strict audience allowlist validation."""
    # Valid audience
    token = mk(aud="allowed-audience")
    config = StrictJWTConfig(audience_allowlist={"allowed-audience", "other-allowed"})
    claims = verify_jwt_strict(token, key=SECRET, config=config)
    assert claims["aud"] == "allowed-audience"

    # Invalid audience
    token = mk(aud="forbidden-audience")
    with pytest.raises(JWTValidationError, match="No valid audience found"):
        verify_jwt_strict(token, key=SECRET, config=config)


def test_audience_array_validation():
    """Test validation with multiple audiences in token."""
    token = mk(aud=["app1", "app2", "app3"])
    config = StrictJWTConfig(audience_allowlist={"app2", "app4"})
    claims = verify_jwt_strict(token, key=SECRET, config=config)
    assert "app2" in claims["aud"]


def test_issuer_allowlist_validation():
    """Test strict issuer allowlist validation."""
    # Valid issuer
    token = mk(iss="https://trusted.issuer.com")
    config = StrictJWTConfig(issuer_allowlist={"https://trusted.issuer.com"})
    claims = verify_jwt_strict(token, key=SECRET, config=config)
    assert claims["iss"] == "https://trusted.issuer.com"

    # Invalid issuer
    token = mk(iss="https://malicious.issuer.com")
    with pytest.raises(JWTValidationError, match="Invalid issuer"):
        verify_jwt_strict(token, key=SECRET, config=config)


def test_bounded_leeway_validation():
    """Test bounded clock skew (leeway) validation."""
    now = int(time.time())

    # Token valid with leeway
    token = mk(nbf=now + 60)
    config = StrictJWTConfig(leeway_seconds=120)
    claims = verify_jwt_strict(token, key=SECRET, config=config)
    assert claims["sub"] == "test-user"

    # Token invalid with smaller leeway
    config = StrictJWTConfig(leeway_seconds=30)
    with pytest.raises(JWTValidationError, match="Invalid token"):
        verify_jwt_strict(token, key=SECRET, config=config)


def test_bounded_leeway_limits():
    """Test that leeway is bounded within acceptable limits."""
    # Valid leeway
    config = StrictJWTConfig(leeway_seconds=60)
    assert config.leeway_seconds == 60

    # Invalid leeway - too high
    with pytest.raises(ValueError, match="leeway_seconds must be 0-300"):
        StrictJWTConfig(leeway_seconds=400)

    # Invalid leeway - negative
    with pytest.raises(ValueError, match="leeway_seconds must be 0-300"):
        StrictJWTConfig(leeway_seconds=-10)


def test_token_age_validation():
    """Test maximum token age validation."""
    now = int(time.time())

    # Fresh token should pass
    token = mk(iat=now - 300)  # 5 minutes old
    config = StrictJWTConfig(max_token_age_seconds=600)  # 10 minutes max
    claims = verify_jwt_strict(token, key=SECRET, config=config)
    assert claims["sub"] == "test-user"

    # Old token should fail
    token = mk(iat=now - 7200)  # 2 hours old
    config = StrictJWTConfig(max_token_age_seconds=3600)  # 1 hour max
    with pytest.raises(JWTValidationError, match="Token too old"):
        verify_jwt_strict(token, key=SECRET, config=config)


def test_future_token_validation():
    """Test rejection of tokens issued in the future."""
    now = int(time.time())
    token = mk(iat=now + 300)  # 5 minutes in future
    config = StrictJWTConfig(leeway_seconds=60)  # Only 1 minute leeway

    with pytest.raises(JWTValidationError, match="Invalid token"):
        verify_jwt_strict(token, key=SECRET, config=config)


def test_jti_requirement():
    """Test JWT ID (jti) requirement for replay protection."""
    # Token without JTI should fail when required
    token = mk()
    config = StrictJWTConfig(require_jti=True)
    with pytest.raises(JWTValidationError, match="Token missing required 'jti' claim"):
        verify_jwt_strict(token, key=SECRET, config=config)

    # Token with valid JTI should pass
    token = mk(jti="unique-jwt-id-12345678")
    claims = verify_jwt_strict(token, key=SECRET, config=config)
    assert claims["jti"] == "unique-jwt-id-12345678"

    # Token with short JTI should fail
    token = mk(jti="short")
    with pytest.raises(JWTValidationError, match="JWT ID 'jti' too short"):
        verify_jwt_strict(token, key=SECRET, config=config)


def test_nbf_requirement():
    """Test not-before (nbf) claim requirement."""
    # Token without NBF should fail when required
    token = mk()
    config = StrictJWTConfig(require_nbf=True)
    with pytest.raises(JWTValidationError, match="Token missing required 'nbf' claim"):
        verify_jwt_strict(token, key=SECRET, config=config)

    # Token with valid NBF should pass
    now = int(time.time())
    token = mk(nbf=now - 60)
    claims = verify_jwt_strict(token, key=SECRET, config=config)
    assert claims["nbf"] == now - 60


def test_suspicious_claims_detection():
    """Test detection of suspicious claims and subjects."""
    # Test suspicious subject patterns
    token = mk(sub="admin-user")
    config = StrictJWTConfig()
    # Should pass but log warning (we can't easily test logging here)
    claims = verify_jwt_strict(token, key=SECRET, config=config)
    assert claims["sub"] == "admin-user"

    # Test dangerous scopes
    token = mk(scope="read write admin")
    claims = verify_jwt_strict(token, key=SECRET, config=config)
    assert "admin" in claims["scope"]

    # Test privileged roles
    token = mk(roles=["user", "admin", "editor"])
    claims = verify_jwt_strict(token, key=SECRET, config=config)
    assert "admin" in claims["roles"]


def test_production_config():
    """Test production JWT configuration."""
    config = create_production_jwt_config(
        audience_allowlist={"prod-app"},
        issuer_allowlist={"https://prod.auth.com"},
        leeway_seconds=30,
        max_token_age_seconds=900,  # 15 minutes
        require_jti=True,
    )

    assert config.audience_allowlist == {"prod-app"}
    assert config.issuer_allowlist == {"https://prod.auth.com"}
    assert config.leeway_seconds == 30
    assert config.max_token_age_seconds == 900
    assert config.require_jti == True
    assert config.require_nbf == True
    assert config.algorithms == ("RS256", "ES256")


def test_missing_required_claims():
    """Test validation of required claims."""
    # Missing subject
    payload = {
        "aud": "test",
        "iss": "test",
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,
    }
    token = jwt.encode(payload, SECRET, algorithm="HS256")

    with pytest.raises(JWTValidationError, match="Invalid token"):
        verify_jwt_strict(token, key=SECRET)


def test_algorithm_restrictions():
    """Test algorithm restrictions in config."""
    config = StrictJWTConfig(algorithms=("RS256",))

    # HS256 token should fail with RS256-only config
    token = mk()  # Uses HS256
    with pytest.raises(JWTValidationError, match="Invalid token"):
        verify_jwt_strict(token, key=SECRET, config=config)


if __name__ == "__main__":
    # Run all tests
    test_functions = [
        test_basic_strict_validation,
        test_legacy_parameter_compatibility,
        test_audience_allowlist_validation,
        test_audience_array_validation,
        test_issuer_allowlist_validation,
        test_bounded_leeway_validation,
        test_bounded_leeway_limits,
        test_token_age_validation,
        test_future_token_validation,
        test_jti_requirement,
        test_nbf_requirement,
        test_suspicious_claims_detection,
        test_production_config,
        test_missing_required_claims,
        test_algorithm_restrictions,
    ]

    print("Running strict JWT verifier tests...")

    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")
            raise

    print(f"\nAll {len(test_functions)} strict JWT verifier tests passed!")
    print(
        "Enhanced JWT verifier with bounded leeway and comprehensive validation ready for production."
    )
