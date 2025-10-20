#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Start GraphOps gRPC Service (Task #49)

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Starting GraphOps gRPC Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Configuration
CONTAINER_NAME="ninaivalaigal-dev-graphops"
IMAGE_NAME="ninaivalaigal-graphops:arm64"
GRAPH_NAME="ninaivalaigal_intelligence_dev"

# Port from ports.nv.yaml (apple.dev.graphops)
HOST_PORT=13398
CONTAINER_PORT=8000

# Stop existing container if running
if container list | grep -q "$CONTAINER_NAME"; then
    echo "🛑 Stopping existing $CONTAINER_NAME..."
    container stop "$CONTAINER_NAME" || true
    container rm "$CONTAINER_NAME" || true
    sleep 2
fi

# Get PgBouncer IP dynamically
echo "📡 Getting PgBouncer IP..."
PGBOUNCER_IP=$(container list | grep ninaivalaigal-dev-pgbouncer | awk '{print $6}')

if [ -z "$PGBOUNCER_IP" ]; then
    echo "❌ Error: PgBouncer not running"
    echo "   Start PgBouncer first: ./scripts/nv-pgbouncer-start.sh"
    exit 1
fi

echo "   PgBouncer IP: $PGBOUNCER_IP"

# Build DATABASE_URL dynamically
DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGBOUNCER_IP}:6432/ninaivalaigal_dev"  # pragma: allowlist secret

# Start GraphOps container
echo ""
echo "🚀 Starting GraphOps..."
container run -d \
  --name "$CONTAINER_NAME" \
  -e DATABASE_URL="$DATABASE_URL" \
  -e GRAPHOPS_GRAPH="$GRAPH_NAME" \
  -e GRAPHOPS_GRPC_ADDR="0.0.0.0:${CONTAINER_PORT}" \
  -e GRAPHOPS_METRICS_ADDR="0.0.0.0:${CONTAINER_PORT}" \
  -e RUST_LOG=info \
  -p "${HOST_PORT}:${CONTAINER_PORT}" \
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
