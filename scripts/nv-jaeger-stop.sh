#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Stop Jaeger distributed tracing

set -euo pipefail

CONTAINER_NAME="ninaivalaigal-dev-jaeger"
COMPOSE_FILE="deployment/observability/docker-compose.jaeger.yml"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛑 Stopping Jaeger Distributed Tracing"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "🛑 Stopping Jaeger..."
    docker-compose -f "$COMPOSE_FILE" down
    echo "✅ Jaeger stopped"
else
    echo "ℹ️  Jaeger is not running"
fi

echo ""
