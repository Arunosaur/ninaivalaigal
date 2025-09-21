"""
RBAC Middleware for FastAPI - Role-Based Access Control Integration
Provides authentication and authorization middleware for the Ninaivalaigal platform
"""

import os
from collections.abc import Callable
from functools import wraps
from typing import Any

import jwt
from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPBearer
from secret_redaction import redact_log_message

from rbac.permissions import Action, Resource, Role, SubjectContext, authorize


class RBACContext:
    """Enhanced RBAC context with user information"""

    def __init__(
        self,
        user_id: int,
        email: str,
        roles: dict[str, str],
        org_id: str | None = None,
        team_ids: set[str] | None = None,
    ):
        self.user_id = user_id
        self.email = email
        self.org_id = org_id or "default"
        self.team_ids = team_ids or set()

        # Convert string roles to Role enums
        self.roles = {}
        for scope, role_str in roles.items():
            try:
                self.roles[scope] = Role[role_str.upper()]
            except (KeyError, AttributeError):
                self.roles[scope] = Role.MEMBER  # Default fallback

    def to_subject_context(self) -> SubjectContext:
        """Convert to RBAC SubjectContext"""
        return SubjectContext(
            org_id=self.org_id, team_ids=self.team_ids, roles=self.roles
        )

    def has_permission(
        self, resource: Resource, action: Action, team_id: str | None = None
    ) -> bool:
        """Check if user has permission for action on resource"""
        subject_ctx = self.to_subject_context()
        return authorize(subject_ctx, resource, action, team_id)

    def get_effective_role(self, team_id: str | None = None) -> str | None:
        """Get the effective role for the user in given context"""
        from rbac.permissions import effective_role

        subject_ctx = self.to_subject_context()
        return effective_role(subject_ctx, team_id)


class RBACMiddleware:
    """FastAPI middleware for RBAC integration"""

    def __init__(self, jwt_secret: str) -> None:
        self.security = HTTPBearer(auto_error=False)
        self.jwt_secret = jwt_secret
        if not self.jwt_secret:
            raise ValueError("NINAIVALAIGAL_JWT_SECRET environment variable required")

    async def extract_rbac_context(self, request: Request) -> RBACContext | None:
        """Extract RBAC context from JWT token - GRACEFUL VERSION"""

        # Enable debug logging if AUTH_DEBUG is set
        debug_mode = os.getenv("AUTH_DEBUG", "").lower() in ("1", "true", "yes")

        try:
            # Get authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                if debug_mode:
                    print(
                        f"[AUTH_DEBUG] No Authorization header for {request.url.path}"
                    )
                return None

            if not auth_header.startswith("Bearer "):
                if debug_mode:
                    print(
                        f"[AUTH_DEBUG] Invalid Authorization header format for "
                        f"{request.url.path}"
                    )
                return None

            token = auth_header.replace("Bearer ", "").strip()
            if not token:
                if debug_mode:
                    print(f"[AUTH_DEBUG] Empty token for {request.url.path}")
                return None

            # Decode JWT token - NO EXCEPTIONS RAISED
            try:
                payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                if debug_mode:
                    print(
                        f"[AUTH_DEBUG] Successfully decoded token for "
                        f"{request.url.path}"
                    )
            except jwt.ExpiredSignatureError:
                if debug_mode:
                    print(f"[AUTH_DEBUG] Token expired for {request.url.path}")
                return None
            except jwt.InvalidTokenError as e:
                if debug_mode:
                    print(
                        f"[AUTH_DEBUG] Invalid token for {request.url.path}: {str(e)}"
                    )
                return None

            # Extract user information - GRACEFUL FALLBACKS
            user_id = payload.get("user_id")
            email = payload.get("email")
            roles = payload.get("roles", {})

            if not user_id or not email:
                if debug_mode:
                    print(
                        f"[AUTH_DEBUG] Missing user_id or email in token for "
                        f"{request.url.path}"
                    )
                return None

            # Extract team and org information
            org_id = roles.get("org_id")
            team_ids = set()

            # Parse team roles
            if "teams" in roles:
                team_ids = set(roles["teams"].keys())

            if debug_mode:
                print(
                    f"[AUTH_DEBUG] Created RBAC context for user {user_id} on "
                    f"{request.url.path}"
                )

            return RBACContext(
                user_id=user_id,
                email=email,
                roles=roles,
                org_id=org_id,
                team_ids=team_ids,
            )

        except Exception as e:
            # Log error without exposing sensitive information - NO EXCEPTIONS RAISED
            error_msg = redact_log_message(f"RBAC context extraction error: {str(e)}")
            print(f"[AUTH_ERROR] {error_msg}")
            if debug_mode:
                print(
                    f"[AUTH_DEBUG] Exception in extract_rbac_context for "
                    f"{request.url.path}: {str(e)}"
                )
            return None

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Middleware execution - GRACEFUL VERSION"""

        # Define public routes that don't require authentication
        PUBLIC_ROUTES = {
            "/health",
            "/health/detailed",
            "/metrics",
            "/auth/login",
            "/auth/signup",
            "/auth/signup/individual",
            "/auth/signup/organization",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

        debug_mode = os.getenv("AUTH_DEBUG", "").lower() in ("1", "true", "yes")

        try:
            # Check if this is a public route
            is_public_route = any(
                request.url.path.startswith(route) for route in PUBLIC_ROUTES
            )

            if debug_mode:
                print(
                    f"[AUTH_DEBUG] Processing {request.method} {request.url.path} "
                    f"(public: {is_public_route})"
                )

            # Extract RBAC context and add to request state - NEVER RAISES EXCEPTIONS
            rbac_context = await self.extract_rbac_context(request)
            request.state.rbac_context = rbac_context

            if debug_mode and rbac_context:
                print(f"[AUTH_DEBUG] RBAC context set for user {rbac_context.user_id}")
            elif debug_mode:
                print("[AUTH_DEBUG] No RBAC context (unauthenticated request)")

            # Continue with request processing
            response = await call_next(request)
            return response

        except Exception as e:
            # Middleware should NEVER crash - log and continue
            error_msg = redact_log_message(f"RBAC middleware error: {str(e)}")
            print(f"[AUTH_ERROR] {error_msg}")

            if debug_mode:
                print(
                    f"[AUTH_DEBUG] Middleware exception for {request.url.path}: "
                    f"{str(e)}"
                )

            # Set empty context and continue
            request.state.rbac_context = None
            response = await call_next(request)
            return response


def require_admin() -> Callable:
    """
    Decorator to require admin role
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            request = kwargs.get("request") or (
                args[0] if args and hasattr(args[0], "headers") else None
            )
            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")

            rbac_context = getattr(request.state, "rbac_context", None)
            if not rbac_context:
                raise HTTPException(status_code=401, detail="Authentication required")

            effective_role = rbac_context.get_effective_role()
            if not effective_role or effective_role != Role.ADMIN:
                raise HTTPException(status_code=403, detail="Admin role required")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_team_admin(func: Callable) -> Callable:
    """Require ADMIN role or ADMINISTER permission on TEAM resource"""
    return require_admin()(func)


def require_org_membership_func(func: Callable) -> Callable:
    """Require ADMIN role or ADMINISTER permission on ORG resource"""
    return require_admin()(func)
