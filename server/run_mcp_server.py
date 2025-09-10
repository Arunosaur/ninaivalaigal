#!/usr/bin/env python3
"""
MCP Server Runner for mem0
Runs the MCP server with proper stdio transport
"""

import asyncio
from mcp_server import mcp

if __name__ == "__main__":
    # Run MCP server with stdio transport (default for MCP)
    asyncio.run(mcp.run())
