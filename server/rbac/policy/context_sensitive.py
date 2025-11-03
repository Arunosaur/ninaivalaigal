#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Context-Sensitive RBAC Context

Implements SPEC-009: Context Sensitivity + RBAC Integration
Extends RBACContext with sensitivity tier awareness.
"""

import importlib.util
import os
from typing import Optional

# Import ContextSensitivity directly to avoid circular dependencies
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, "../../../"))
config_path = os.path.join(_project_root, "server/security/redaction/config.py")

spec = importlib.util.spec_from_file_location("security_redaction_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
ContextSensitivity = config_module.ContextSensitivity

from ...rbac_middleware import RBACContext
from ..permissions import Action, Resource, Role
from .mapping import can_access_tier, get_allowed_tiers_for_role


class ContextSensitiveRBACContext(RBACContext):
    """Enhanced RBAC context with context sensitivity awareness

    Extends RBACContext to check permissions with sensitivity tier restrictions.
    Implements SPEC-009 requirement for context sensitivity + RBAC integration.
    """

    def has_permission_with_sensitivity(
        self,
        resource: Resource,
        action: Action,
        context_sensitivity: Optional[ContextSensitivity] = None,
        resource_id: Optional[str] = None,
        team_id: Optional[str] = None,
    ) -> bool:
        """Check permission with context sensitivity awareness

        This method implements the core SPEC-009 requirement:
        1. Check base RBAC permission
        2. If context_sensitivity is provided, verify role can access that tier
        3. Return True only if both checks pass

        Args:
            resource: The resource to check permission for
            action: The action to check permission for
            context_sensitivity: Optional sensitivity tier to check against
            resource_id: Optional resource ID (for future use)
            team_id: Optional team ID for scoped permissions

        Returns:
            True if user has permission and can access the sensitivity tier
            False otherwise
        """
        # Step 1: Check base RBAC permission
        has_base_permission = self.has_permission(resource, action, team_id)
        if not has_base_permission:
            return False

        # Step 2: If sensitivity tier is specified, check tier access
        if context_sensitivity:
            return self._check_sensitivity_access(context_sensitivity)

        # If no sensitivity tier specified, base permission is sufficient
        return True

    def _check_sensitivity_access(self, sensitivity: ContextSensitivity) -> bool:
        """Check if user's role can access the given sensitivity tier

        Uses the effective role from the context to check against
        ROLE_SENSITIVITY_MATRIX.

        Args:
            sensitivity: The sensitivity tier to check access for

        Returns:
            True if user's role can access the tier, False otherwise
        """
        # Get effective role (highest role across all scopes)
        effective_role_str = self.get_effective_role()
        if not effective_role_str:
            return False

        # Convert string role to Role enum
        try:
            if isinstance(effective_role_str, Role):
                role = effective_role_str
            else:
                role = Role[effective_role_str.upper()]
        except (KeyError, AttributeError):
            # Fallback to checking all roles in context
            # If any role has access, allow it
            for scope_role in self.roles.values():
                if can_access_tier(scope_role, sensitivity):
                    return True
            return False

        # Check if role can access the tier
        return can_access_tier(role, sensitivity)

    def get_allowed_sensitivity_tiers(self, team_id: Optional[str] = None) -> list[ContextSensitivity]:
        """Get list of sensitivity tiers the user can access

        Useful for filtering resources by sensitivity tier or displaying
        available options to the user.

        Args:
            team_id: Optional team ID for scoped role lookup

        Returns:
            List of ContextSensitivity tiers the user can access
        """
        effective_role_str = self.get_effective_role(team_id)
        if not effective_role_str:
            return []

        try:
            if isinstance(effective_role_str, Role):
                role = effective_role_str
            else:
                role = Role[effective_role_str.upper()]
        except (KeyError, AttributeError):
            # If role lookup fails, get tiers from highest role in context
            highest_role = max(self.roles.values(), key=lambda r: r.value, default=Role.MEMBER)
            return get_allowed_tiers_for_role(highest_role)

        return get_allowed_tiers_for_role(role)
