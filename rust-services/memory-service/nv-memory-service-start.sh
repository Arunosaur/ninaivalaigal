#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Start the Rust memory service inside Apple Container CLI following Developer A conventions

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Starting ninaivalaigal Memory Service"
echo "====================================="

if [ -f "$PROJECT_ROOT/.env.dev" ]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env.dev"
    echo "Loaded environment from .env.dev"
else
    echo ".env.dev not found, using defaults"
fi

echo ""

NINA_ENV=${NINA_ENV:-dev}
NINA_DB_USER=${NINA_DB_USER:-nina}
NINA_DB_PASSWORD=${NINA_DB_PASSWORD:-dev_password_change_in_production}
NINA_JWT_SECRET=${NINAIVALAIGAL_JWT_SECRET:-${NINA_JWT_SECRET:-dev_jwt_secret_change_in_production}}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-memory-service"
IMAGE_NAME="nina-memory-service:arm64"
PORT_EXTERNAL=13393
PORT_INTERNAL=8000

MEMORY_CACHE_TTL_SECONDS=${MEMORY_CACHE_TTL_SECONDS:-3600}
REDIS_PORT=${REDIS_PORT:-6379}

echo "Configuration"
echo "   Environment: $NINA_ENV"
echo "   Container:   $CONTAINER_NAME"
echo "   Image:       $IMAGE_NAME"
echo "   Port:        $PORT_EXTERNAL -> $PORT_INTERNAL"
echo "   JWT Secret:  ${NINA_JWT_SECRET:0:4}***"
echo "   Cache TTL:   ${MEMORY_CACHE_TTL_SECONDS}s"
echo ""

# Task #85 Revised: Use PgBouncer SESSION mode (port 6433) for prepared statements
echo "Resolving PgBouncer SESSION mode endpoint..."
PGBOUNCER_CONTAINER="ninaivalaigal-${NINA_ENV}-pgbouncer-sess"
PGBOUNCER_IP=$(container inspect "$PGBOUNCER_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
if [ -z "$PGBOUNCER_IP" ] || [ "$PGBOUNCER_IP" = "null" ]; then
    echo "❌ Unable to find PgBouncer SESSION container ($PGBOUNCER_CONTAINER)."
    echo "   Please ensure PgBouncer SESSION mode is running:"
    echo "   cd $PROJECT_ROOT && ./scripts/nv-pgbouncer-sess-start.sh"
    exit 1
fi

echo "   Database: $PGBOUNCER_IP:6433 (via PgBouncer-SESS - session mode, prepared statements)"
DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${PGBOUNCER_IP}:6433/ninaivalaigal_${NINA_ENV}"
echo "   Database URL: postgresql://${NINA_DB_USER}:***@${PGBOUNCER_IP}:6433/ninaivalaigal_${NINA_ENV}"
echo ""

if [ -z "${REDIS_URL:-}" ]; then
    echo "Resolving Redis endpoint..."
    REDIS_CONTAINER="ninaivalaigal-${NINA_ENV}-redis"
    REDIS_IP=$(container inspect "$REDIS_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
    if [ -z "$REDIS_IP" ] || [ "$REDIS_IP" = "null" ]; then
        echo "Unable to find Redis container ($REDIS_CONTAINER)."
        echo "   Please ensure redis services are running:"
        echo "   cd $PROJECT_ROOT && ./scripts/nv-redis-start.sh"
        exit 1
    fi
    REDIS_URL="redis://${REDIS_IP}:${REDIS_PORT}"
    echo "   Redis URL: $REDIS_URL"
else
    echo "Using provided REDIS_URL environment override"
fi

echo ""

# Build Docker image for Apple container import
echo "Building memory-service Docker image..."
cd "$SCRIPT_DIR"
docker build --platform linux/arm64 --no-cache -t "$IMAGE_NAME" . > /tmp/memory-service-build.log 2>&1 || {
    echo "Docker build failed"
    tail -20 /tmp/memory-service-build.log
    exit 1
}
echo "   Docker build complete"

echo "Exporting image for Apple Container CLI"
docker save -o /tmp/memory-service.tar "$IMAGE_NAME"
container image load -i /tmp/memory-service.tar > /tmp/memory-service-load.log 2>&1 || {
    echo "Failed to load image into Apple Container CLI"
    tail -20 /tmp/memory-service-load.log
    rm -f /tmp/memory-service.tar /tmp/memory-service-build.log /tmp/memory-service-load.log
    exit 1
}
echo "   Image loaded"
rm -f /tmp/memory-service.tar /tmp/memory-service-build.log /tmp/memory-service-load.log

echo ""
echo "Stopping existing container (if running)"
container stop "$CONTAINER_NAME" 2>/dev/null && echo "   Stopped" || echo "   Not running"
container rm "$CONTAINER_NAME" 2>/dev/null && echo "   Removed" || echo "   Not found"

echo ""
echo "Launching new container"
container run -d \
    --name "$CONTAINER_NAME" \
    -p "${PORT_EXTERNAL}:${PORT_INTERNAL}" \
    -e NINA_ENV="$NINA_ENV" \
    -e DATABASE_URL="$DATABASE_URL" \
    -e NINAIVALAIGAL_JWT_SECRET="$NINA_JWT_SECRET" \
    -e NINA_JWT_SECRET="$NINA_JWT_SECRET" \
    -e REDIS_URL="$REDIS_URL" \
    -e MEMORY_CACHE_TTL_SECONDS="$MEMORY_CACHE_TTL_SECONDS" \
    -e PORT="$PORT_INTERNAL" \
    -e RUST_LOG="info" \
    "$IMAGE_NAME" || {
    echo "Failed to start container"
    exit 1
}
echo "   Container started"

echo ""
echo "Waiting for health check..."
sleep 2
for attempt in {1..10}; do
    if curl -s "http://localhost:${PORT_EXTERNAL}/health" > /dev/null 2>&1; then
        echo "   Service healthy"
        break
    fi
    echo "   Waiting... (${attempt}/10)"
    sleep 2
    if [ $attempt -eq 10 ]; then
        echo "Service did not become healthy in time"
        exit 1
    fi

done

echo ""
echo "====================================="
echo "Memory Service Started Successfully"
echo "====================================="
echo ""
echo "External: http://localhost:${PORT_EXTERNAL}"
MEMORY_IP=$(container inspect "$CONTAINER_NAME" | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "Internal: http://${MEMORY_IP}:${PORT_INTERNAL}"
echo ""
echo "Useful Commands"
echo "   Status: container list | grep memory-service"
echo "   Logs:   container logs -f $CONTAINER_NAME"
echo "   Stop:   $SCRIPT_DIR/nv-memory-service-stop.sh"
echo "   Query:  curl http://localhost:${PORT_EXTERNAL}/health"
echo ""
