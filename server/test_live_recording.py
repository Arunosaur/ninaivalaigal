#!/usr/bin/env python3
"""
Test script to verify live auto-recording functionality
"""

import asyncio
import sys
import os

# Add server directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_server import remember, recall, context_start, auto_record_tool_usage
from database import DatabaseManager
from auto_recording import get_auto_recorder

async def test_live_recording():
    """Test live recording with tool usage"""
    
    print("🧪 Testing Live Auto-Recording")
    print("=" * 50)
    
    # Test 1: Start context recording
    print("\n1. Starting CCTV recording...")
    start_result = await context_start("live-test-context")
    print(f"Result: {start_result}")
    
    # Test 2: Simulate tool usage
    print("\n2. Simulating tool usage...")
    await auto_record_tool_usage("test_tool", "User asked about project status")
    await auto_record_tool_usage("another_tool", "User requested code review")
    
    # Test 3: Add explicit memory
    print("\n3. Adding explicit memory...")
    memory_result = await remember("This is a manually added memory", "live-test-context")
    print(f"Memory result: {memory_result}")
    
    # Test 4: Use recall (which should auto-record)
    print("\n4. Using recall (should auto-record)...")
    memories = await recall("live-test-context")
    print(f"Found {len(memories)} memories")
    
    # Test 5: Wait for auto-save
    print("\n5. Waiting for auto-save...")
    await asyncio.sleep(3)
    
    # Test 6: Final recall to see all recorded interactions
    print("\n6. Final recall to see all interactions...")
    final_memories = await recall("live-test-context")
    
    if final_memories and not any("error" in str(m) for m in final_memories):
        print(f"✅ Total memories found: {len(final_memories)}")
        for i, memory in enumerate(final_memories, 1):
            content = memory.get('data', {}).get('text', str(memory))[:100]
            print(f"   {i}. {content}...")
    else:
        print(f"❌ No memories or error: {final_memories}")
    
    print("\n" + "=" * 50)
    print("🏁 Live Recording Test Complete")

if __name__ == "__main__":
    asyncio.run(test_live_recording())
