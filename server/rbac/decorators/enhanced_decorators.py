#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Enhanced RBAC Decorators with Context Sensitivity Support

Implements SPEC-009: Context Sensitivity + RBAC Integration decorator.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any, Optional

from fastapi import HTTPException, Request

from ...rbac_middleware import get_rbac_context
from ...security.redaction.config import ContextSensitivity
from ..permissions import Action, Resource
from ..policy.context_sensitive import ContextSensitiveRBACContext


def require_permission_with_sensitivity(
    resource: Resource | str,
    action: Action | str,
    sensitivity_param: str = "sensitivity_tier",
    sensitivity_default: Optional[ContextSensitivity] = None,
) -> Callable:
    """Enhanced decorator that enforces RBAC permissions with context sensitivity

    This decorator implements SPEC-009 requirement for context-sensitive permission checks.
    It combines:
    1. Standard RBAC permission check
    2. Context sensitivity tier access check

    Usage:
        @require_permission_with_sensitivity(Resource.MEMORY, Action.READ)
        async def get_memory(request: Request, context_sensitivity: str = "internal"):
            ...

    Or with explicit sensitivity:
        @require_permission_with_sensitivity(
            Resource.CONTEXT,
            Action.READ,
            sensitivity_param="tier"
        )
        async def get_context(request: Request, tier: str = "confidential"):
            ...

    Args:
        resource: The resource to check permission for (Resource enum or string)
        action: The action to check permission for (Action enum or string)
        sensitivity_param: Name of the parameter/query/body field containing sensitivity tier
        sensitivity_default: Default sensitivity tier if not provided (optional)

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Get request object
            request = kwargs.get("request") or (args[0] if args and hasattr(args[0], "headers") else None)
            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")

            # Get RBAC context
            rbac_context = get_rbac_context(request)

            # Convert to context-sensitive context
            if not isinstance(rbac_context, ContextSensitiveRBACContext):
                context_sensitive_context = ContextSensitiveRBACContext(
                    user_id=rbac_context.user_id,
                    email=rbac_context.email,
                    roles=rbac_context.roles,
                    org_id=rbac_context.org_id,
                    team_ids=rbac_context.team_ids,
                )
            else:
                context_sensitive_context = rbac_context

            # Convert resource/action strings to enums if needed
            if isinstance(resource, str):
                resource_enum = getattr(Resource, resource.upper(), None)
                if not resource_enum:
                    raise HTTPException(status_code=500, detail=f"Invalid resource: {resource}")
            else:
                resource_enum = resource

            if isinstance(action, str):
                action_enum = getattr(Action, action.upper(), None)
                if not action_enum:
                    raise HTTPException(status_code=500, detail=f"Invalid action: {action}")
            else:
                action_enum = action

            # Extract sensitivity tier from request
            context_sensitivity: Optional[ContextSensitivity] = None

            # Try to get from kwargs (function parameter)
            if sensitivity_param in kwargs:
                sensitivity_value = kwargs[sensitivity_param]
                if sensitivity_value:
                    if isinstance(sensitivity_value, str):
                        try:
                            context_sensitivity = ContextSensitivity(sensitivity_value.lower())
                        except ValueError:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Invalid sensitivity tier: {sensitivity_value}",
                            )
                    elif isinstance(sensitivity_value, ContextSensitivity):
                        context_sensitivity = sensitivity_value

            # Try to get from query parameters
            elif hasattr(request, "query_params") and sensitivity_param in request.query_params:
                sensitivity_value = request.query_params[sensitivity_param]
                if sensitivity_value:
                    try:
                        context_sensitivity = ContextSensitivity(sensitivity_value.lower())
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid sensitivity tier: {sensitivity_value}",
                        )

            # Try to get from request body (if JSON)
            elif hasattr(request, "json") and request.method in ("POST", "PUT", "PATCH"):
                try:
                    body = await request.json() if hasattr(request, "_json") else None
                    if body and sensitivity_param in body:
                        sensitivity_value = body[sensitivity_param]
                        if sensitivity_value:
                            if isinstance(sensitivity_value, str):
                                context_sensitivity = ContextSensitivity(sensitivity_value.lower())
                            elif isinstance(sensitivity_value, ContextSensitivity):
                                context_sensitivity = sensitivity_value
                except Exception:
                    pass  # Body might not be JSON or already parsed

            # Use default if provided
            if context_sensitivity is None and sensitivity_default:
                context_sensitivity = sensitivity_default

            # Get team_id if available (for scoped permissions)
            team_id = kwargs.get("team_id") or request.query_params.get("team_id")

            # Check permission with sensitivity
            has_permission = context_sensitive_context.has_permission_with_sensitivity(
                resource=resource_enum,
                action=action_enum,
                context_sensitivity=context_sensitivity,
                team_id=team_id,
            )

            if not has_permission:
                if context_sensitivity:
                    raise HTTPException(
                        status_code=403,
                        detail=(
                            f"Permission denied: {action_enum.name} on {resource_enum.name} "
                            f"with sensitivity tier {context_sensitivity.value}"
                        ),
                    )
                else:
                    raise HTTPException(
                        status_code=403,
                        detail=(f"Permission denied: {action_enum.name} on {resource_enum.name}"),
                    )

            # Replace rbac_context in request state with context-sensitive version
            request.state.rbac_context = context_sensitive_context

            return await func(*args, **kwargs)

        return wrapper

    return decorator
