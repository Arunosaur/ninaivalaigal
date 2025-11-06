#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Start GraphOps gRPC Service (Task #49, Fixed for Task #85)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Starting GraphOps gRPC Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

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
echo ""

# Configuration
NINA_ENV=${NINA_ENV:-dev}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-graphops"
IMAGE_NAME="nina-graphops:arm64"
GRAPH_NAME="ninaivalaigal_intelligence_${NINA_ENV}"

# Port from ports.nv.yaml (apple.dev.graphops) - SPEC-145 compliance
HOST_PORT=13398
CONTAINER_PORT=50051  # GraphOps gRPC actually listens on 50051, not 8000

# Stop existing container if running
if container list | grep -q "$CONTAINER_NAME"; then
    echo "🛑 Stopping existing $CONTAINER_NAME..."
    container stop "$CONTAINER_NAME" || true
    container rm "$CONTAINER_NAME" || true
    sleep 2
fi

# Task #85 Revised: Use PgBouncer TRANSACTION mode (stateless Cypher queries)
echo "📡 Getting PgBouncer-TX IP..."
PGBOUNCER_TX_CONTAINER=${PGBOUNCER_TX_CONTAINER:-ninaivalaigal-${NINA_ENV}-pgbouncer-tx}
PGBOUNCER_IP=$(container inspect "$PGBOUNCER_TX_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

if [ -z "$PGBOUNCER_IP" ] || [ "$PGBOUNCER_IP" = "null" ]; then
    echo "❌ Error: PgBouncer-TX not running"
    echo "   Start PgBouncer first: ./scripts/nv-pgbouncer-tx-start.sh"
    exit 1
fi

echo "   PgBouncer-TX (transaction mode): $PGBOUNCER_IP:6432"

# Build DATABASE_URL from environment variables (NO hardcoded credentials)
DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${PGBOUNCER_IP}:6432/ninaivalaigal_${NINA_ENV}"
echo "   Database URL: postgresql://${NINA_DB_USER}:***@${PGBOUNCER_IP}:6432/ninaivalaigal_${NINA_ENV}"

# Start GraphOps container
echo ""
echo "🚀 Starting GraphOps..."
container run -d \
  --name "$CONTAINER_NAME" \
  -e DATABASE_URL="$DATABASE_URL" \
  -e GRAPHOPS_GRAPH="$GRAPH_NAME" \
  -e GRAPHOPS_GRPC_ADDR="0.0.0.0:50051" \
  -e GRAPHOPS_METRICS_ADDR="0.0.0.0:9090" \
  -e RUST_LOG=info \
  -e OTEL_SERVICE_NAME="ninaivalaigal-graphops" \
  -e OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317" \
  -e OTEL_TRACING_ENABLED="true" \
  -e ENVIRONMENT="development" \
  -p "${HOST_PORT}:${CONTAINER_PORT}" \
  -p "9090:9090" \
  --cpus 4 \
  --memory 1g \
  "$IMAGE_NAME"

# Wait for startup
echo ""
echo "⏳ Waiting for GraphOps to start..."
sleep 3

# Get container IP
GRAPHOPS_IP=$(container list | grep "$CONTAINER_NAME" | awk '{print $6}')

# Test health check
echo ""
echo "🏥 Testing health check..."
if container exec "$CONTAINER_NAME" /usr/local/bin/graphops --health-check 2>&1 | grep -q "PASSED"; then
    echo "   ✅ Health check passed!"
else
    echo "   ⚠️  Health check did not pass (container may still be starting)"
fi

# Show status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ GraphOps Started"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Service Info:"
echo "   Container: $CONTAINER_NAME"
echo "   IP:        $GRAPHOPS_IP"
echo "   Port:      localhost:${HOST_PORT} (13398)"
echo "   Metrics:   http://localhost:${HOST_PORT}/metrics"
echo ""
echo "🔗 Connections:"
echo "   Database:  $PGBOUNCER_IP:6432"
echo "   Graph:     $GRAPH_NAME"
echo ""
echo "🧪 Test Commands:"
echo "   Health:    container exec $CONTAINER_NAME /usr/local/bin/graphops --health-check"
echo "   Logs:      container logs $CONTAINER_NAME"
echo "   gRPC:      grpcurl -plaintext localhost:${HOST_PORT} list"
echo "   Metrics:   curl http://localhost:${HOST_PORT}/metrics"
echo ""
