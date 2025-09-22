#!/opt/homebrew/anaconda3/bin/python
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