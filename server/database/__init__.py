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
from .operations import DatabaseOperations, get_db

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
    # Manager and operations
    "DatabaseManager",
    "DatabaseOperations",
    "get_db",
]
