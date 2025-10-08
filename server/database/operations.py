"""
Database Operations for ninaivalaigal
LEGACY FILE - REPLACED BY MODULAR STRUCTURE

This file has been refactored into focused modules:
- operations/util_ops.py - Database utilities and helpers
- operations/context_ops.py - Context management operations
- operations/memory_ops.py - Memory management operations
- operations/user_ops.py - User management operations
- operations/organization_ops.py - Organization and team operations
- operations/rbac_ops.py - Role-based access control operations

Import from operations/ module instead of this file.
"""

# Import the new modular operations
from .operations import DatabaseOperations

# Legacy compatibility - maintain get_db function
from .operations.util_ops import get_db

__all__ = ["DatabaseOperations", "get_db"]
