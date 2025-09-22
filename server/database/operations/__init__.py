"""
Database Operations Module
Modular breakdown of database operations for better maintainability
"""

from .context_ops import ContextOperations
from .memory_ops import MemoryOperations
from .organization_ops import OrganizationOperations
from .rbac_ops import RBACOperations
from .user_ops import UserOperations
from .util_ops import DatabaseUtilities, get_db


# Main operations class combining all modules
class DatabaseOperations(
    DatabaseUtilities,
    MemoryOperations,
    UserOperations,
    ContextOperations,
    RBACOperations,
    OrganizationOperations,
):
    """
    Combined database operations class
    Inherits from all specialized operation modules
    """

    pass


__all__ = [
    "DatabaseOperations",
    "DatabaseUtilities",
    "MemoryOperations",
    "UserOperations",
    "ContextOperations",
    "RBACOperations",
    "OrganizationOperations",
    "get_db",
]
