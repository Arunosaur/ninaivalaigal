#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Database Operations Module
Modular breakdown of database operations for better maintainability
"""

from .context_ops import ContextOps as ContextOperations
from .memory_ops import MemoryOperations
from .organization_ops import OrganizationOperations
from .rbac_ops import RBACOperations
from .user_ops import UserOperations
from .util_ops import DatabaseUtilities, get_db
from .vendor_admin import VendorAdminOperations


# Main operations class combining all modules
class DatabaseOperations(
    DatabaseUtilities,
    MemoryOperations,
    UserOperations,
    ContextOperations,
    RBACOperations,
    # VendorAdminOperations,  # Skip - has different initialization
    OrganizationOperations,
):
    """
    Combined database operations class
    Inherits from all specialized operation modules
    """
    
    def __init__(self, config=None, create_tables: bool = False):
        """
        Initialize all database operations.
        
        Args:
            config: Configuration dict or database URL string
            create_tables: Whether to create tables automatically (default: False)
        """
        # Initialize DatabaseUtilities (which inherits from DatabaseManager)
        DatabaseUtilities.__init__(self, config=config, create_tables=create_tables)
        
        # Initialize other operations that accept config
        MemoryOperations.__init__(self, config=config)
        UserOperations.__init__(self, config=config)
        ContextOperations.__init__(self, config=config)
        RBACOperations.__init__(self, config=config)
        OrganizationOperations.__init__(self, config=config)


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
