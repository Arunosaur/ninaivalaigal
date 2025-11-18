#!/usr/bin/env bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Start Traefik API Gateway
# US #83: API Gateway Path Routing
# SPEC-100: Runtime-Agnostic Federation
# SPEC-145: Multi-Runtime Multi-Architecture Container Builds

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load environment variables from configs/env-{env}.env (STANDARDS COMPLIANCE)
NINA_ENV=${NINA_ENV:-dev}
ENV_FILE="$PROJECT_ROOT/configs/env-${NINA_ENV}.env"
if [ -f "$ENV_FILE" ]; then
    # shellcheck source=/dev/null
    source "$ENV_FILE"
    echo "✅ Loaded environment from $ENV_FILE"
else
    echo "⚠️  $ENV_FILE not found, using defaults"
fi

# Configuration
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-gateway"
IMAGE_NAME="nina-gateway:arm64"
TRAEFIK_DIR="$PROJECT_ROOT/deployment/traefik"
CONTAINERS_DIR="$PROJECT_ROOT/containers/traefik"

# Ports (standard HTTP/HTTPS, not subject to runtime offsets per ports.nv.yaml)
PORT_HTTP=80
PORT_HTTPS=443
PORT_DASHBOARD=8080

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Starting Traefik API Gateway"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Configuration:"
echo "   Environment: $NINA_ENV"
echo "   Container: $CONTAINER_NAME"
echo "   Image: $IMAGE_NAME"
echo "   HTTP: $PORT_HTTP"
echo "   HTTPS: $PORT_HTTPS"
echo "   Dashboard: $PORT_DASHBOARD"
echo ""

# Step 1: Check if image exists, build if needed
if ! container image list | grep -q "$IMAGE_NAME"; then
    echo "🔨 Building gateway image..."
    cd "$CONTAINERS_DIR"

    # Copy deployment config to containers dir for build
    cp "$TRAEFIK_DIR/traefik.yml" "$CONTAINERS_DIR/traefik.yml"
    mkdir -p "$CONTAINERS_DIR/dynamic"
    cp "$TRAEFIK_DIR/dynamic.yml" "$CONTAINERS_DIR/dynamic/dynamic.yml"

    # Build using Docker (SPEC-145: Docker → Apple Container CLI workflow)
    docker build --platform linux/arm64 -t "$IMAGE_NAME" "$CONTAINERS_DIR"

    # Export and load into Apple Container CLI
    docker save "$IMAGE_NAME" -o /tmp/gateway.tar
    container image load --input /tmp/gateway.tar
    rm /tmp/gateway.tar

    echo "✅ Gateway image built and loaded"
else
    echo "✅ Gateway image exists"
fi

# Step 2: Stop existing container if running
if container list | grep -q "$CONTAINER_NAME"; then
    echo "🛑 Stopping existing $CONTAINER_NAME..."
    container stop "$CONTAINER_NAME" || true
    container rm "$CONTAINER_NAME" || true
    sleep 2
fi

# Step 3: Generate dynamic configuration with resolved container IPs
echo "🔧 Generating dynamic configuration with resolved container IPs..."
"$SCRIPT_DIR/generate-traefik-dynamic-config.sh" "$TRAEFIK_DIR/dynamic.yml" || {
    echo "❌ Error: Failed to generate dynamic configuration"
    exit 1
}
echo "✅ Dynamic configuration generated"
echo ""

# Step 4: Verify configuration files exist
if [ ! -f "$TRAEFIK_DIR/traefik.yml" ]; then
    echo "❌ Error: $TRAEFIK_DIR/traefik.yml not found"
    exit 1
fi

if [ ! -f "$TRAEFIK_DIR/dynamic.yml" ]; then
    echo "❌ Error: $TRAEFIK_DIR/dynamic.yml not found"
    exit 1
fi

# Step 5: Start Traefik gateway
echo "🚀 Starting Traefik gateway..."
echo "   Using dynamically resolved container IPs for service discovery"
echo ""

container run -d \
  --name "$CONTAINER_NAME" \
  -p "$PORT_HTTP:80" \
  -p "$PORT_HTTPS:443" \
  -p "$PORT_DASHBOARD:8080" \
  -v "$TRAEFIK_DIR/traefik.yml:/etc/traefik/traefik.yml:ro" \
  -v "$TRAEFIK_DIR/dynamic.yml:/etc/traefik/dynamic/dynamic.yml:ro" \
  -v traefik-certs:/letsencrypt \
  -v traefik-logs:/var/log/traefik \
  "$IMAGE_NAME"

sleep 3

# Step 5: Verify container is running
if ! container list | grep -q "$CONTAINER_NAME"; then
    echo "❌ Error: Gateway container failed to start"
    echo "📝 Check logs: container logs $CONTAINER_NAME"
    exit 1
fi

# Get container IP
GATEWAY_IP=$(container inspect "$CONTAINER_NAME" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1 || echo "N/A")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Traefik Gateway Started Successfully"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Gateway Info:"
echo "   Container: $CONTAINER_NAME"
echo "   IP:        ${GATEWAY_IP}"
echo "   HTTP:      http://localhost:$PORT_HTTP"
echo "   HTTPS:     https://localhost:$PORT_HTTPS"
echo "   Dashboard: http://localhost:$PORT_DASHBOARD"
echo ""
echo "🔗 API Routes (via http://localhost:$PORT_HTTP):"
echo "   /api/auth, /api/users, /api/teams, /api/orgs, /api/acl"
echo "      → Core API (ninaivalaigal-${NINA_ENV}-core-api:8000)"
echo ""
echo "   /api/billing, /api/usage, /api/analytics"
echo "      → Business Service (ninaivalaigal-${NINA_ENV}-business-service:8000)"
echo ""
echo "   /api/admin, /api/vendor"
echo "      → Admin/Vendor Service (ninaivalaigal-${NINA_ENV}-admin-vendor-service:8000)"
echo ""
echo "   /api/memory, /api/recall"
echo "      → Memory Service (ninaivalaigal-${NINA_ENV}-memory-service:8000)"
echo ""
echo "   /api/graph, /api/intelligence"
echo "      → Graph Service (ninaivalaigal-${NINA_ENV}-graph-service:8000)"
echo ""
echo "   /grpc"
echo "      → gRPC Gateway (ninaivalaigal-${NINA_ENV}-grpc-gateway:13395)"
echo ""
echo "   /health, /ping"
echo "      → Gateway Health Check"
echo ""
echo "   /metrics"
echo "      → Prometheus Metrics"
echo ""
echo "🧪 Test Commands:"
echo "   curl http://localhost:$PORT_HTTP/health"
echo "   curl http://localhost:$PORT_HTTP/api/auth/health"
echo "   curl http://localhost:$PORT_HTTP/api/memory/health"
echo "   curl http://localhost:$PORT_HTTP/api/graph/health"
echo "   curl http://localhost:$PORT_HTTP/metrics"
echo ""
echo "📝 View Logs:"
echo "   container logs -f $CONTAINER_NAME"
echo ""
