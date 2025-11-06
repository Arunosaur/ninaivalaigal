#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Start Core API service with Apple Container CLI
# Follows the same pattern as nv-db-start.sh and nv-pgbouncer-start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🚀 Starting ninaivalaigal Core API Service"
echo "==========================================="

# Load environment variables from configs/env-{env}.env (STANDARDS COMPLIANCE)
NINA_ENV=${NINA_ENV:-dev}
ENV_FILE="$PROJECT_ROOT/configs/env-${NINA_ENV}.env"
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    echo "✅ Loaded environment from $ENV_FILE"
else
    echo "⚠️  $ENV_FILE not found, using defaults"
    NINA_ENV=${NINA_ENV:-dev}
fi

# Set defaults
NINA_ENV=${NINA_ENV:-dev}
NINA_DB_USER=${NINA_DB_USER:-nina}
NINA_DB_PASSWORD=${NINA_DB_PASSWORD:-dev_password_change_in_production}
NINA_JWT_SECRET=${NINA_JWT_SECRET:-dev_jwt_secret_change_in_production}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-core-api"
IMAGE_NAME="nina-core-api:arm64"
# Port allocation per config/ports.nv.yaml (apple.dev.api = 13390)
PORT_EXTERNAL=13390
PORT_INTERNAL=8000

echo ""
echo "📊 Configuration:"
echo "   Environment: $NINA_ENV"
echo "   Container: $CONTAINER_NAME"
echo "   Image: $IMAGE_NAME"
echo "   Port: $PORT_EXTERNAL → $PORT_INTERNAL"
echo ""

# Step 1: Get dynamic IPs for dependencies
echo "🔍 Step 1: Discovering service IPs..."

