#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Start Core API service with Apple Container CLI

set -e

echo "🚀 Starting Core API Microservice with Apple Container CLI"
echo "=========================================================="

cd /Users/swami/WorkSpace/ninaivalaigal

# Export environment variables
export DB_PASSWORD=dev_password_change_in_production
export JWT_SECRET=dev_jwt_secret_change_in_production
export LOG_LEVEL=info

# Get PgBouncer IP dynamically (support dual PgBouncer architecture)
PGB_IP=""
PGB_PORT="6432"
for candidate in ninaivalaigal-dev-pgbouncer-tx ninaivalaigal-dev-pgbouncer-session ninaivalaigal-dev-pgbouncer-sess; do
    INSPECT_OUTPUT=$(container inspect "$candidate" 2>/dev/null || true)
    if [ -n "$INSPECT_OUTPUT" ]; then
        ADDRESS=$(echo "$INSPECT_OUTPUT" | jq -r '.[0].networks[0].address // ""')
        if [ -n "$ADDRESS" ]; then
            PGB_IP=${ADDRESS%/*}
            case "$candidate" in
                *-session|*-sess)
                    PGB_PORT="6433"
                    ;;
                *)
                    PGB_PORT="6432"
                    ;;
            esac
            break
        fi
    fi
done

if [ -z "$PGB_IP" ]; then
    echo "⚠️ Could not resolve PgBouncer container IP; defaulting to localhost."
    PGB_IP="localhost"
    PGB_PORT="6432"
fi

REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

echo "📊 Dynamic IPs:"
echo "   PgBouncer: $PGB_IP:$PGB_PORT"
echo "   Redis: $REDIS_IP:6379"
echo ""

# Build Core API image
echo "📦 Building Core API image..."
container build --no-cache -t ninaivalaigal-core-api:latest -f services/core-api/Dockerfile .

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "✅ Image built successfully!"
echo ""

# Stop existing container if running
echo "🛑 Stopping existing container (if any)..."
container stop ninaivalaigal-core-api 2>/dev/null || true
container rm ninaivalaigal-core-api 2>/dev/null || true

# Start Core API container
echo "🚀 Starting Core API service..."
container run -d \
    --name ninaivalaigal-core-api \
    -p 8001:8000 \
    -e NINA_ENV=dev \
    -e NINA_DB_USER=nina \
    -e NINA_DB_PASSWORD=$DB_PASSWORD \
    -e DATABASE_URL="postgresql://nina:${DB_PASSWORD}@${PGB_IP}:${PGB_PORT}/ninaivalaigal_dev" \
    -e NINAIVALAIGAL_JWT_SECRET=$JWT_SECRET \
    -e NINA_JWT_SECRET=$JWT_SECRET \
    -e JWT_ALGORITHM=HS256 \
    -e JWT_EXPIRATION_HOURS=168 \
    -e PORT=8000 \
    -e ENVIRONMENT=development \
    -e LOG_LEVEL=$LOG_LEVEL \
    -e REDIS_URL="redis://${REDIS_IP}:6379/0" \
    ninaivalaigal-core-api:latest

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Core API service started!"
    echo ""
    echo "📍 Endpoints:"
    echo "   Health: http://localhost:8001/health"
    echo "   Signup: http://localhost:8001/auth/signup"
    echo "   Login:  http://localhost:8001/auth/login"
    echo ""
    echo "🔍 Check logs:"
    echo "   container logs -f ninaivalaigal-core-api"
    echo ""
    echo "🛑 Stop service:"
    echo "   container stop ninaivalaigal-core-api"
    echo ""
    echo "📊 Check status:"
    echo "   container list | grep core-api"
    echo ""
else
    echo "❌ Failed to start service!"
    exit 1
fi
