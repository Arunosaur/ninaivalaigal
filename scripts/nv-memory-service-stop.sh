#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Stop Rust Memory Service

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load environment for NINA_ENV
if [ -f "$PROJECT_ROOT/.env.dev" ]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env.dev"
fi

NINA_ENV=${NINA_ENV:-dev}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-memory-service"

echo "Stopping Rust Memory Service"
echo "======================================"
echo "  Container: $CONTAINER_NAME"
echo ""

# Check if container exists
if ! container inspect "$CONTAINER_NAME" &>/dev/null; then
    echo "❌ Container not found: $CONTAINER_NAME"
    exit 0
fi

# Stop container
echo "Stopping container..."
container stop "$CONTAINER_NAME" 2>/dev/null || true

# Remove container
echo "Removing container..."
container rm "$CONTAINER_NAME" 2>/dev/null || true

echo ""
echo "✅ Rust Memory Service stopped"
echo ""
