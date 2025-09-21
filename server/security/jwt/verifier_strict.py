from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import jwt  # PyJWT

logger = logging.getLogger(__name__)


class JWTValidationError(Exception):
    """Strict JWT validation error with detailed context."""

    pass


@dataclass
class StrictJWTConfig:
    """Configuration for strict JWT verification."""

    audience_allowlist: set[str] | None = None
    issuer_allowlist: set[str] | None = None
    leeway_seconds: int = 120  # Bounded clock skew tolerance
    max_token_age_seconds: int = 3600  # Maximum token age (1 hour)
    require_jti: bool = False  # Require JWT ID for replay protection
    require_nbf: bool = False  # Require not-before claim
    algorithms: tuple[str, ...] = ("RS256", "ES256", "HS256")

    def __post_init__(self):
        # Validate bounded leeway
        if self.leeway_seconds < 0 or self.leeway_seconds > 300:  # Max 5 minutes
            raise ValueError(f"leeway_seconds must be 0-300, got {self.leeway_seconds}")

        # Validate token age limit
        if (
            self.max_token_age_seconds < 300 or self.max_token_age_seconds > 86400
        ):  # 5min - 24hrs
            raise ValueError(
                f"max_token_age_seconds must be 300-86400, got {self.max_token_age_seconds}"
            )


def verify_jwt_strict(
    token: str,
    *,
    key: str | bytes,
    config: StrictJWTConfig | None = None,
    # Legacy parameters for backward compatibility
    algorithms: Iterable[str] | None = None,
    audience_allowlist: set[str] | None = None,
    issuer_allowlist: set[str] | None = None,
    leeway_seconds: int | None = None,
) -> dict[str, Any]:
    """
    Strict JWT verification with bounded clock skew and comprehensive validation.

    Args:
        token: JWT token to verify
        key: Signing key (string or bytes)
        config: StrictJWTConfig instance (preferred)
        algorithms: Allowed algorithms (legacy)
        audience_allowlist: Allowed audiences (legacy)
        issuer_allowlist: Allowed issuers (legacy)
        leeway_seconds: Clock skew tolerance (legacy)

    Returns:
        Validated JWT claims

    Raises:
        JWTValidationError: Validation failed with detailed reason
    """
    # Handle legacy parameters vs config
    if config is None:
        config = StrictJWTConfig(
            audience_allowlist=audience_allowlist,
            issuer_allowlist=issuer_allowlist,
            leeway_seconds=leeway_seconds or 120,
            algorithms=tuple(algorithms) if algorithms else ("HS256",),
        )

    start_time = time.time()

    try:
        # Step 1: Basic JWT decode with signature verification
        claims = jwt.decode(
            token,
            key=key,
            algorithms=list(config.algorithms),
            audience=None,  # We'll validate manually for better control
            issuer=None,  # We'll validate manually for better control
            options={
                "require": ["exp", "iat", "sub"],
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": False,  # Disable internal audience validation
                "verify_iss": False,  # Disable internal issuer validation
            },
            leeway=config.leeway_seconds,
        )

        logger.debug(f"JWT basic validation passed in {time.time() - start_time:.3f}s")

    except jwt.ExpiredSignatureError as e:
        raise JWTValidationError(f"Token expired: {e}") from e
    except jwt.InvalidTokenError as e:
        raise JWTValidationError(f"Invalid token: {e}") from e
    except Exception as e:
        raise JWTValidationError(f"JWT decode failed: {e}") from e

    # Step 2: Strict audience validation
    if config.audience_allowlist is not None:
        aud = claims.get("aud")
        if not aud:
            raise JWTValidationError("Token missing required 'aud' claim")

        # Handle both single audience and audience arrays
        audiences_to_check = aud if isinstance(aud, list) else [aud]

        # At least one audience must be in allowlist
        valid_audiences = [
            a for a in audiences_to_check if a in config.audience_allowlist
        ]
        if not valid_audiences:
            raise JWTValidationError(
                f"No valid audience found. Token audiences: {audiences_to_check}, "
                f"allowed: {sorted(config.audience_allowlist)}"
            )

        logger.debug(f"Audience validation passed: {valid_audiences}")

    # Step 3: Strict issuer validation
    if config.issuer_allowlist is not None:
        iss = claims.get("iss")
        if not iss:
            raise JWTValidationError("Token missing required 'iss' claim")

        if iss not in config.issuer_allowlist:
            raise JWTValidationError(
                f"Invalid issuer '{iss}'. Allowed: {sorted(config.issuer_allowlist)}"
            )

        logger.debug(f"Issuer validation passed: {iss}")

    # Step 4: Enhanced temporal validation
    now = int(time.time())

    # Validate token age (issued-at time)
    iat = claims.get("iat")
    if iat:
        token_age = now - int(iat)
        if token_age > config.max_token_age_seconds:
            raise JWTValidationError(
                f"Token too old: {token_age}s > {config.max_token_age_seconds}s max"
            )
        if token_age < -config.leeway_seconds:  # Token from future
            raise JWTValidationError(f"Token issued in future: iat={iat}, now={now}")

    # Validate not-before with bounded leeway
    nbf = claims.get("nbf")
    if nbf is not None:
        if now + config.leeway_seconds < int(nbf):
            raise JWTValidationError(
                f"Token not yet valid: nbf={nbf}, now={now}, leeway={config.leeway_seconds}"
            )
    elif config.require_nbf:
        raise JWTValidationError("Token missing required 'nbf' claim")

    # Step 5: Additional security validations

    # Validate subject format
    sub = claims.get("sub", "")
    if not sub or len(sub) < 1:
        raise JWTValidationError("Token missing or invalid 'sub' claim")

    # Check for suspicious subject patterns
    if any(
        pattern in sub.lower() for pattern in ["admin", "root", "system", "service"]
    ):
        logger.warning(f"Privileged subject detected: {sub}")

    # Validate JWT ID if required
    if config.require_jti:
        jti = claims.get("jti")
        if not jti:
            raise JWTValidationError("Token missing required 'jti' claim")
        if len(jti) < 8:  # Minimum entropy requirement
            raise JWTValidationError("JWT ID 'jti' too short for security")

    # Step 6: Validate claim structure
    _validate_claim_security(claims)

    logger.info(
        f"Strict JWT validation completed successfully for sub={sub} in {time.time() - start_time:.3f}s"
    )

    return claims


