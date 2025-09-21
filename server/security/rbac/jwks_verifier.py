"""
JWKS Verification with Rotation and Caching

Implements JWT verification with JWKS endpoint caching, kid selection,
and 5-10 minute cache TTL for production security requirements.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidKeyError, InvalidTokenError


@dataclass
class JWKSConfig:
    """JWKS configuration."""
    jwks_uri: str
    audience: str
    issuer: str
    cache_ttl: int = 600  # 10 minutes
    algorithms: list[str] = None

    def __post_init__(self):
        if self.algorithms is None:
            self.algorithms = ["RS256", "ES256", "HS256"]


class JWKSVerifier:
    """JWT verifier with JWKS rotation and caching."""

    def __init__(self, config: JWKSConfig):
        self.config = config
        self.logger = logging.getLogger("jwks.verifier")

        # Initialize PyJWKClient with caching
        self.jwks_client = PyJWKClient(
            uri=config.jwks_uri,
            cache_ttl=config.cache_ttl,
            cache_jwks=True
        )

        # Track key rotation events
        self._last_kid_seen = None
        self._rotation_count = 0

    async def verify_token(self, token: str) -> dict[str, Any]:
        """
        Verify JWT token with JWKS key rotation support.
        
        Raises:
            InvalidTokenError: Token validation failed
            InvalidKeyError: Key not found or invalid
        """
        try:
            # Get unverified header to extract kid
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise InvalidTokenError("Token missing 'kid' in header")

            # Track key rotation
            if self._last_kid_seen and self._last_kid_seen != kid:
                self._rotation_count += 1
                self.logger.info(f"Key rotation detected: {self._last_kid_seen} -> {kid}")

            self._last_kid_seen = kid

            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key(kid)

            # Verify token with full validation
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=self.config.algorithms,
                audience=self.config.audience,
                issuer=self.config.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "require": ["exp", "iat", "aud", "iss", "sub"]
                }
            )

            # Additional security checks
            self._validate_payload_security(payload)

            self.logger.info(f"Token verified successfully for subject: {payload.get('sub')}")
            return payload

        except InvalidTokenError as e:
            self.logger.error(f"Token validation failed: {e}")
            raise

        except InvalidKeyError as e:
            self.logger.error(f"Key validation failed: {e}")
            raise

        except Exception as e:
            self.logger.error(f"Unexpected verification error: {e}")
            raise InvalidTokenError(f"Token verification failed: {e}")

    def _validate_payload_security(self, payload: dict[str, Any]) -> None:
        """Additional security validation for JWT payload."""

        # Check token age (not too old)
        iat = payload.get("iat")
        if iat:
            token_age = time.time() - iat
            if token_age > 3600:  # 1 hour max age
                raise InvalidTokenError("Token too old")

        # Check for suspicious claims
        if "admin" in payload.get("scope", "").lower():
            self.logger.warning(f"Admin scope detected for subject: {payload.get('sub')}")

        # Validate subject format
        sub = payload.get("sub", "")
        if not sub or len(sub) < 3:
            raise InvalidTokenError("Invalid subject format")

    async def verify_with_replay_guard(self, token: str, nonce: str | None = None) -> dict[str, Any]:
        """
        Verify token with replay attack protection.
        
        For OAuth flows, validates nonce to prevent code replay.
        """
        payload = await self.verify_token(token)

        if nonce:
            token_nonce = payload.get("nonce")
            if not token_nonce or token_nonce != nonce:
                raise InvalidTokenError("Nonce mismatch - potential replay attack")

        return payload

    def get_rotation_stats(self) -> dict[str, Any]:
        """Get key rotation statistics."""
        return {
            "current_kid": self._last_kid_seen,
            "rotation_count": self._rotation_count,
            "cache_ttl": self.config.cache_ttl,
            "jwks_uri": self.config.jwks_uri
        }

    async def prefetch_keys(self) -> None:
        """Prefetch JWKS keys to warm cache."""
        try:
            # Force cache refresh
            self.jwks_client.get_jwks()
            self.logger.info("JWKS keys prefetched successfully")
        except Exception as e:
            self.logger.error(f"Failed to prefetch JWKS keys: {e}")


class JWKSVerifierPool:
    """Pool of JWKS verifiers for multiple issuers."""

    def __init__(self):
        self.verifiers: dict[str, JWKSVerifier] = {}
        self.logger = logging.getLogger("jwks.pool")

    def add_verifier(self, issuer: str, config: JWKSConfig) -> None:
        """Add verifier for issuer."""
        self.verifiers[issuer] = JWKSVerifier(config)
        self.logger.info(f"Added JWKS verifier for issuer: {issuer}")

    async def verify_token(self, token: str, issuer: str | None = None) -> dict[str, Any]:
        """Verify token using appropriate verifier."""

        if issuer:
            verifier = self.verifiers.get(issuer)
            if not verifier:
                raise InvalidTokenError(f"No verifier configured for issuer: {issuer}")
            return await verifier.verify_token(token)

        # Try all verifiers if issuer not specified
        last_error = None
        for iss, verifier in self.verifiers.items():
            try:
                return await verifier.verify_token(token)
            except InvalidTokenError as e:
                last_error = e
                continue

        raise last_error or InvalidTokenError("No valid verifier found")

    def get_pool_stats(self) -> dict[str, Any]:
        """Get statistics for all verifiers."""
        return {
            issuer: verifier.get_rotation_stats()
            for issuer, verifier in self.verifiers.items()
        }


# Global verifier pool
_verifier_pool = JWKSVerifierPool()


def configure_jwks_verifier(
    issuer: str,
    jwks_uri: str,
    audience: str,
    cache_ttl: int = 600,
    algorithms: list[str] | None = None
) -> None:
    """Configure JWKS verifier for issuer."""
    config = JWKSConfig(
        jwks_uri=jwks_uri,
        audience=audience,
        issuer=issuer,
        cache_ttl=cache_ttl,
        algorithms=algorithms
    )
    _verifier_pool.add_verifier(issuer, config)


async def verify_jwt_with_jwks(token: str, issuer: str | None = None) -> dict[str, Any]:
    """Global function to verify JWT with JWKS."""
    return await _verifier_pool.verify_token(token, issuer)


def get_jwks_stats() -> dict[str, Any]:
    """Get JWKS verification statistics."""
    return _verifier_pool.get_pool_stats()


# Test utilities
def create_test_jwks_config(
    issuer: str = "https://test.example.com",
    audience: str = "test-audience"
) -> JWKSConfig:
    """Create test JWKS configuration."""
    return JWKSConfig(
        jwks_uri=f"{issuer}/.well-known/jwks.json",
        audience=audience,
        issuer=issuer,
        cache_ttl=300  # 5 minutes for testing
    )


async def test_jwks_rotation(verifier: JWKSVerifier, tokens: list[str]) -> dict[str, Any]:
    """Test JWKS key rotation with multiple tokens."""
    results = []

    for i, token in enumerate(tokens):
        try:
            payload = await verifier.verify_token(token)
            results.append({
                "token_index": i,
                "success": True,
                "subject": payload.get("sub"),
                "kid": jwt.get_unverified_header(token).get("kid")
            })
        except Exception as e:
            results.append({
                "token_index": i,
                "success": False,
                "error": str(e)
            })

    return {
        "test_results": results,
        "rotation_stats": verifier.get_rotation_stats()
    }
