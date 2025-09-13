#!/bin/bash
# VS Code MCP Server Wrapper Script
# Handles environment setup and Python path issues

set -e

# Set environment variables
export MEM0_JWT_SECRET="FcbdlNhk9AlKmeGjDNVmZK3CK12UZdQRrdaG1i8xesk"
export MEM0_DATABASE_URL="postgresql://mem0user:mem0pass@localhost:5432/mem0db"
export PYTHONPATH="/Users/asrajag/Workspace/mem0/server"

# Change to project directory
cd "/Users/asrajag/Workspace/mem0"

# Start MCP server with full Python path
exec /opt/homebrew/anaconda3/bin/python3.11 server/mcp_server.py "$@"
