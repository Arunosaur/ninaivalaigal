#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Stop the Rust memory service container following Developer A conventions

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/../../.env.dev" ]; then
    # shellcheck disable=SC1091
    source "$SCRIPT_DIR/../../.env.dev"
fi

NINA_ENV=${NINA_ENV:-dev}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-memory-service"

echo "Stopping $CONTAINER_NAME"
container stop "$CONTAINER_NAME" 2>/dev/null && echo "   Stopped" || echo "   Not running"
container rm "$CONTAINER_NAME" 2>/dev/null && echo "   Removed" || echo "   Not found"
