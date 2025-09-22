"""
MCP Package for ninaivalaigal
Modularized from monolithic mcp_server.py for better organization

This addresses external code review feedback:
- Break down monolithic files (mcp_server.py 929 lines → focused modules)
- Improve code organization and maintainability
"""

# Import all components for backward compatibility
from .server import mcp, get_user_from_jwt
from .tools import *
from .resources import *
from .prompts import *

# Export all for backward compatibility
__all__ = [
    "mcp",
    "get_user_from_jwt",
    # Tools will be auto-registered with mcp server
    # Resources will be auto-registered with mcp server
    # Prompts will be auto-registered with mcp server
]
