#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
MCP Server Runner for mem0
Runs the MCP server with proper stdio transport
"""

import asyncio

from mcp_server import mcp

if __name__ == "__main__":
    # Run MCP server with stdio transport (default for MCP)
    asyncio.run(mcp.run())