def _validate_claim_security(claims: dict[str, Any]) -> None:
    """Additional security validation for JWT claims."""

    # Check for dangerous scopes
    scope = claims.get("scope", "")
    if isinstance(scope, str):
        dangerous_scopes = ["admin", "root", "superuser", "system:admin"]
        found_dangerous = [s for s in dangerous_scopes if s in scope.lower()]
        if found_dangerous:
            logger.warning(f"Dangerous scopes detected: {found_dangerous}")

    # Validate roles if present
    roles = claims.get("roles", [])
    if isinstance(roles, list):
        privileged_roles = ["admin", "root", "superuser", "system"]
        found_privileged = [
            r for r in roles if isinstance(r, str) and r.lower() in privileged_roles
        ]
        if found_privileged:
            logger.warning(f"Privileged roles detected: {found_privileged}")

    # Check for suspicious custom claims
    suspicious_claims = ["is_admin", "admin_access", "root_access", "system_access"]
    found_suspicious = [claim for claim in suspicious_claims if claims.get(claim)]
    if found_suspicious:
        logger.warning(f"Suspicious claims detected: {found_suspicious}")


def create_production_jwt_config(
    audience_allowlist: set[str],
    issuer_allowlist: set[str],
    leeway_seconds: int = 60,  # Stricter default for production
    max_token_age_seconds: int = 1800,  # 30 minutes for production
    require_jti: bool = True,  # Enable replay protection
) -> StrictJWTConfig:
    """Create production-ready JWT configuration with security defaults."""
    return StrictJWTConfig(
        audience_allowlist=audience_allowlist,
        issuer_allowlist=issuer_allowlist,
        leeway_seconds=leeway_seconds,
        max_token_age_seconds=max_token_age_seconds,
        require_jti=require_jti,
        require_nbf=True,  # Require not-before for production
        algorithms=("RS256", "ES256"),  # Only asymmetric algorithms for production
    )
