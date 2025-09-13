#!/bin/bash
# VS Code MCP Server Wrapper Script
# Handles environment setup and Python path issues

set -e

# Debug logging
echo "DEBUG: Wrapper script starting" >&2
echo "DEBUG: PATH=$PATH" >&2
echo "DEBUG: PWD=$(pwd)" >&2

# Set environment variables
export NINAIVALAIGAL_JWT_SECRET="FcbdlNhk9AlKmeGjDNVmZK3CK12UZdQRrdaG1i8xesk"
export NINAIVALAIGAL_DATABASE_URL="postgresql://mem0user:mem0pass@localhost:5432/mem0db"
export PYTHONPATH="/Users/asrajag/Workspace/mem0/server"

# Change to project directory
cd "/Users/asrajag/Workspace/mem0"

echo "DEBUG: Changed to $(pwd)" >&2
echo "DEBUG: Python path: /opt/homebrew/anaconda3/bin/python3.11" >&2
echo "DEBUG: MCP server path: server/mcp_server.py" >&2

# Verify files exist
if [[ ! -f "/opt/homebrew/anaconda3/bin/python3.11" ]]; then
    echo "ERROR: Python executable not found at /opt/homebrew/anaconda3/bin/python3.11" >&2
    exit 1
fi

if [[ ! -f "server/mcp_server.py" ]]; then
    echo "ERROR: MCP server not found at server/mcp_server.py" >&2
    exit 1
fi

echo "DEBUG: Starting MCP server..." >&2

# Start MCP server with full Python path
exec /opt/homebrew/anaconda3/bin/python3.11 server/mcp_server.py "$@"
