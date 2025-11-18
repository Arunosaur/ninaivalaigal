#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Start Rust Memory Service
# Follows: docs/standards/CONTAINERIZATION_STANDARD.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Starting Rust Memory Service"
echo "======================================"

# Load environment
if [ -f "$PROJECT_ROOT/.env.dev" ]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env.dev"
    echo "✅ Loaded environment from .env.dev"
else
    echo "❌ .env.dev not found!"
    echo "   Run: cp .env.example .env.dev"
    echo "   Then edit .env.dev with proper values"
    exit 1
fi

# Validate required environment variables
required_vars=(
    "NINA_ENV"
    "NINA_DB_USER"
    "NINA_DB_PASSWORD"
    "NINA_DB_NAME"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "❌ Required environment variable $var not set"
        exit 1
    fi
done

# Configuration from ports.nv.yaml
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-memory-service"
# Image name - check both with and without tag
IMAGE_NAME="ninaivalaigal-memory-service"
IMAGE_NAME_ALT="ninaivalaigal-memory-service:arm64"
# Use PgBouncer Session Mode for prepared statements (SQLx compatibility)
PGBOUNCER_SESS_CONTAINER="ninaivalaigal-${NINA_ENV}-pgbouncer-sess"
REDIS_CONTAINER="ninaivalaigal-${NINA_ENV}-redis"
HOST_PORT=13393  # From ports.nv.yaml - memory_service base port
CONTAINER_PORT=8000
PGBOUNCER_SESS_PORT=6433  # PgBouncer Session Mode container port

# Optional configuration
MEMORY_CACHE_TTL_SECONDS=${MEMORY_CACHE_TTL_SECONDS:-3600}
LOG_LEVEL=${LOG_LEVEL:-info}
NINA_JWT_SECRET=${NINAIVALAIGAL_JWT_SECRET:-${NINA_JWT_SECRET:-dev_jwt_secret_change_in_production}}

echo ""
echo "Configuration:"
echo "  Environment: $NINA_ENV"
echo "  Container: $CONTAINER_NAME"
echo "  Image: $IMAGE_NAME"
echo "  Port: $HOST_PORT -> $CONTAINER_PORT"
echo "  Cache TTL: ${MEMORY_CACHE_TTL_SECONDS}s"
echo "  Log Level: $LOG_LEVEL"
echo ""

# Function: Resolve container IP dynamically
resolve_container_ip() {
    local container_name=$1
    local container_ip

    container_ip=$(container inspect "$container_name" 2>/dev/null \
        | jq -r '.[0].networks[0].address' \
        | cut -d'/' -f1)

    if [ -z "$container_ip" ] || [ "$container_ip" = "null" ]; then
        return 1
    fi

    echo "$container_ip"
}

# Resolve dependency IPs
echo "Resolving dependency endpoints..."

# PgBouncer Session Mode (for SQLx prepared statements)
PGBOUNCER_IP=$(resolve_container_ip "$PGBOUNCER_SESS_CONTAINER")
if [ $? -ne 0 ]; then
    echo "❌ PgBouncer Session Mode container not running: $PGBOUNCER_SESS_CONTAINER"
    echo "   Run: ./scripts/nv-pgbouncer-sess-start.sh"
    exit 1
fi

# Redis
REDIS_IP=$(resolve_container_ip "$REDIS_CONTAINER")
if [ $? -ne 0 ]; then
    echo "❌ Redis container not running: $REDIS_CONTAINER"
    echo "   Run: ./scripts/nv-redis-start.sh"
    exit 1
fi

echo "  ✅ PgBouncer (Session Mode): $PGBOUNCER_IP:${PGBOUNCER_SESS_PORT}"
echo "  ✅ Redis: $REDIS_IP:6379"
echo ""

# Build DATABASE_URL (via PgBouncer Session Mode - supports prepared statements)
# URL encode password to handle any special characters
ENCODED_PASSWORD=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "${NINA_DB_PASSWORD}")
DATABASE_URL="postgresql://${NINA_DB_USER}:${ENCODED_PASSWORD}@${PGBOUNCER_IP}:${PGBOUNCER_SESS_PORT}/${NINA_DB_NAME}"

# Build REDIS_URL with authentication (if password exists)
REDIS_PASSWORD=${REDIS_PASSWORD:-dev_redis_change_me}
if [ -n "$REDIS_PASSWORD" ]; then
    REDIS_URL="redis://:${REDIS_PASSWORD}@${REDIS_IP}:6379/0"
