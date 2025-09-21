#!/usr/bin/env python3
"""
Test script to verify memory recording functionality in MCP server
"""

import asyncio
import os
import sys

# Add server directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from mcp_server import context_start, recall, remember


async def test_memory_recording():
    """Test the complete memory recording flow"""

    print("🧪 Testing Memory Recording Flow")
    print("=" * 50)

    # Test 1: Start context recording
    print("\n1. Starting CCTV recording for test context...")
    start_result = await context_start("test-personal-scope")
    print(f"Result: {start_result}")

    # Test 2: Add some memories
    print("\n2. Adding test memories...")

    memory1 = await remember(
        "This is a test memory about project planning", "test-personal-scope"
    )
    print(f"Memory 1: {memory1}")

    memory2 = await remember(
        "Another memory about code review findings", "test-personal-scope"
    )
    print(f"Memory 2: {memory2}")

    memory3 = await remember(
        "Security improvements needed for JWT handling", "test-personal-scope"
    )
    print(f"Memory 3: {memory3}")

    # Test 3: Wait a moment for auto-save
    print("\n3. Waiting for auto-save...")
    await asyncio.sleep(2)

    # Test 4: Recall memories
    print("\n4. Recalling memories from context...")
    memories = await recall("test-personal-scope")

    if memories and not any("error" in str(m) for m in memories):
        print(f"✅ Found {len(memories)} memories:")
        for i, memory in enumerate(memories, 1):
            print(f"   {i}. {memory}")
    else:
        print(f"❌ No memories found or error occurred: {memories}")

    # Test 5: Query-based recall
    print("\n5. Testing query-based recall...")
    security_memories = await recall("test-personal-scope", "security")
    print(f"Security-related memories: {security_memories}")

    print("\n" + "=" * 50)
    print("🏁 Test Complete")


if __name__ == "__main__":
    asyncio.run(test_memory_recording())
