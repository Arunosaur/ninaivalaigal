#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Database Package for ninaivalaigal
Modularized from monolithic database.py for better organization

This addresses external code review feedback:
- Break down monolithic files (database.py 1285 lines → focused modules)
- Improve code organization and maintainability
"""

import importlib
import sys

# Ensure consistent module aliasing when imported as `database` or `server.database`
sys.modules.setdefault("database", sys.modules[__name__])
sys.modules.setdefault("server.database", sys.modules[__name__])

# Import manager and operations
from .manager import DatabaseManager

# Import all models for backward compatibility
from .models import TeamMember  # Team membership model (was TeamMembership)
from .models import (
    Base,
    Context,
    ContextPermission,
    Memory,
    Organization,
    OrganizationRegistration,
    Team,
    TeamBilling,
    TeamSubscription,
    User,
    UserInvitation,
)

# Import RBAC models to register dynamic relationships on User model
# This MUST come after importing User model
try:
    import os

    # Add server directory to path for rbac_models import
    server_path = os.path.dirname(os.path.dirname(__file__))
    if server_path not in sys.path:
        sys.path.insert(0, server_path)
    import rbac_models  # noqa: F401 - imported for side effects
except ImportError:
    pass  # RBAC models optional for basic database operations

from .operations import DatabaseOperations, get_db

# Export all for backward compatibility
__all__ = [
    # Models
    "Base",
    "User",
    "Memory",
    "Organization",
    "Team",
    "TeamBilling",
    "TeamMembership",  # Consolidated model
    "TeamSubscription",
    "Context",
    "ContextPermission",
    "OrganizationRegistration",
    "UserInvitation",
    # Manager and operations
    "DatabaseManager",
    "DatabaseOperations",
    "get_db",
]
