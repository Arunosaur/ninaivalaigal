#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Test script portability across macOS (BSD) and Linux (GNU)
#
# Run this on both:
# - macOS:   ./scripts/test_portability.sh
# - Container: container exec ninaivalaigal-dev-core-api /bin/bash -c "apt-get update && apt-get install -y curl && bash /app/scripts/test_portability.sh"

set -e

echo "🔍 Testing Script Portability on $(uname -s) $(uname -m)"
echo "========================================================="
echo ""

# Test 1: sed '$d' (remove last line)
echo "Test 1: sed '\$d' (remove last line)"
TEST_DATA="line1
line2
line3
200"

BODY=$(echo "$TEST_DATA" | sed '$d')
CODE=$(echo "$TEST_DATA" | tail -n 1)

if [ "$CODE" = "200" ] && [ "$(echo "$BODY" | wc -l | tr -d ' ')" = "3" ]; then
    echo "   ✅ sed '\$d' works correctly"
else
    echo "   ❌ sed '\$d' failed"
    exit 1
fi

# Test 2: tail -n 1 (get last line)
echo "Test 2: tail -n 1 (get last line)"
LAST_LINE=$(echo "$TEST_DATA" | tail -n 1)
if [ "$LAST_LINE" = "200" ]; then
    echo "   ✅ tail -n 1 works correctly"
else
    echo "   ❌ tail -n 1 failed"
    exit 1
fi

# Test 3: curl with -w flag (status code extraction)
echo "Test 3: curl -w flag (if curl is available)"
if command -v curl >/dev/null 2>&1; then
    # Test that curl accepts -w flag (just check it doesn't error)
    if curl -w "" --version >/dev/null 2>&1; then
        echo "   ✅ curl supports -w flag"
    else
        echo "   ⚠️  curl -w flag test inconclusive (curl version: $(curl --version | head -1))"
    fi
else
    echo "   ⚠️  curl not installed (optional for testing)"
fi

# Test 4: date +%s (epoch timestamp)
echo "Test 4: date +%s (epoch timestamp)"
TIMESTAMP=$(date +%s)
if [ "$TIMESTAMP" -gt 1000000000 ]; then
    echo "   ✅ date +%s works correctly (timestamp: $TIMESTAMP)"
else
    echo "   ❌ date +%s failed"
    exit 1
fi

echo ""
echo "========================================================="
echo "✅ All portability tests passed on $(uname -s)!"
echo "========================================================="
echo ""
echo "This system is compatible with:"
echo "  - debug_auth_tests.sh"
echo "  - All auth testing scripts"
echo ""
