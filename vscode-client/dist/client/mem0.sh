#!/bin/bash
# mem0 client wrapper script
# Portable solution for shell integration

# Find the mem0 project directory (portable)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Run the Python client
python3 mem0 "$@"
