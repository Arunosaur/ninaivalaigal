# VS Code MCP Server Troubleshooting Guide

## Issue: "spawn python ENOENT" Error

The wrapper script approach is not resolving the VS Code MCP startup issue. Here are alternative solutions:

### Solution 1: Direct Python Path (Recommended)

Use the system Python path that VS Code can find:

```json
{
  "mcp.servers": {
    "mem0": {
      "command": "/usr/bin/python3",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "cwd": "/Users/asrajag/Workspace/mem0",
      "env": {
        "MEM0_JWT_SECRET": "FcbdlNhk9AlKmeGjDNVmZK3CK12UZdQRrdaG1i8xesk",
        "MEM0_DATABASE_URL": "postgresql://mem0user:mem0pass@localhost:5432/mem0db",
        "PYTHONPATH": "/Users/asrajag/Workspace/mem0/server"
      }
    }
  }
}
```

### Solution 2: Anaconda Python with Full Path

If you need Anaconda Python specifically:

```json
{
  "mcp.servers": {
    "mem0": {
      "command": "/opt/homebrew/anaconda3/bin/python3.11",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "cwd": "/Users/asrajag/Workspace/mem0",
      "env": {
        "MEM0_JWT_SECRET": "FcbdlNhk9AlKmeGjDNVmZK3CK12UZdQRrdaG1i8xesk",
        "MEM0_DATABASE_URL": "postgresql://mem0user:mem0pass@localhost:5432/mem0db",
        "PYTHONPATH": "/Users/asrajag/Workspace/mem0/server"
      }
    }
  }
}
```

### Solution 3: Environment-Based Configuration

Store secrets in environment variables and reference them:

```bash
# Add to ~/.zshrc or ~/.bashrc
export MEM0_JWT_SECRET="FcbdlNhk9AlKmeGjDNVmZK3CK12UZdQRrdaG1i8xesk"
export MEM0_DATABASE_URL="postgresql://mem0user:mem0pass@localhost:5432/mem0db"
```

Then use simplified VS Code config:

```json
{
  "mcp.servers": {
    "mem0": {
      "command": "/usr/bin/python3",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "cwd": "/Users/asrajag/Workspace/mem0",
      "env": {
        "PYTHONPATH": "/Users/asrajag/Workspace/mem0/server"
      }
    }
  }
}
```

## Debugging Steps

1. **Test Python Path**: Verify which Python VS Code can access
2. **Check MCP Server**: Test server directly: `python3 server/mcp_server.py`
3. **Environment Variables**: Ensure all required env vars are set
4. **VS Code Restart**: Restart VS Code after configuration changes
5. **Check Output Panel**: Look for detailed error messages in VS Code output

## Why Wrapper Script Failed

VS Code's MCP implementation may have restrictions on executing shell scripts directly. Direct Python execution is more reliable.

## Recommended Configuration

Use **Solution 1** with `/usr/bin/python3` as it's the most compatible with VS Code's execution environment.
