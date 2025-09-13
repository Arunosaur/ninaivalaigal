#!/usr/bin/env python3
"""
Basic MCP Server Test
Tests core MCP server functionality and tool availability
"""

import json
import subprocess
import time
import os
import sys

def test_mcp_server_initialization():
    """Test that MCP server starts and responds to initialization"""
    server_path = "/Users/asrajag/Workspace/mem0/server/mcp_server.py"
    
    # Start MCP server process
    process = subprocess.Popen(
        [sys.executable, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/Users/asrajag/Workspace/mem0/server"
    )
    
    try:
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send request
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response with timeout
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            
            if "result" in response:
                print("✅ MCP server initialization successful")
                print(f"Server capabilities: {response['result'].get('capabilities', {})}")
                return True
            else:
                print(f"❌ Initialization failed: {response}")
                return False
        else:
            print("❌ No response from server")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

def test_mcp_tools_list():
    """Test that MCP server returns available tools"""
    server_path = "/Users/asrajag/Workspace/mem0/server/mcp_server.py"
    
    process = subprocess.Popen(
        [sys.executable, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/Users/asrajag/Workspace/mem0/server"
    )
    
    try:
        # Initialize first
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read init response
        init_response = process.stdout.readline()
        
        # Send tools/list request
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        # Read tools response
        tools_response_line = process.stdout.readline()
        if tools_response_line:
            tools_response = json.loads(tools_response_line.strip())
            
            if "result" in tools_response and "tools" in tools_response["result"]:
                tools = tools_response["result"]["tools"]
                print(f"✅ Found {len(tools)} MCP tools:")
                for tool in tools:
                    print(f"  - {tool['name']}: {tool.get('description', 'No description')}")
                
                # Check for expected tools
                tool_names = [tool['name'] for tool in tools]
                expected_tools = [
                    "context_start",
                    "remember",
                    "recall",
                    "list_contexts",
                    "enhance_ai_prompt_tool"
                ]
                
                missing_tools = [tool for tool in expected_tools if tool not in tool_names]
                if missing_tools:
                    print(f"⚠️  Missing expected tools: {missing_tools}")
                else:
                    print("✅ All expected tools are available")
                
                return True
            else:
                print(f"❌ Invalid tools response: {tools_response}")
                return False
        else:
            print("❌ No tools response received")
            return False
            
    except Exception as e:
        print(f"❌ Tools test failed: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

def test_basic_memory_operation():
    """Test basic memory operations via MCP"""
    server_path = "/Users/asrajag/Workspace/mem0/server/mcp_server.py"
    
    process = subprocess.Popen(
        [sys.executable, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/Users/asrajag/Workspace/mem0/server"
    )
    
    try:
        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        process.stdout.readline()  # Read init response
        
        # Test context_start
        context_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "context_start",
                "arguments": {
                    "context_name": "test-context"
                }
            }
        }
        
        process.stdin.write(json.dumps(context_request) + "\n")
        process.stdin.flush()
        
        context_response_line = process.stdout.readline()
        if context_response_line:
            context_response = json.loads(context_response_line.strip())
            if "result" in context_response:
                print("✅ Context start successful")
                return True
            else:
                print(f"❌ Context start failed: {context_response}")
                return False
        else:
            print("❌ No context response received")
            return False
            
    except Exception as e:
        print(f"❌ Memory operation test failed: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

def main():
    """Run all MCP server tests"""
    print("🧪 Testing MCP Server Functionality\n")
    
    tests = [
        ("MCP Server Initialization", test_mcp_server_initialization),
        ("MCP Tools List", test_mcp_tools_list),
        ("Basic Memory Operation", test_basic_memory_operation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        result = test_func()
        results.append((test_name, result))
        print()
    
    # Summary
    print("📊 Test Results:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! MCP server is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit(main())
