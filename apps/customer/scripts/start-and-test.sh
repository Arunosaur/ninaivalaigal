#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Start dev server and run accessibility tests

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CUSTOMER_DIR="$PROJECT_DIR/apps/customer"

cd "$CUSTOMER_DIR"

echo "=========================================="
echo "Customer UI - Accessibility Testing"
echo "=========================================="
echo ""

# Check if dev server is already running
if lsof -ti:8101 > /dev/null 2>&1; then
    echo "✅ Dev server is already running on port 8101"
    echo ""
    echo "Running accessibility tests..."
    npm run test:accessibility
else
    echo "🚀 Starting dev server..."
    echo ""
    echo "⚠️  The dev server will start in the background."
    echo "   Run tests in another terminal with:"
    echo "   cd apps/customer && npm run test:accessibility"
    echo ""
    echo "Or wait ~10 seconds for server to start, then tests will run automatically..."
    echo ""

    # Start dev server in background
    npm run dev > /tmp/vite-dev-server.log 2>&1 &
    VITE_PID=$!

    # Wait for server to be ready
    echo "⏳ Waiting for dev server to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8101 > /dev/null 2>&1; then
            echo "✅ Dev server is ready!"
            echo ""
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""

    # Run tests
    echo "🧪 Running accessibility tests..."
    echo ""
    npm run test:accessibility

    # Cleanup
    echo ""
    echo "🛑 Stopping dev server..."
    kill $VITE_PID 2>/dev/null || true
    echo "✅ Done"
fi
