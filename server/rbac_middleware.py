#!/usr/bin/env python3
"""
RBAC Middleware for FastAPI - Role-Based Access Control Integration
Provides authentication and authorization middleware for the Ninaivalaigal platform
"""

import os
from functools import wraps

import jwt
from fastapi import HTTPException, Request
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

    def get_effective_role(self, team_id: str | None = None) -> Role | None:
        """Get the effective role for the user in given context"""
        from rbac.permissions import effective_role

        subject_ctx = self.to_subject_context()
        return effective_role(subject_ctx, team_id)


class RBACMiddleware:
    """FastAPI middleware for RBAC integration"""

    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
        self.jwt_secret = os.getenv("NINAIVALAIGAL_JWT_SECRET")
        if not self.jwt_secret:
            raise ValueError("NINAIVALAIGAL_JWT_SECRET environment variable required")

    async def extract_rbac_context(self, request: Request) -> RBACContext | None:
        """Extract RBAC context from JWT token"""
        try:
            # Get authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None

            token = auth_header.replace("Bearer ", "")

            # Decode JWT token
            try:
                payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token expired")
            except jwt.InvalidTokenError:
                raise HTTPException(status_code=401, detail="Invalid token")

            # Extract user information
            user_id = payload.get("user_id")
            email = payload.get("email")
            roles = payload.get("roles", {})

            if not user_id or not email:
                raise HTTPException(status_code=401, detail="Invalid token payload")

            # Extract team and org information
            org_id = roles.get("org_id")
            team_ids = set()

            # Parse team roles
            if "teams" in roles:
                team_ids = set(roles["teams"].keys())

            return RBACContext(
                user_id=user_id,
                email=email,
                roles=roles,
                org_id=org_id,
                team_ids=team_ids,
            )

        except HTTPException:
            raise
        except Exception as e:
            # Log error without exposing sensitive information
            error_msg = redact_log_message(f"RBAC context extraction error: {str(e)}")
            print(error_msg)
            return None

    async def __call__(self, request: Request, call_next):
        """Middleware execution"""
        # Extract RBAC context and add to request state
        rbac_context = await self.extract_rbac_context(request)
        request.state.rbac_context = rbac_context

        # Continue with request processing
        response = await call_next(request)
        return response


def require_permission(
    resource: Resource, action: Action, scope_param: str | None = None
):
    """
    Decorator to require specific permission for endpoint access

    Args:
        resource: The resource being accessed
        action: The action being performed
        scope_param: Parameter name containing scope ID (e.g., 'team_id')
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # Try to find request in kwargs
                request = kwargs.get("request")

            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")

            # Get RBAC context
            rbac_context = getattr(request.state, "rbac_context", None)
            if not rbac_context:
                raise HTTPException(status_code=401, detail="Authentication required")

            # Determine scope if specified
            scope_id = None
            if scope_param and scope_param in kwargs:
                scope_id = str(kwargs[scope_param])

            # Check permission
            if not rbac_context.has_permission(resource, action, scope_id):
                # Log permission denial
                log_msg = redact_log_message(
                    f"Permission denied: user {rbac_context.user_id} "
                    f"attempted {action.name} on {resource.name}"
                )
                print(log_msg)

                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions: {action.name} on {resource.name}",
                )

            # Log successful access
            log_msg = redact_log_message(
                f"Permission granted: user {rbac_context.user_id} "
                f"performed {action.name} on {resource.name}"
            )
            print(log_msg)

            result = await func(*args, **kwargs)
            return result

        return wrapper

    return decorator


def require_role(min_role: Role, scope_param: str | None = None):
    """
    Decorator to require minimum role level for endpoint access

    Args:
        min_role: Minimum role required
        scope_param: Parameter name containing scope ID (e.g., 'team_id')
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request") or (
                args[0] if args and hasattr(args[0], "headers") else None
            )
            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")

            rbac_context = getattr(request.state, "rbac_context", None)
            if not rbac_context:
                raise HTTPException(status_code=401, detail="Authentication required")

            # Determine scope if specified
            scope_id = None
            if scope_param and scope_param in kwargs:
                scope_id = str(kwargs[scope_param])

            # Check role level
            effective_role = rbac_context.get_effective_role(scope_id)
            if not effective_role:
                raise HTTPException(status_code=403, detail="No role assigned")

            from rbac.permissions import ROLE_PRECEDENCE

            if ROLE_PRECEDENCE.index(effective_role) < ROLE_PRECEDENCE.index(min_role):
                raise HTTPException(
                    status_code=403, detail=f"Minimum role required: {min_role.name}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def get_rbac_context(request: Request) -> RBACContext | None:
    """Get RBAC context from request"""
    return getattr(request.state, "rbac_context", None)


def require_authentication(func):
    """Decorator to require authentication (any valid user)"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find the request object
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        if not request:
            request = kwargs.get("request")

        if not request:
            raise HTTPException(status_code=500, detail="Request object not found")

        # Check authentication
        rbac_context = getattr(request.state, "rbac_context", None)
        if not rbac_context:
            raise HTTPException(status_code=401, detail="Authentication required")

        return await func(*args, **kwargs)

    return wrapper


# Global middleware instance
rbac_middleware = RBACMiddleware()


# Convenience functions for common permission checks
def require_context_read(func):
    """Require READ permission on CONTEXT resource"""
    return require_permission(Resource.CONTEXT, Action.READ)(func)


def require_context_write(func):
    """Require CREATE/UPDATE permission on CONTEXT resource"""
    return require_permission(Resource.CONTEXT, Action.UPDATE)(func)


def require_memory_read(func):
    """Require READ permission on MEMORY resource"""
    return require_permission(Resource.MEMORY, Action.READ)(func)


def require_memory_write(func):
    """Require CREATE/UPDATE permission on MEMORY resource"""
    return require_permission(Resource.MEMORY, Action.UPDATE)(func)


def require_team_admin(func):
    """Require ADMIN role or ADMINISTER permission on TEAM resource"""
    return require_permission(Resource.TEAM, Action.ADMINISTER)(func)


def require_org_admin(func):
    """Require ADMIN role or ADMINISTER permission on ORG resource"""
    return require_permission(Resource.ORG, Action.ADMINISTER)(func)
