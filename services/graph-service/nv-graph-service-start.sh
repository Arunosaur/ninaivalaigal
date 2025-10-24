#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Start Graph/AI Service (SPEC-100 + SPEC-062 Compliant)
# Task #85: Uses PgBouncer-TX (transaction mode) for stateless REST API

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🧠 Starting Graph/AI Service (SPEC-100 + SPEC-062)"
echo "==================================================="

# Load centralized environment
if [ -f "$PROJECT_ROOT/.env.dev" ]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env.dev"
    echo "✅ Loaded environment from .env.dev"
else
    echo "❌ .env.dev not found!"
    echo "   Run: cp .env.example .env.dev"
    exit 1
fi

# Configuration
NINA_ENV=${NINA_ENV:-dev}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-graph-service"
IMAGE_NAME="nina-graph-service:arm64"
PORT_EXTERNAL=13392  # From ports.nv.yaml
PORT_INTERNAL=8001

echo ""
echo "Configuration:"
echo "  Environment: $NINA_ENV"
echo "  Container: $CONTAINER_NAME"
echo "  Port: $PORT_EXTERNAL → $PORT_INTERNAL"
echo ""

# Task #85: Use PgBouncer TRANSACTION mode (stateless REST API)
echo "Resolving PgBouncer-TX endpoint..."
PGBOUNCER_TX_CONTAINER=${PGBOUNCER_TX_CONTAINER:-ninaivalaigal-${NINA_ENV}-pgbouncer-tx}
PGBOUNCER_IP=$(container inspect "$PGBOUNCER_TX_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

if [ -z "$PGBOUNCER_IP" ] || [ "$PGBOUNCER_IP" = "null" ]; then
    echo "❌ PgBouncer-TX not found!"
    echo "   Start it first: ./scripts/nv-pgbouncer-tx-start.sh"
    exit 1
fi

echo "  PgBouncer-TX (transaction mode): $PGBOUNCER_IP:6432"

# Build DATABASE_URL from environment variables
DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${PGBOUNCER_IP}:6432/ninaivalaigal_${NINA_ENV}"
echo "  Database URL: postgresql://${NINA_DB_USER}:***@${PGBOUNCER_IP}:6432/ninaivalaigal_${NINA_ENV}"
echo ""

# Resolve Redis
REDIS_CONTAINER=${REDIS_CONTAINER:-ninaivalaigal-${NINA_ENV}-redis}
REDIS_IP=$(container inspect "$REDIS_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

if [ -z "$REDIS_IP" ] || [ "$REDIS_IP" = "null" ]; then
    echo "  ⚠️  Redis not found (optional)"
    REDIS_IP="127.0.0.1"
fi

REDIS_PASSWORD=${REDIS_PASSWORD:-}
if [ -n "$REDIS_PASSWORD" ]; then
    REDIS_URL="redis://:${REDIS_PASSWORD}@${REDIS_IP}:6379/0"
    echo "  Redis: $REDIS_IP:6379 (with password)"
else
    REDIS_URL="redis://${REDIS_IP}:6379/0"
    echo "  Redis: $REDIS_IP:6379"
fi
echo ""

# Build Docker image
echo "Building Graph Service image..."
cd "$PROJECT_ROOT"
docker build --no-cache \
    -t "$IMAGE_NAME" \
    -f services/graph-service/Dockerfile \
    . > /tmp/graph-service-build.log 2>&1

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    tail -20 /tmp/graph-service-build.log
    exit 1
fi
echo "✅ Docker build complete"

# Save and load to Apple Container
docker save -o /tmp/graph-service.tar "$IMAGE_NAME"
container image load -i /tmp/graph-service.tar > /dev/null 2>&1
rm -f /tmp/graph-service.tar /tmp/graph-service-build.log
echo "✅ Image loaded"
echo ""

# Stop existing container
echo "Stopping existing container (if any)..."
container stop "$CONTAINER_NAME" 2>/dev/null && echo "  Stopped" || echo "  Not running"
container rm "$CONTAINER_NAME" 2>/dev/null && echo "  Removed" || echo "  Not found"
echo ""

# Start container
echo "Starting Graph/AI Service container..."
container run -d \
    --name "$CONTAINER_NAME" \
    -p "${PORT_EXTERNAL}:${PORT_INTERNAL}" \
    -e NINA_ENV="$NINA_ENV" \
    -e NINA_DB_USER="$NINA_DB_USER" \
    -e NINA_DB_PASSWORD="$NINA_DB_PASSWORD" \
    -e DATABASE_URL="$DATABASE_URL" \
    -e REDIS_URL="$REDIS_URL" \
    -e PORT="$PORT_INTERNAL" \
    -e ENVIRONMENT=development \
    -e LOG_LEVEL=info \
    "$IMAGE_NAME"

echo "✅ Container started"
echo ""

# Wait for health check
echo "Waiting for service to be healthy..."
sleep 3

for i in {1..10}; do
    if curl -s "http://localhost:${PORT_EXTERNAL}/api/v1/graph/health" > /dev/null 2>&1; then
        echo "✅ Graph/AI Service is healthy!"
        break
    fi
    echo "  Waiting... ($i/10)"
    sleep 2
done

# Get container IP
GRAPH_IP=$(container inspect "$CONTAINER_NAME" | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

echo ""
echo "====================================================="
echo "✅ Graph/AI Service Started Successfully"
echo "====================================================="
echo ""
echo "Access Points:"
echo "  External: http://localhost:${PORT_EXTERNAL}"
echo "  Internal: http://${GRAPH_IP}:${PORT_INTERNAL}"
echo ""
echo "API Endpoints:"
echo "  Health:       GET  http://localhost:${PORT_EXTERNAL}/api/v1/graph/health"
echo "  Metrics:      GET  http://localhost:${PORT_EXTERNAL}/api/v1/graph/metrics"
echo "  GraphOps:     GET  http://localhost:${PORT_EXTERNAL}/api/v1/graph/ops/*"
echo "  Intelligence: GET  http://localhost:${PORT_EXTERNAL}/api/v1/graph/intelligence/*"
echo ""
echo "Connections:"
echo "  Database: PgBouncer-TX (transaction mode)"
echo "  Redis:    $REDIS_IP:6379"
echo ""
echo "Monitoring:"
echo "  Status:   container list | grep graph-service"
echo "  Logs:     container logs -f $CONTAINER_NAME"
echo "  Restart:  $0"
echo ""
