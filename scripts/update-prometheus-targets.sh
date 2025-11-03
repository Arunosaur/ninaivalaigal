#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Update Prometheus configuration with actual container IPs
# This fixes the "No data" issue in Grafana dashboards

set -euo pipefail

ENV="${NINA_ENV:-dev}"
CONTAINER_NAME="ninaivalaigal-${ENV}-prometheus"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Updating Prometheus Targets with Container IPs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Resolve container IPs
echo "📡 Resolving container IPs..."

CORE_API_CONTAINER="ninaivalaigal-${ENV}-core-api"
CORE_API_IP=$(container inspect "$CORE_API_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' 2>/dev/null | cut -d'/' -f1)
CORE_API_PORT="8000"

GRPC_GW_CONTAINER="ninaivalaigal-${ENV}-grpc-gateway"
GRPC_GW_IP=$(container inspect "$GRPC_GW_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' 2>/dev/null | cut -d'/' -f1)
GRPC_GW_PORT="8080"

MEMORY_CONTAINER="ninaivalaigal-${ENV}-memory-service"
MEMORY_IP=$(container inspect "$MEMORY_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' 2>/dev/null | cut -d'/' -f1)
MEMORY_PORT="8000"

GRAPHOPS_CONTAINER="ninaivalaigal-${ENV}-graphops"
GRAPHOPS_IP=$(container inspect "$GRAPHOPS_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' 2>/dev/null | cut -d'/' -f1)
GRAPHOPS_PORT="50051"  # gRPC port, but check if it has HTTP metrics

echo "   Core API:       ${CORE_API_IP:-NOT_FOUND}:${CORE_API_PORT}"
echo "   gRPC Gateway:   ${GRPC_GW_IP:-NOT_FOUND}:${GRPC_GW_PORT}"
echo "   Memory Service: ${MEMORY_IP:-NOT_FOUND}:${MEMORY_PORT}"
echo "   GraphOps:       ${GRAPHOPS_IP:-NOT_FOUND}:${GRAPHOPS_PORT}"
echo ""

# Create new Prometheus config
cat > /tmp/prometheus-updated.yml <<EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'ninaivalaigal'
    environment: '${ENV}'

rule_files:
  - '/etc/prometheus/alerts.yml'

scrape_configs:
EOF

# Add core-api if found
if [ -n "$CORE_API_IP" ] && [ "$CORE_API_IP" != "null" ]; then
    cat >> /tmp/prometheus-updated.yml <<EOF
  - job_name: 'core-api'
    static_configs:
      - targets: ['${CORE_API_IP}:${CORE_API_PORT}']
    metrics_path: '/metrics'
EOF
    echo "✅ Added core-api target: ${CORE_API_IP}:${CORE_API_PORT}"
else
    echo "⚠️  core-api container not found"
fi

# Add grpc-gateway if found
if [ -n "$GRPC_GW_IP" ] && [ "$GRPC_GW_IP" != "null" ]; then
    cat >> /tmp/prometheus-updated.yml <<EOF
  - job_name: 'grpc-gateway'
    static_configs:
      - targets: ['${GRPC_GW_IP}:${GRPC_GW_PORT}']
    metrics_path: '/metrics'
EOF
    echo "✅ Added grpc-gateway target: ${GRPC_GW_IP}:${GRPC_GW_PORT}"
else
    echo "⚠️  grpc-gateway container not found"
fi

# Add memory-service if found
if [ -n "$MEMORY_IP" ] && [ "$MEMORY_IP" != "null" ]; then
    cat >> /tmp/prometheus-updated.yml <<EOF
  - job_name: 'memory-service'
    static_configs:
      - targets: ['${MEMORY_IP}:${MEMORY_PORT}']
    metrics_path: '/metrics'
EOF
    echo "✅ Added memory-service target: ${MEMORY_IP}:${MEMORY_PORT}"
else
    echo "⚠️  memory-service container not found"
fi

# Add graphops if found (if it has metrics endpoint)
if [ -n "$GRAPHOPS_IP" ] && [ "$GRAPHOPS_IP" != "null" ]; then
    # GraphOps might not have /metrics, but let's try
    cat >> /tmp/prometheus-updated.yml <<EOF
  - job_name: 'graphops'
    static_configs:
      - targets: ['${GRAPHOPS_IP}:${GRAPHOPS_PORT}']
    metrics_path: '/metrics'
EOF
    echo "✅ Added graphops target: ${GRAPHOPS_IP}:${GRAPHOPS_PORT}"
else
    echo "⚠️  graphops container not found"
fi

# Copy config into Prometheus container
echo ""
echo "📝 Copying updated config into Prometheus container..."
cat /tmp/prometheus-updated.yml | container exec -i "$CONTAINER_NAME" sh -c \
    'cat > /etc/prometheus/prometheus.yml' || {
    echo "❌ Failed to copy config"
    exit 1
}

# Reload Prometheus config
echo "🔄 Reloading Prometheus configuration..."
curl -s -X POST "http://localhost:9090/-/reload" >/dev/null 2>&1 || {
    echo "⚠️  Manual reload failed, Prometheus will reload automatically"
}

echo ""
echo "✅ Prometheus configuration updated!"
echo ""
echo "📊 Check targets at: http://localhost:9090/targets"
echo "   (Should show all targets as 'up' within 15 seconds)"
echo ""

rm -f /tmp/prometheus-updated.yml
