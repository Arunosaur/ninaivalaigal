#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Start Jaeger for distributed tracing (Task #84)

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Starting Jaeger Distributed Tracing"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Configuration
CONTAINER_NAME="ninaivalaigal-dev-jaeger"
IMAGE_NAME="jaegertracing/all-in-one:1.51"
COMPOSE_FILE="deployment/observability/docker-compose.jaeger.yml"

# Check if network exists
if ! docker network inspect ninaivalaigal-network >/dev/null 2>&1; then
    echo "📡 Creating ninaivalaigal-network..."
    docker network create ninaivalaigal-network
fi

# Stop existing container if running
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "🛑 Stopping existing Jaeger container..."
    docker stop "$CONTAINER_NAME" || true
    docker rm "$CONTAINER_NAME" || true
    sleep 2
fi

# Start Jaeger using docker-compose
echo ""
echo "🚀 Starting Jaeger..."
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for Jaeger to be ready
echo ""
echo "⏳ Waiting for Jaeger to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker exec "$CONTAINER_NAME" wget --spider -q http://localhost:16686/ 2>/dev/null; then
        echo "   ✅ Jaeger is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "   ❌ Jaeger failed to start within expected time"
    exit 1
fi

# Get container IP
JAEGER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$CONTAINER_NAME")

# Show status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Jaeger Started Successfully"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Jaeger UI:"
echo "   http://localhost:16686"
echo ""
echo "📡 Collector Endpoints:"
echo "   OTLP gRPC:  localhost:4317"
echo "   OTLP HTTP:  localhost:4318"
echo "   Jaeger gRPC: localhost:14250"
echo "   Jaeger HTTP: localhost:14268"
echo "   Zipkin:     localhost:9411"
echo ""
echo "🔗 Container Info:"
echo "   Name:       $CONTAINER_NAME"
echo "   IP:         $JAEGER_IP"
echo "   Network:    ninaivalaigal-network"
echo ""
echo "🧪 Quick Test:"
echo "   # Check health"
echo "   curl http://localhost:16686/"
echo ""
echo "   # View in browser"
echo "   open http://localhost:16686"
echo ""
echo "   # View logs"
echo "   docker logs -f $CONTAINER_NAME"
echo ""
