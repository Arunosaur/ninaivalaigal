# mem0 MCP Server Design

## Overview
Convert mem0 from a FastAPI server to a Model Context Protocol (MCP) server for better integration with AI tools like Claude Desktop, VS Code Copilot, and other MCP clients.

## MCP Architecture Benefits
- **Standardized Protocol**: JSON-RPC 2.0 based communication
- **Better AI Integration**: Direct integration with Claude Desktop, VS Code, etc.
- **Three Core Capabilities**: Resources, Tools, and Prompts
- **Transport Options**: stdio, HTTP, or custom transports

## Proposed MCP Interface

### Tools (Functions AI can call)
```python
@mcp.tool()
async def remember(text: str, context: str = None) -> str:
    """Store a memory in the specified context"""
    
@mcp.tool() 
async def recall(context: str = None, query: str = None) -> list[dict]:
    """Retrieve memories from context, optionally filtered by query"""
    
@mcp.tool()
async def context_start(context_name: str) -> str:
    """Start recording to a specific context"""
    
@mcp.tool()
async def context_stop() -> str:
    """Stop active recording"""
    
@mcp.tool()
async def list_contexts() -> list[str]:
    """List all available contexts"""
```

### Resources (Data AI can read)
```python
@mcp.resource("mem0://contexts")
async def list_all_contexts():
    """Provide list of all contexts as a resource"""
    
@mcp.resource("mem0://context/{context_name}")
async def get_context_memories(context_name: str):
    """Provide all memories for a specific context"""
    
@mcp.resource("mem0://recent")
async def get_recent_memories():
    """Provide recently added memories across all contexts"""
```

### Prompts (Templates for common tasks)
```python
@mcp.prompt()
async def analyze_context(context_name: str):
    """Generate a prompt to analyze memories in a context"""
    
@mcp.prompt()
async def summarize_session():
    """Generate a prompt to summarize current session memories"""
```

## Implementation Steps

### 1. Create MCP Server Structure
```python
# mcp_server.py
from mcp.server.fastmcp import FastMCP
from typing import Any, Optional
import asyncio

mcp = FastMCP("mem0")

# Import existing database and logic
from database import MemoryDatabase
from server.main import get_memories, store_memory

db = MemoryDatabase()
```

### 2. Convert Existing Endpoints
- Transform FastAPI endpoints to MCP tools
- Maintain existing database schema and logic
- Add MCP-specific error handling

### 3. Shell Integration Updates
```bash
# Update mem0.zsh to use MCP protocol
# Instead of HTTP requests, use MCP client calls
```

### 4. VS Code Extension Updates
```typescript
// Replace HTTP calls with MCP client integration
// Use VS Code's MCP support (if available) or direct MCP client
```

## Migration Strategy

### Phase 1: Parallel Implementation
- Keep existing FastAPI server running
- Create new MCP server alongside
- Test MCP functionality

### Phase 2: Client Migration
- Update shell integration to use MCP
- Update VS Code extension to use MCP
- Test automatic capture with MCP

### Phase 3: Full Migration
- Deprecate FastAPI server
- Use MCP server as primary interface
- Update documentation

## Benefits of MCP Conversion

1. **Better AI Integration**: Direct protocol support in Claude Desktop, VS Code
2. **Standardized Interface**: Follow MCP conventions for tools/resources/prompts
3. **Improved Discoverability**: AI tools can automatically discover capabilities
4. **Enhanced Security**: MCP's built-in security and approval mechanisms
5. **Future-Proof**: Standard protocol with growing ecosystem support

## Technical Requirements

- **Python MCP SDK**: `mcp[cli]` package
- **Transport**: stdio for local use, HTTP for remote
- **Database**: Keep existing PostgreSQL setup
- **Shell Integration**: Update to use MCP client instead of HTTP
- **VS Code**: Use MCP client library or VS Code MCP support

## Estimated Effort
- **Core MCP Server**: 2-3 days
- **Shell Integration Update**: 1 day  
- **VS Code Extension Update**: 1-2 days
- **Testing & Documentation**: 1 day

**Total**: ~1 week for full conversion
