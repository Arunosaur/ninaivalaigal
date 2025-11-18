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

# Import manager and operations
from .manager import DatabaseManager

# Import all models for backward compatibility
from .models import (
    Base,
    Context,
    ContextPermission,
    Memory,
    Organization,
    OrganizationRegistration,
    Team,
    TeamMember,
    User,
    UserInvitation,
)

# Import security models so they are registered with Base metadata
try:
    # Try relative import first (when lib.database is imported as a package)
    try:
        from ..security import models as _security_models  # noqa: F401
        from ..security.models import AlertEvent, RedactionAudit, SecurityEvent
    except ImportError:
        # Fallback to absolute import (for test environments)
        from lib.security import models as _security_models  # noqa: F401
        from lib.security.models import AlertEvent, RedactionAudit, SecurityEvent
except ImportError:  # pragma: no cover - security models optional in some runtimes
    AlertEvent = None  # type: ignore[assignment]
    RedactionAudit = None  # type: ignore[assignment]
    SecurityEvent = None  # type: ignore[assignment]

# Import RBAC models to register dynamic relationships on User model
# This MUST come after importing User model
try:
    import os
    import sys

    # Add server directory to path for rbac_models import
    server_path = os.path.dirname(os.path.dirname(__file__))
    if server_path not in sys.path:
        sys.path.insert(0, server_path)
    import rbac_models  # noqa: F401 - imported for side effects
except ImportError:
    pass  # RBAC models optional for basic database operations

from .operations import DatabaseOperations, get_db

# US-954: Multi-Replica Support & Load Balancing
try:
    from .connection_router import DatabaseConnectionRouter, create_connection_router
    from .health_routing import HealthRouter, HealthStatus
    from .load_balancer import (
        LoadBalancer,
        LoadBalancingStrategy,
        ReplicaInfo,
        create_load_balancer,
    )
    from .replica_pool_manager import ReplicaPool, ReplicaPoolManager

    HAS_REPLICATION = True
except ImportError:
    # Optional - replication modules may not be available in all environments
    HAS_REPLICATION = False
    LoadBalancer = None
    LoadBalancingStrategy = None
    ReplicaInfo = None
    create_load_balancer = None
    ReplicaPoolManager = None
    ReplicaPool = None
    HealthRouter = None
    HealthStatus = None
    DatabaseConnectionRouter = None
    create_connection_router = None

# Export all for backward compatibility
__all__ = [
    # Models
    "Base",
    "User",
    "Memory",
    "Organization",
    "Team",
    "TeamMember",
    "Context",
    "ContextPermission",
    "OrganizationRegistration",
    "UserInvitation",
    "SecurityEvent",
    "AlertEvent",
    "RedactionAudit",
    # Manager and operations
    "DatabaseManager",
    "DatabaseOperations",
    "get_db",
]

# Add replication exports if available
if HAS_REPLICATION:
    __all__.extend(
        [
            "LoadBalancer",
            "LoadBalancingStrategy",
            "ReplicaInfo",
            "create_load_balancer",
            "ReplicaPoolManager",
            "ReplicaPool",
            "HealthRouter",
            "HealthStatus",
            "DatabaseConnectionRouter",
            "create_connection_router",
        ]
    )