else
    REDIS_URL="redis://${REDIS_IP}:6379/0"
fi

echo "  Database URL: postgresql://${NINA_DB_USER}:***@${PGBOUNCER_IP}:${PGBOUNCER_SESS_PORT}/${NINA_DB_NAME}"
echo "  Redis URL: ${REDIS_URL}"
echo ""

# Check if image exists and get proper name:tag format
echo "Checking for image..."
FOUND_IMAGE=$(container image list | grep ninaivalaigal-memory-service | awk '{print $1 ":" $2}' | head -1)

if [ -n "$FOUND_IMAGE" ]; then
    echo "  ✅ Image found: $FOUND_IMAGE"
    FINAL_IMAGE_NAME="$FOUND_IMAGE"
else
    echo "❌ Image not found: ninaivalaigal-memory-service"
    echo ""
    echo "Build and deploy the image first:"
    echo "   cd rust-services/memory-service"
    echo "   docker build --no-cache --platform linux/arm64 -t ninaivalaigal-memory-service:arm64 ."
    echo "   docker save ninaivalaigal-memory-service:arm64 -o /tmp/memory-service.tar"
    echo "   container image load -i /tmp/memory-service.tar"
    echo ""
    exit 1
fi
echo ""

# Stop existing container if running
if container inspect "$CONTAINER_NAME" &>/dev/null; then
    echo "Stopping existing container..."
    container stop "$CONTAINER_NAME" 2>/dev/null || true
    container rm "$CONTAINER_NAME" 2>/dev/null || true
    echo "  ✅ Cleaned up"
fi

# Start container (Apple Container CLI syntax - no --restart, --memory, --cpus)
echo ""
echo "Starting container..."
container run -d \
  --name "$CONTAINER_NAME" \
  -p "$HOST_PORT:$CONTAINER_PORT" \
  -e NINA_ENV="$NINA_ENV" \
  -e DATABASE_URL="$DATABASE_URL" \
  -e REDIS_URL="$REDIS_URL" \
  -e NINAIVALAIGAL_JWT_SECRET="$NINA_JWT_SECRET" \
  -e NINA_JWT_SECRET="$NINA_JWT_SECRET" \
  -e MEMORY_CACHE_TTL_SECONDS="$MEMORY_CACHE_TTL_SECONDS" \
  -e SERVICE_NAME="memory-service" \
  -e SERVICE_ROLE="memory-crud" \
  -e PORT="$CONTAINER_PORT" \
  -e RUST_LOG="$LOG_LEVEL" \
  "$FINAL_IMAGE_NAME"

if [ $? -ne 0 ]; then
    echo "❌ Failed to start container"
    exit 1
fi

echo "✅ Container started: $CONTAINER_NAME"
echo ""

# Wait for service to be healthy
echo "Waiting for service to be healthy..."
sleep 5

MAX_ATTEMPTS=10
for attempt in $(seq 1 $MAX_ATTEMPTS); do
    if curl -sf "http://localhost:$HOST_PORT/health" > /dev/null 2>&1; then
        echo "✅ Service is healthy!"
        echo ""
        curl -s "http://localhost:$HOST_PORT/health" | jq . || true
        echo ""
        break
    fi

    if [ $attempt -eq $MAX_ATTEMPTS ]; then
        echo "❌ Health check failed after ${MAX_ATTEMPTS} attempts"
        echo ""
        echo "Check logs:"
        echo "   container logs $CONTAINER_NAME"
        echo ""
        exit 1
    fi

    echo "  Waiting... (${attempt}/${MAX_ATTEMPTS})"
    sleep 2
done

# Get container IP for internal access
MEMORY_IP=$(resolve_container_ip "$CONTAINER_NAME")

echo ""
echo "======================================"
echo "🎉 Rust Memory Service Running!"
echo "======================================"
echo ""
echo "External Access:"
echo "  Health: http://localhost:$HOST_PORT/health"
echo "  Docs:   http://localhost:$HOST_PORT/docs"
echo "  API:    http://localhost:$HOST_PORT/api/v1/memory"
echo ""
echo "Internal Access (from other containers):"
echo "  URL: http://$MEMORY_IP:$CONTAINER_PORT"
echo ""
echo "Useful Commands:"
echo "  Status: container list | grep memory-service"
echo "  Logs:   container logs -f $CONTAINER_NAME"
echo "  Stop:   container stop $CONTAINER_NAME"
echo "  Health: curl http://localhost:$HOST_PORT/health"
echo ""
