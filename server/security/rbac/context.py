"""
JWT Claims Resolver and Subject Context

Provides JWT token parsing, signature verification, and subject context
extraction for RBAC integration in the Ninaivalaigal platform.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

import jwt


class Role(Enum):
    """User roles in the system."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


@dataclass
class SubjectContext:
    """Subject context extracted from JWT claims."""

    user_id: str
    email: str | None = None
    role: Role | None = None
    organization_id: str | None = None
    team_id: str | None = None
    permissions: list | None = None
    tier: str | None = None


class JWTClaimsResolver:
    """Resolves JWT claims and extracts subject context."""

    def __init__(
        self,
        secret_key: str | None = None,
        verify_signature: bool = True,
        algorithm: str = "HS256",
    ):
        self.secret_key = secret_key or os.getenv("NINAIVALAIGAL_JWT_SECRET")
        self.verify_signature = verify_signature and bool(
            os.getenv("NINAIVALAIGAL_JWT_VERIFY", "true").lower() == "true"
        )
        self.algorithm = algorithm
        self.logger = logging.getLogger("jwt.resolver")

    def resolve_claims(self, token: str) -> dict[str, Any]:
        """Resolve JWT claims with optional signature verification."""
        try:
            if self.verify_signature and self.secret_key:
                # Verify signature
                claims = jwt.decode(
                    token,
                    self.secret_key,
                    algorithms=[self.algorithm],
                    options={"verify_exp": True},
                )
                self.logger.info("JWT signature verified successfully")
            else:
                # Unverified parsing for development/testing
                claims = jwt.decode(
                    token, options={"verify_signature": False, "verify_exp": False}
                )
                self.logger.warning("JWT parsed without signature verification")

            return claims

        except jwt.ExpiredSignatureError:
            self.logger.error("JWT token has expired")
            raise ValueError("Token has expired")

        except jwt.InvalidTokenError as e:
            self.logger.error(f"Invalid JWT token: {e}")
            raise ValueError(f"Invalid token: {e}")

        except Exception as e:
            self.logger.error(f"JWT parsing error: {e}")
            raise ValueError(f"Token parsing failed: {e}")

    def extract_subject_context(self, token: str) -> SubjectContext:
        """Extract subject context from JWT token."""
        claims = self.resolve_claims(token)

        # Extract user ID (required)
        user_id = claims.get("sub") or claims.get("user_id")
        if not user_id:
            raise ValueError("User ID not found in token claims")

        # Extract role
        role_str = claims.get("role", "user")
        try:
            role = Role(role_str) if role_str else Role.USER
        except ValueError:
            self.logger.warning(f"Invalid role '{role_str}', defaulting to USER")
            role = Role.USER

        # Extract organization and team context
        organization_id = claims.get("org_id") or claims.get("organization_id")
        team_id = claims.get("team_id")

        # Extract permissions
        permissions = claims.get("permissions", [])
        if isinstance(permissions, str):
            permissions = permissions.split(",")

        # Extract tier information
        tier = claims.get("tier", "standard")

        return SubjectContext(
            user_id=str(user_id),
            email=claims.get("email"),
            role=role,
            organization_id=organization_id,
            team_id=team_id,
            permissions=permissions,
            tier=tier,
        )


# Global resolver instance
_resolver = JWTClaimsResolver()


def get_subject_ctx(token: str) -> SubjectContext:
    """Global function to get subject context from JWT token."""
    return _resolver.extract_subject_context(token)


def resolve_jwt_claims(token: str) -> dict[str, Any]:
    """Global function to resolve JWT claims."""
    return _resolver.resolve_claims(token)


def extract_user_context(token: str) -> dict[str, Any]:
    """Extract user context for backward compatibility."""
    context = get_subject_ctx(token)
    return {
        "user_id": context.user_id,
        "email": context.email,
        "role": context.role.value if context.role else "user",
        "organization_id": context.organization_id,
        "team_id": context.team_id,
        "permissions": context.permissions or [],
        "tier": context.tier,
    }


def validate_token_signature(token: str, secret_key: str | None = None) -> bool:
    """Validate JWT token signature."""
    try:
        resolver = JWTClaimsResolver(secret_key=secret_key, verify_signature=True)
        resolver.resolve_claims(token)
        return True
    except Exception:
        return False


def get_token_expiry(token: str) -> int | None:
    """Get token expiry timestamp."""
    try:
        claims = jwt.decode(token, options={"verify_signature": False})
        return claims.get("exp")
    except Exception:
        return None


def is_token_expired(token: str) -> bool:
    """Check if token is expired."""
    try:
        expiry = get_token_expiry(token)
        if not expiry:
            return False

        import time

        return time.time() > expiry
    except Exception:
        return True


def create_test_context(
    user_id: str = "test_user",
    role: Role = Role.USER,
    organization_id: str | None = None,
    team_id: str | None = None,
) -> SubjectContext:
    """Create test subject context for development."""
    return SubjectContext(
        user_id=user_id,
        email=f"{user_id}@example.com",
        role=role,
        organization_id=organization_id,
        team_id=team_id,
        permissions=["read", "write"] if role != Role.VIEWER else ["read"],
        tier="standard",
    )
