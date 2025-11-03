#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
RBAC Decorators and Audit System

Comprehensive role-based access control decorators with audit logging
and tier-based access enforcement for the Ninaivalaigal platform.
"""

import importlib.util
import inspect
import logging
import os
import sys
import time
from collections.abc import Callable
from enum import Enum
from functools import wraps
from typing import Any

from fastapi import Depends, HTTPException, Request, status

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from rbac.permissions import Permission, Resource, Role
except ImportError:
    # Fallback definitions
    class Role(Enum):
        """Role class."""

        ADMIN = "admin"
        USER = "user"
        VIEWER = "viewer"

    class Permission(Enum):
        """Permission class."""

        READ = "read"
        WRITE = "write"
        DELETE = "delete"
        ADMIN = "admin"

    class Resource(Enum):
        """Resource class."""

        MEMORY = "memory"
        CONTEXT = "context"
        USER = "user"
        ORGANIZATION = "organization"


try:
    from rbac.policy import expand_roles
except ImportError:  # pragma: no cover - fallback for isolated test runs
    _fallback_policy_path = os.path.join(project_root, "rbac", "policy.py")

    if os.path.isfile(_fallback_policy_path):
        _spec = importlib.util.spec_from_file_location("_rbac_policy_fallback", _fallback_policy_path)
        _module = importlib.util.module_from_spec(_spec) if _spec and _spec.loader else None
        if _module and _spec.loader:
            _spec.loader.exec_module(_module)
            expand_roles = _module.expand_roles  # type: ignore[attr-defined]
        else:

            def expand_roles(roles):
                """Fallback role expansion when policy module spec cannot be loaded."""

                return sorted(set(roles))

    else:

        def expand_roles(roles):
            """Fallback role expansion when policy module is unavailable."""

            return sorted(set(roles))


from .metrics import rbac_denials_total
from .subject_ctx import SubjectContext


class AccessDeniedError(Exception):
    """Raised when access is denied by RBAC."""


class RBACEnforcer:
    """RBAC enforcement engine with audit logging."""

    def __init__(self):
        """Initialize instance."""
        self.logger = logging.getLogger("rbac.audit")

    def check_permission(
        self,
        user_role: Role,
        required_permission: Permission,
        resource: Resource,
        user_id: str | None = None,
        resource_id: str | None = None,
    ) -> bool:
        """Check if user has required permission for resource."""

        # Admin has all permissions
        if user_role == Role.ADMIN:
            return True

        # Define permission matrix
        permission_matrix = {
            Role.USER: {
                Resource.MEMORY: [Permission.READ, Permission.WRITE],
                Resource.CONTEXT: [Permission.READ, Permission.WRITE],
                Resource.USER: [Permission.READ],
            },
            Role.VIEWER: {
                Resource.MEMORY: [Permission.READ],
                Resource.CONTEXT: [Permission.READ],
                Resource.USER: [Permission.READ],
            },
        }

        allowed_permissions = permission_matrix.get(user_role, {}).get(resource, [])
        has_permission = required_permission in allowed_permissions

        # Audit log
        self.logger.info(
            f"RBAC Check: user_role={user_role.value}, permission={required_permission.value}, "
            f"resource={resource.value}, allowed={has_permission}, user_id={user_id}, "
            f"resource_id={resource_id}"
        )

        if not has_permission:
            self.logger.warning(
                f"Access DENIED: user_role={user_role.value}, permission={required_permission.value}, "
                f"resource={resource.value}, user_id={user_id}, resource_id={resource_id}"
            )

        return has_permission

    def enforce_permission(
        self,
        user_role: Role,
        required_permission: Permission,
        resource: Resource,
        user_id: str | None = None,
        resource_id: str | None = None,
    ) -> None:
        """Enforce permission check, raise exception if denied."""
        if not self.check_permission(user_role, required_permission, resource, user_id, resource_id):
            raise AccessDeniedError(
                f"Access denied: {user_role.value} lacks {required_permission.value} "
                f"permission for {resource.value}"
            )


# Global enforcer instance
_enforcer = RBACEnforcer()


def _legacy_require_permission(
    permission: Permission,
    resource: Resource,
    user_role_key: str = "user_role",
    user_id_key: str = "user_id",
    resource_id_key: str | None = None,
):
    """Decorator to require specific permission for resource access."""

    def decorator(func: Callable) -> Callable:

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user context from kwargs
            user_role = kwargs.get(user_role_key)
            user_id = kwargs.get(user_id_key)
            resource_id = kwargs.get(resource_id_key) if resource_id_key else None

            if not user_role:
                raise AccessDeniedError("User role not provided")

            # Convert string role to enum if needed
            if isinstance(user_role, str):
                try:
                    user_role = Role(user_role)
                except ValueError:
                    raise AccessDeniedError(f"Invalid user role: {user_role}")

            # Enforce permission
            _enforcer.enforce_permission(user_role, permission, resource, user_id, resource_id)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(required_role: Role):
    """Decorator to require specific role."""

    def decorator(func: Callable) -> Callable:

        @wraps(func)
        def wrapper(*args, **kwargs):
            user_role = kwargs.get("user_role")

            if not user_role:
                raise AccessDeniedError("User role not provided")

            if isinstance(user_role, str):
                try:
                    user_role = Role(user_role)
                except ValueError:
                    raise AccessDeniedError(f"Invalid user role: {user_role}")

            if user_role != required_role and user_role != Role.ADMIN:
                raise AccessDeniedError(f"Required role: {required_role.value}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(func: Callable) -> Callable:
    """Decorator to require admin role."""
    return require_role(Role.ADMIN)(func)


def authenticated_required(func: Callable) -> Callable:
    """Decorator to require any authenticated user."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = kwargs.get("user_id")
        if not user_id:
            raise AccessDeniedError("Authentication required")
        return func(*args, **kwargs)

    return wrapper


