#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Stop GraphOps gRPC Service

set -euo pipefail

CONTAINER_NAME="ninaivalaigal-dev-graphops"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛑 Stopping GraphOps gRPC Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if container list | grep -q "$CONTAINER_NAME"; then
    echo "🛑 Stopping $CONTAINER_NAME..."
    container stop "$CONTAINER_NAME"
    container rm "$CONTAINER_NAME"
    echo "✅ GraphOps stopped"
else
    echo "ℹ️  GraphOps is not running"
fi

echo ""
