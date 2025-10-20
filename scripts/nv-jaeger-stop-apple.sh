#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Stop Jaeger distributed tracing (Apple Container CLI)

set -euo pipefail

CONTAINER_NAME="ninaivalaigal-dev-jaeger"

echo "🛑 Stopping Jaeger..."

if container list | grep -q "$CONTAINER_NAME"; then
    container stop "$CONTAINER_NAME"
    container rm "$CONTAINER_NAME"
    echo "✅ Jaeger stopped and removed"
else
    echo "⚠️  Jaeger is not running"
fi
