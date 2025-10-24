#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Start Traefik API Gateway
# US #83: API Gateway Path Routing

set -euo pipefail

NINA_ENV=${NINA_ENV:-dev}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-gateway"
IMAGE_NAME="ninaivalaigal-gateway:arm64"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Starting Traefik API Gateway"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Stop existing container if running
if container list | grep -q "$CONTAINER_NAME"; then
    echo "🛑 Stopping existing $CONTAINER_NAME..."
    container stop "$CONTAINER_NAME" || true
    container rm "$CONTAINER_NAME" || true
    sleep 2
fi

# Get dynamic IPs for all services
echo "📡 Detecting service IPs..."
CORE_API_IP=$(container list | grep "ninaivalaigal-${NINA_ENV}-core-api" | awk '{print $6}')
BUSINESS_IP=$(container list | grep "ninaivalaigal-${NINA_ENV}-business-service" | awk '{print $6}')
ADMIN_IP=$(container list | grep "ninaivalaigal-${NINA_ENV}-admin-vendor" | awk '{print $6}')
MEMORY_IP=$(container list | grep "ninaivalaigal-${NINA_ENV}-memory-service" | awk '{print $6}')
GRAPH_IP=$(container list | grep "ninaivalaigal-${NINA_ENV}-graph-service" | awk '{print $6}')
GRPC_GW_IP=$(container list | grep "ninaivalaigal-${NINA_ENV}-grpc-gateway" | awk '{print $6}')

echo "   Core API:        ${CORE_API_IP:-NOT FOUND}"
echo "   Business:        ${BUSINESS_IP:-NOT FOUND}"
echo "   Admin/Vendor:    ${ADMIN_IP:-NOT FOUND}"
echo "   Memory Service:  ${MEMORY_IP:-NOT FOUND}"
echo "   Graph Service:   ${GRAPH_IP:-NOT FOUND}"
echo "   gRPC Gateway:    ${GRPC_GW_IP:-NOT FOUND}"

# Generate dynamic config
CONFIG_DIR="$(cd "$(dirname "$0")/../config/traefik" && pwd)"
sed -e "s|CORE_API_IP|${CORE_API_IP:-192.168.66.93}|g" \
    -e "s|BUSINESS_IP|${BUSINESS_IP:-192.168.66.99}|g" \
    -e "s|ADMIN_IP|${ADMIN_IP:-192.168.66.98}|g" \
    -e "s|MEMORY_IP|${MEMORY_IP:-192.168.66.103}|g" \
    -e "s|GRAPH_IP|${GRAPH_IP:-192.168.66.94}|g" \
    -e "s|GRPC_GW_IP|${GRPC_GW_IP:-192.168.66.92}|g" \
    "${CONFIG_DIR}/dynamic.yml.template" > "${CONFIG_DIR}/dynamic-runtime.yml"

# Rebuild image with runtime config
echo "🔨 Rebuilding gateway image with dynamic IPs..."
cp "${CONFIG_DIR}/dynamic-runtime.yml" "$(dirname "$0")/../containers/traefik/dynamic.yml"
docker build --quiet --platform linux/arm64 -t "$IMAGE_NAME" "$(dirname "$0")/../containers/traefik" > /dev/null
docker save -o /tmp/gw.tar "$IMAGE_NAME"
container image load --input /tmp/gw.tar > /dev/null
rm /tmp/gw.tar

# Start Traefik on port 8888 (avoiding port 80 conflicts)
echo "🚀 Starting Traefik..."
echo "   Gateway will be accessible via http://localhost:8888"
container run -d \
  --name "$CONTAINER_NAME" \
  -p 8888:80 \
  -p 8081:8080 \
  "$IMAGE_NAME"

sleep 3

# Get container IP
GATEWAY_IP=$(container list | grep "$CONTAINER_NAME" | awk '{print $6}')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Traefik Gateway Started"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Gateway Info:"
echo "   Container: $CONTAINER_NAME"
echo "   IP:        $GATEWAY_IP"
echo "   HTTP:      http://localhost:8888"
echo "   Dashboard: http://localhost:8080"
echo ""
echo "🔗 API Routes (via http://localhost:8888):"
echo "   /api/auth     → Core API (192.168.66.93:8000)"
echo "   /api/memory   → Memory Service (192.168.66.103:8000)"
echo "   /api/graph    → Graph Service (192.168.66.94:8000)"
echo "   /api/billing  → Business Service (192.168.66.99:8000)"
echo "   /api/admin    → Admin/Vendor (192.168.66.98:8000)"
echo "   /grpc         → gRPC Gateway (192.168.66.92:8000)"
echo ""
echo "🧪 Test Commands:"
echo "   curl http://localhost:8888/api/auth/health"
echo "   curl http://localhost:8888/api/memory/health"
echo "   curl http://localhost:8888/api/graph/health"
echo ""
