#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Start Prometheus for metrics collection using Apple Container CLI (US#102)

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Starting Prometheus Metrics Collection (Apple Container CLI)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Configuration (following ports.nv.yaml)
ENV="${NINA_ENV:-dev}"
CONTAINER_NAME="ninaivalaigal-${ENV}-prometheus"
IMAGE_NAME="prom/prometheus:v2.51.2"

# Ports (from ports.nv.yaml)
HOST_PORT=9090        # Host port for external access
CONTAINER_PORT=9090   # Container internal port

# Configuration directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="${ROOT_DIR}/monitoring"
PROMETHEUS_CONFIG="${CONFIG_DIR}/prometheus.yml"

# Create Prometheus config if it doesn't exist
if [ ! -f "$PROMETHEUS_CONFIG" ]; then
    echo "📝 Creating Prometheus configuration..."
    mkdir -p "$CONFIG_DIR"
    cat > "$PROMETHEUS_CONFIG" <<EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'ninaivalaigal'
    environment: '${ENV}'

rule_files:
  - '/etc/prometheus/alerts.yml'

scrape_configs:
  - job_name: 'grpc-gateway'
    static_configs:
      - targets: ['host.docker.internal:13395']
    metrics_path: '/metrics'

  - job_name: 'memory-service'
    static_configs:
      - targets: ['host.docker.internal:13393']
    metrics_path: '/metrics'

  - job_name: 'core-api'
    static_configs:
      - targets: ['host.docker.internal:13390']
    metrics_path: '/metrics'

  - job_name: 'graphops'
    static_configs:
      - targets: ['host.docker.internal:13398']
    metrics_path: '/metrics'
EOF
    echo "✅ Created ${PROMETHEUS_CONFIG}"
fi

# Stop existing container if running
if container list | grep -q "$CONTAINER_NAME"; then
    echo "🛑 Stopping existing $CONTAINER_NAME..."
    container stop "$CONTAINER_NAME" || true
    container rm "$CONTAINER_NAME" || true
    sleep 2
fi

# Create data directory for Prometheus
PROMETHEUS_DATA_DIR="${ROOT_DIR}/.data/prometheus-${ENV}"
mkdir -p "$PROMETHEUS_DATA_DIR"
echo "📁 Prometheus data directory: $PROMETHEUS_DATA_DIR"

# Start Prometheus container (following Apple Container CLI pattern - no bind mounts)
# Config will be copied into container after startup
echo ""
echo "🚀 Starting Prometheus..."
echo "   Port: ${HOST_PORT}:${CONTAINER_PORT} (from ports.nv.yaml)"
echo "   Config: Will be copied into container after startup"

# Start container without config mount (following Jaeger pattern)
container run -d \
  --name "$CONTAINER_NAME" \
  -p "${HOST_PORT}:${CONTAINER_PORT}" \
  --cpus 1 \
  --memory 1g \
  "$IMAGE_NAME" \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --storage.tsdb.retention.time=30d \
  --web.console.libraries=/usr/share/prometheus/console_libraries \
  --web.console.templates=/usr/share/prometheus/consoles \
  --web.enable-lifecycle

# Wait a moment for container to start
sleep 3

# Copy config file into container (workaround for Apple Container CLI bind mount issues)
echo "📝 Copying Prometheus configuration into container..."
cat "$PROMETHEUS_CONFIG" | container exec -i "$CONTAINER_NAME" sh -c 'cat > /etc/prometheus/prometheus.yml'

# Reload Prometheus configuration
echo "🔄 Reloading Prometheus configuration..."
curl -X POST "http://localhost:${HOST_PORT}/-/reload" 2>/dev/null || echo "   (Prometheus will use config on next restart)"

# Wait for Prometheus to be ready
echo ""
echo "⏳ Waiting for Prometheus to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s "http://localhost:${HOST_PORT}/-/ready" > /dev/null 2>&1; then
        echo ""
        echo "✅ Prometheus is ready!"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📊 Prometheus Metrics Collection"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "📍 Prometheus UI: http://localhost:${HOST_PORT} (from ports.nv.yaml)"
        echo "📍 Metrics: http://localhost:${HOST_PORT}/metrics"
        echo "📍 Targets: http://localhost:${HOST_PORT}/targets"
        echo "📍 Alerts: http://localhost:${HOST_PORT}/alerts"
        echo ""
        echo "🔍 Check targets: curl http://localhost:${HOST_PORT}/api/v1/targets"
        echo ""
        exit 0
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 2
done

echo ""
echo "❌ Prometheus failed to start within ${MAX_RETRIES} retries"
echo "   Check logs: container logs $CONTAINER_NAME"
exit 1