# Resource-specific decorators
def memory_read_required(func: Callable) -> Callable:
    """Decorator for memory read access."""
    return _legacy_require_permission(Permission.READ, Resource.MEMORY)(func)


def memory_write_required(func: Callable) -> Callable:
    """Decorator for memory write access."""
    return _legacy_require_permission(Permission.WRITE, Resource.MEMORY)(func)


def context_read_required(func: Callable) -> Callable:
    """Decorator for context read access."""
    return _legacy_require_permission(Permission.READ, Resource.CONTEXT)(func)


def context_write_required(func: Callable) -> Callable:
    """Decorator for context write access."""
    return _legacy_require_permission(Permission.WRITE, Resource.CONTEXT)(func)


def organization_admin_required(func: Callable) -> Callable:
    """Decorator for organization admin access."""
    return _legacy_require_permission(Permission.ADMIN, Resource.ORGANIZATION)(func)


# Audit logging functions
def log_access_attempt(user_id: str, action: str, resource: str, success: bool, details: dict | None = None):
    """Log access attempt for audit trail."""
    logger = logging.getLogger("rbac.audit")

    log_data = {
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "success": success,
        "timestamp": None,  # Will be added by logging framework
    }

    if details:
        log_data.update(details)

    if success:
        logger.info(f"Access granted: {log_data}")
    else:
        logger.warning(f"Access denied: {log_data}")


def get_enforcer() -> RBACEnforcer:
    """Get the global RBAC enforcer instance."""
    return _enforcer


_jwt_resolver: Callable[[str], SubjectContext] | None = None


def set_jwt_resolver(resolver: Callable[[str], SubjectContext] | None) -> None:
    """Register the callable used to turn bearer tokens into subject context."""

    global _jwt_resolver
    _jwt_resolver = resolver


def _coerce_permission(permission: Permission | str) -> Permission:
    """Translate string permission names to Permission enums when available."""

    if isinstance(permission, Permission):
        return permission
    if isinstance(permission, str):
        try:
            return Permission[permission.upper()]
        except KeyError as exc:  # pragma: no cover - defensive guardrail
            raise AccessDeniedError(f"Unknown permission '{permission}'") from exc
    raise TypeError("permission must be Permission or str")


def _coerce_resource(resource: Resource | str) -> Resource:
    """Translate string resource names to Resource enums when available."""

    if isinstance(resource, Resource):
        return resource
    if isinstance(resource, str):
        try:
            return Resource[resource.upper()]
        except KeyError as exc:  # pragma: no cover - defensive guardrail
            raise AccessDeniedError(f"Unknown resource '{resource}'") from exc
    raise TypeError("resource must be Resource or str")