# Task #85 Revised: Use PgBouncer TRANSACTION mode (port 6432) for Core API
PGBOUNCER_TX_CONTAINER=${PGBOUNCER_TX_CONTAINER:-ninaivalaigal-${NINA_ENV}-pgbouncer-tx}
PGB_IP=$(container inspect "$PGBOUNCER_TX_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
if [ -z "$PGB_IP" ] || [ "$PGB_IP" = "null" ]; then
    echo "❌ PgBouncer-TX not found! Please start it first:"
    echo "   cd $PROJECT_ROOT"
    echo "   ./scripts/nv-pgbouncer-tx-start.sh"
    exit 1
fi
echo "   ✅ PgBouncer-TX (transaction mode): $PGB_IP:6432"

REDIS_CONTAINER=${REDIS_CONTAINER:-ninaivalaigal-${NINA_ENV}-redis}
REDIS_IP=$(container inspect "$REDIS_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
if [ -z "$REDIS_IP" ] || [ "$REDIS_IP" = "null" ]; then
    echo "   ⚠️  Redis not found (optional)"
    REDIS_IP="127.0.0.1"
fi
REDIS_PASSWORD=${REDIS_PASSWORD:-}
if [ -n "$REDIS_PASSWORD" ]; then
    REDIS_URL="redis://:${REDIS_PASSWORD}@${REDIS_IP}:6379/0"
    echo "   ✅ Redis: $REDIS_IP:6379 (with password)"
else
    REDIS_URL="redis://${REDIS_IP}:6379/0"
    echo "   ✅ Redis: $REDIS_IP:6379 (no password)"
fi

# Construct database URL (via PgBouncer-TX transaction mode)
DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${PGB_IP}:6432/ninaivalaigal_${NINA_ENV}"
echo "   ✅ Database URL: postgresql://${NINA_DB_USER}:***@${PGB_IP}:6432/ninaivalaigal_${NINA_ENV}"

echo ""

# Step 2: Build with Docker, convert to Apple Container
echo "📦 Step 2: Building Core API image..."
cd "$PROJECT_ROOT"

# Build with Docker (works reliably)
echo "   Building with Docker..."
docker build --no-cache \
    -t "$IMAGE_NAME" \
    -f services/core-api/Dockerfile \
    . > /tmp/core-api-build.log 2>&1

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    tail -20 /tmp/core-api-build.log
    exit 1
fi
echo "   ✅ Docker build complete"

# Save as tar
echo "   Saving Docker image to tar..."
docker save -o /tmp/core-api.tar "$IMAGE_NAME"
if [ $? -ne 0 ]; then
    echo "❌ Failed to save Docker image!"
    exit 1
fi
echo "   ✅ Saved to /tmp/core-api.tar"

# Load into Apple Container CLI
echo "   Loading into Apple Container CLI..."
container image load -i /tmp/core-api.tar > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Failed to load into Apple Container!"
    exit 1
fi
echo "   ✅ Loaded into Apple Container CLI"

# Cleanup
rm -f /tmp/core-api.tar /tmp/core-api-build.log
echo "✅ Image ready: $IMAGE_NAME"
echo ""

# Step 3: Stop existing container
echo "🛑 Step 3: Stopping existing container (if any)..."
container stop "$CONTAINER_NAME" 2>/dev/null && echo "   Stopped" || echo "   Not running"
container rm "$CONTAINER_NAME" 2>/dev/null && echo "   Removed" || echo "   Not found"
echo ""

# Step 4: Start the container with resource limits
echo "🚀 Step 4: Starting Core API container..."
echo "   Memory Limit: 1GB (Fix #3)"
echo "   CPU Limit: 1 core"
echo "   Note: Apple Container CLI doesn't support --restart policy"
echo "         Manual restart required if container crashes"

container run -d \
    --name "$CONTAINER_NAME" \
    --memory 1g \
    --cpus 1 \
    -p "${PORT_EXTERNAL}:${PORT_INTERNAL}" \
    -e NINA_ENV="$NINA_ENV" \
    -e NINA_DB_USER="$NINA_DB_USER" \
    -e NINA_DB_PASSWORD="$NINA_DB_PASSWORD" \
    -e DATABASE_URL="$DATABASE_URL" \
    -e NINAIVALAIGAL_JWT_SECRET="$NINA_JWT_SECRET" \
    -e NINA_JWT_SECRET="$NINA_JWT_SECRET" \
    -e JWT_ALGORITHM=HS256 \
    -e JWT_EXPIRATION_HOURS=168 \
    -e PORT="$PORT_INTERNAL" \
    -e ENVIRONMENT=development \
    -e LOG_LEVEL=info \
    -e REDIS_URL="$REDIS_URL" \
    "$IMAGE_NAME"

if [ $? -eq 0 ]; then
    echo "✅ Container started: $CONTAINER_NAME"
else
    echo "❌ Failed to start container!"
    exit 1
fi

# Step 5: Wait for health check
echo ""
echo "⏳ Step 5: Waiting for service to be healthy..."
sleep 3

CORE_API_IP=$(container inspect "$CONTAINER_NAME" | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

for i in {1..10}; do
    if curl -s "http://localhost:${PORT_EXTERNAL}/health" > /dev/null 2>&1; then
        echo "✅ Core API is healthy!"
        break
    fi
    echo "   Waiting... ($i/10)"
    sleep 2
done

echo ""
echo "==========================================="
echo "✅ Core API Service Started Successfully!"
echo "==========================================="
echo ""
echo "📍 Access Points:"
echo "   External: http://localhost:${PORT_EXTERNAL}"
echo "   Internal: http://${CORE_API_IP}:${PORT_INTERNAL}"
echo ""
echo "📝 API Endpoints:"
echo "   Health:  GET  http://localhost:${PORT_EXTERNAL}/health"
echo "   Signup:  POST http://localhost:${PORT_EXTERNAL}/auth/signup"
echo "   Login:   POST http://localhost:${PORT_EXTERNAL}/auth/login"
echo ""
echo "🔍 Useful Commands:"
echo "   Check status:  container list | grep core-api"
echo "   View logs:     container logs -f $CONTAINER_NAME"
echo "   Stop service:  container stop $CONTAINER_NAME"
echo "   Restart:       $0"
echo ""
echo "🧪 Test Signup:"
echo "   curl -X POST http://localhost:${PORT_EXTERNAL}/auth/signup \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\":\"test@example.com\",\"password\":\"test123\",\"name\":\"Test User\"}'"
echo ""
