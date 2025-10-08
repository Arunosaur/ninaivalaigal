#!/usr/bin/env bash
# Stack Restart Script
# Version: 1.0.0 - Day 3 Infrastructure Reliability

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "🔄 Restarting Ninaivalaigal Stack..."
echo ""

# Stop the stack
"$SCRIPT_DIR/stack-stop.sh"

# Wait a moment for clean shutdown
sleep 3

# Start the stack
"$SCRIPT_DIR/stack-start.sh"
