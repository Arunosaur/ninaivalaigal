#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC

# Stop Traefik API Gateway
# Task #83: API Gateway Deployment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TRAEFIK_DIR="$PROJECT_ROOT/deployment/traefik"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛑 Stopping Traefik API Gateway"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$TRAEFIK_DIR"

# Stop gateway
if docker ps | grep -q ninaivalaigal-gateway; then
    echo "🛑 Stopping gateway..."
    docker-compose down
    echo "✅ Gateway stopped"
else
    echo "ℹ️  Gateway is not running"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Gateway Stopped"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
