#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Role to Sensitivity Tier Mapping

Defines which sensitivity tiers each role can access according to SPEC-009.
"""

import importlib.util

# Import ContextSensitivity directly to avoid circular dependencies with security.__init__
# Use direct file import to avoid loading security middleware dependencies
import os

# Calculate absolute path to config.py
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, "../../../"))
config_path = os.path.join(_project_root, "server/security/redaction/config.py")

spec = importlib.util.spec_from_file_location("security_redaction_config", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
ContextSensitivity = config_module.ContextSensitivity

from ..permissions import Role

# Role → Sensitivity Tier Mapping (SPEC-009)
# Defines which sensitivity tiers each role can access
ROLE_SENSITIVITY_MATRIX: dict[Role, list[ContextSensitivity]] = {
    # VIEWER: Read-only access to public information only
    Role.VIEWER: [
        ContextSensitivity.PUBLIC,
    ],
    # MEMBER: Access to public and internal information
    Role.MEMBER: [
        ContextSensitivity.PUBLIC,
        ContextSensitivity.INTERNAL,
    ],
    # MAINTAINER: Access to public, internal, and confidential information
    Role.MAINTAINER: [
        ContextSensitivity.PUBLIC,
        ContextSensitivity.INTERNAL,
        ContextSensitivity.CONFIDENTIAL,
    ],
    # ADMIN: Access to public, internal, confidential, and restricted information
    # Cannot access SECRETS tier (requires OWNER)
    Role.ADMIN: [
        ContextSensitivity.PUBLIC,
        ContextSensitivity.INTERNAL,
        ContextSensitivity.CONFIDENTIAL,
        ContextSensitivity.RESTRICTED,
    ],
    # OWNER: Full access to all sensitivity tiers
    Role.OWNER: list(ContextSensitivity),  # All tiers
    # SYSTEM: Full access for automated processes
    Role.SYSTEM: list(ContextSensitivity),  # All tiers
}


def get_allowed_tiers_for_role(role: Role) -> list[ContextSensitivity]:
    """Get list of sensitivity tiers a role can access"""
    return ROLE_SENSITIVITY_MATRIX.get(role, [])


def can_access_tier(role: Role, tier: ContextSensitivity) -> bool:
    """Check if a role can access a specific sensitivity tier

    Note: Compares by value to handle cases where ContextSensitivity
    enum instances come from different import paths.
    """
    allowed_tiers = get_allowed_tiers_for_role(role)
    # Compare by value to handle enum instances from different modules
    tier_value = tier.value if hasattr(tier, "value") else str(tier)
    return any(allowed_tier.value == tier_value for allowed_tier in allowed_tiers)
