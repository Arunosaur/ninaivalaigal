#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Cleanup script: Remove all legacy nv-* containers
# These were replaced by ninaivalaigal-dev-* naming convention

set -euo pipefail

echo "🧹 Cleaning up legacy nv-* containers..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get all container names starting with "nv-"
LEGACY_CONTAINERS=$(container list | awk '{print $1}' | grep "^nv-" || true)

if [ -z "$LEGACY_CONTAINERS" ]; then
    echo "✅ No legacy nv-* containers found"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
fi

echo "Found legacy containers:"
echo "$LEGACY_CONTAINERS"
echo ""

# Stop and remove each container
for container_name in $LEGACY_CONTAINERS; do
    echo "🛑 Stopping $container_name..."
    container stop "$container_name" 2>/dev/null || echo "  (already stopped)"

    echo "🗑️  Removing $container_name..."
    container rm "$container_name" 2>/dev/null || echo "  (already removed)"

    echo "✅ $container_name cleaned up"
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All legacy nv-* containers removed"
echo ""
echo "Current containers (should only be ninaivalaigal-dev-*):"
container list | grep "ninaivalaigal-dev-" || echo "  (none running)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
