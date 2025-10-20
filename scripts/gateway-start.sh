#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC

# Start Traefik API Gateway
# Task #83: API Gateway Deployment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TRAEFIK_DIR="$PROJECT_ROOT/deployment/traefik"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚪 Starting Traefik API Gateway"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create network if it doesn't exist
if ! docker network ls | grep -q ninaivalaigal-network; then
    echo "📡 Creating ninaivalaigal-network..."
    docker network create ninaivalaigal-network
fi

# Stop existing gateway if running
if docker ps | grep -q ninaivalaigal-gateway; then
    echo "🛑 Stopping existing gateway..."
    docker stop ninaivalaigal-gateway >/dev/null 2>&1
    docker rm ninaivalaigal-gateway >/dev/null 2>&1
fi

# Start Traefik
cd "$TRAEFIK_DIR"
echo "🚀 Starting Traefik..."
docker-compose up -d

# Wait for health check
echo "⏳ Waiting for gateway to be healthy..."
for i in {1..30}; do
    if docker ps | grep -q "ninaivalaigal-gateway.*healthy\|ninaivalaigal-gateway.*Up"; then
        echo "✅ Gateway is healthy!"
        break
    fi
    sleep 1
done

# Show status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Traefik API Gateway Started"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Services:"
echo "   • Dashboard: http://localhost:8080"
echo "   • HTTP:      http://localhost:80"
echo "   • HTTPS:     https://localhost:443"
echo ""
echo "🔗 Routes:"
echo "   • /api/*      → Core API"
echo "   • /business/* → Business Service"
echo "   • /memory/*   → Memory Service"
echo "   • /graph/*    → GraphOps"
echo "   • /health     → Gateway Health"
echo "   • /metrics    → Prometheus Metrics"
echo ""
echo "📝 Logs:"
echo "   docker logs -f ninaivalaigal-gateway"
echo ""
