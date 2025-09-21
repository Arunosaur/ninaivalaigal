#!/usr/bin/env python3
"""
Test script for mem0 MCP server
"""

import asyncio
import json

from mcp_server import context_start, list_contexts, recall, remember


async def test_mcp_tools():
    """Test MCP server tools"""
    print("Testing mem0 MCP Server Tools...")

    # Test context start
    print("\n1. Testing context_start...")
    result = await context_start("test-mcp-context")
    print(f"Result: {result}")

    # Test remember
    print("\n2. Testing remember...")
    result = await remember("This is a test memory from MCP server", "test-mcp-context")
    print(f"Result: {result}")

    # Test recall
    print("\n3. Testing recall...")
    result = await recall("test-mcp-context")
    print(f"Result: {json.dumps(result, indent=2)}")

    # Test list contexts
    print("\n4. Testing list_contexts...")
    result = await list_contexts()
    print(f"Result: {result}")

    print("\nMCP server tools test completed!")

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
