"""
RBAC Decorators and Audit System

Comprehensive role-based access control decorators with audit logging
and tier-based access enforcement for the Ninaivalaigal platform.
"""

import logging
import os
import sys
from collections.abc import Callable
from enum import Enum
from functools import wraps

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from rbac.permissions import Permission, Resource, Role
except ImportError:
    # Fallback definitions
    class Role(Enum):
        ADMIN = "admin"
        USER = "user"
        VIEWER = "viewer"

    class Permission(Enum):
        READ = "read"
        WRITE = "write"
        DELETE = "delete"
        ADMIN = "admin"

    class Resource(Enum):
        MEMORY = "memory"
        CONTEXT = "context"
        USER = "user"
        ORGANIZATION = "organization"


class AccessDeniedError(Exception):
    """Raised when access is denied by RBAC."""
    pass


class RBACEnforcer:
    """RBAC enforcement engine with audit logging."""

    def __init__(self):
        self.logger = logging.getLogger("rbac.audit")

    def check_permission(
        self,
        user_role: Role,
        required_permission: Permission,
        resource: Resource,
        user_id: str | None = None,
        resource_id: str | None = None
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
            }
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
        resource_id: str | None = None
    ) -> None:
        """Enforce permission check, raise exception if denied."""
        if not self.check_permission(user_role, required_permission, resource, user_id, resource_id):
            raise AccessDeniedError(
                f"Access denied: {user_role.value} lacks {required_permission.value} "
                f"permission for {resource.value}"
            )


# Global enforcer instance
_enforcer = RBACEnforcer()


def require_permission(
    permission: Permission,
    resource: Resource,
    user_role_key: str = "user_role",
    user_id_key: str = "user_id",
    resource_id_key: str | None = None
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
    return require_permission(Permission.READ, Resource.MEMORY)(func)


def memory_write_required(func: Callable) -> Callable:
    """Decorator for memory write access."""
    return require_permission(Permission.WRITE, Resource.MEMORY)(func)


def context_read_required(func: Callable) -> Callable:
    """Decorator for context read access."""
    return require_permission(Permission.READ, Resource.CONTEXT)(func)


def context_write_required(func: Callable) -> Callable:
    """Decorator for context write access."""
    return require_permission(Permission.WRITE, Resource.CONTEXT)(func)


def organization_admin_required(func: Callable) -> Callable:
    """Decorator for organization admin access."""
    return require_permission(Permission.ADMIN, Resource.ORGANIZATION)(func)


# Audit logging functions
def log_access_attempt(
    user_id: str,
    action: str,
    resource: str,
    success: bool,
    details: dict | None = None
):
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
