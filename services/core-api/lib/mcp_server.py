#!/opt/homebrew/anaconda3/bin/python
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Ninaivalaigal MCP Server - Model Context Protocol implementation
Provides e^M (exponential Memory) management capabilities as MCP tools, resources, and prompts

This is the legacy monolithic server file. The modular version is available in server/mcp/
"""

# Import the modular MCP server
from mcp import mcp

# For backward compatibility, expose the server
if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