def _normalize_permission_name(permission: Permission | str) -> str:
    """Normalize permission inputs into canonical string labels."""

    if isinstance(permission, Permission):
        return str(permission.value)
    if isinstance(permission, str):
        return permission
    raise TypeError("permission must be Permission or str")


def _resolve_subject_context(request: Request) -> SubjectContext:
    """Run the configured resolver against the bearer token on the request."""

    if _jwt_resolver is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="JWT resolver not configured")

    cached = getattr(request.state, "_rbac_subject_ctx", None)
    if isinstance(cached, SubjectContext):
        return cached

    header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not header or not header.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    resolver = _jwt_resolver
    try:
        if hasattr(resolver, "resolve"):
            ctx = resolver.resolve(token)  # type: ignore[attr-defined]
        else:
            ctx = resolver(token)  # type: ignore[operator]
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - hardened boundary
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if not isinstance(ctx, SubjectContext):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid resolver output")

    if not ctx.user_id or not ctx.claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    exp_claim = ctx.claims.get("exp") if isinstance(ctx.claims, dict) else None
    if isinstance(exp_claim, (int, float)) and exp_claim < time.time():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    setattr(request.state, "_rbac_subject_ctx", ctx)
    return ctx


def _ensure_permission(request: Request, permission_name: str, *, allow_inheritance: bool) -> SubjectContext:
    """Validate the permission is present on the subject, raising HTTP errors on failure."""

    ctx = _resolve_subject_context(request)
    roles = ctx.roles or []
    effective_roles = expand_roles(roles) if allow_inheritance else sorted(set(roles))

    if permission_name not in effective_roles:
        rbac_denials_total.labels(permission=permission_name).inc()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    return ctx


def require_permission(  # type: ignore[override] - legacy compatibility
    permission: Permission | str,
    resource: Resource | str | None = None,
    *,
    user_role_key: str = "user_role",
    user_id_key: str = "user_id",
    resource_id_key: str | None = None,
    allow_inheritance: bool = True,
):
    """Hybrid decorator supporting both legacy RBAC paths and JWT-aware enforcement."""

    if resource is not None:
        perm_enum = _coerce_permission(permission)
        res_enum = _coerce_resource(resource)
        return _legacy_require_permission(
            perm_enum,
            res_enum,
            user_role_key=user_role_key,
            user_id_key=user_id_key,
            resource_id_key=resource_id_key,
        )

    perm_name = _normalize_permission_name(permission)

    def decorator(func: Callable) -> Callable:
        signature = inspect.signature(func)
        accepts_subject_ctx = any(
            param.kind is inspect.Parameter.VAR_KEYWORD
            or (
                param.name == "subject_ctx"
                and param.kind
                in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                )
            )
            for param in signature.parameters.values()
        )

        async def _subject_ctx_dependency(request: Request) -> SubjectContext:
            return _ensure_permission(request, perm_name, allow_inheritance=allow_inheritance)

        injection_param = inspect.Parameter(
            "_rbac_subject_ctx",
            inspect.Parameter.KEYWORD_ONLY,
            default=Depends(_subject_ctx_dependency),
            annotation=SubjectContext,
        )
        new_signature = signature.replace(parameters=[*signature.parameters.values(), injection_param])

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any):
                ctx = kwargs.pop("_rbac_subject_ctx", None)
                if not isinstance(ctx, SubjectContext):
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Subject context unavailable",
                    )

                if accepts_subject_ctx and "subject_ctx" not in kwargs:
                    kwargs["subject_ctx"] = ctx
                return await func(*args, **kwargs)

            async_wrapper.__signature__ = new_signature  # type: ignore[attr-defined]
            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any):
            ctx = kwargs.pop("_rbac_subject_ctx", None)
            if not isinstance(ctx, SubjectContext):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Subject context unavailable",
                )

            if accepts_subject_ctx and "subject_ctx" not in kwargs:
                kwargs["subject_ctx"] = ctx
            return func(*args, **kwargs)

        sync_wrapper.__signature__ = new_signature  # type: ignore[attr-defined]
        return sync_wrapper

    return decorator
