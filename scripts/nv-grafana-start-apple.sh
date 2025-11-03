#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Start Grafana for monitoring dashboards using Apple Container CLI (US#102)

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📈 Starting Grafana Monitoring Dashboards (Apple Container CLI)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Configuration (following ports.nv.yaml)
ENV="${NINA_ENV:-dev}"
CONTAINER_NAME="ninaivalaigal-${ENV}-grafana"
IMAGE_NAME="grafana/grafana:10.2.0"

# Ports (from ports.nv.yaml)
HOST_PORT=3001        # Host port (US-90 requirement: localhost:3001)
CONTAINER_PORT=3000   # Container internal port (Grafana default)

# Configuration directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="${ROOT_DIR}/config/grafana"
GRAFANA_DATASOURCES_DIR="${CONFIG_DIR}/datasources"
GRAFANA_DASHBOARDS_DIR="${CONFIG_DIR}/dashboards"

# Create directories
mkdir -p "$GRAFANA_DATASOURCES_DIR"
mkdir -p "$GRAFANA_DASHBOARDS_DIR"

# Create Prometheus datasource configuration
echo "📝 Creating Prometheus datasource configuration..."
cat > "${GRAFANA_DATASOURCES_DIR}/prometheus.yml" <<EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://host.docker.internal:9090
    isDefault: true
    editable: true
    jsonData:
      httpMethod: POST
      timeInterval: 15s
EOF
echo "✅ Created Prometheus datasource config"

# Create dashboard provisioning configuration
echo "📝 Creating dashboard provisioning configuration..."
cat > "${GRAFANA_DATASOURCES_DIR}/../dashboards.yml" <<EOF
apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF
echo "✅ Created dashboard provisioning config"

# Stop existing container if running
if container list | grep -q "$CONTAINER_NAME"; then
    echo "🛑 Stopping existing $CONTAINER_NAME..."
    container stop "$CONTAINER_NAME" || true
    container rm "$CONTAINER_NAME" || true
    sleep 2
fi

# Resolve Prometheus container IP (Apple Container CLI pattern)
echo "📡 Resolving Prometheus container IP..."
PROMETHEUS_CONTAINER="ninaivalaigal-${ENV}-prometheus"
PROMETHEUS_IP=$(container inspect "$PROMETHEUS_CONTAINER" 2>/dev/null \
    | jq -r '.[0].networks[0].address' \
    | cut -d'/' -f1)

if [ -n "$PROMETHEUS_IP" ] && [ "$PROMETHEUS_IP" != "null" ]; then
    PROMETHEUS_URL="http://${PROMETHEUS_IP}:9090"
    echo "   Using Prometheus at: $PROMETHEUS_URL"
    # Update datasource config with container IP
    sed -i.bak "s|http://host.docker.internal:9090|${PROMETHEUS_URL}|g" "${GRAFANA_DATASOURCES_DIR}/prometheus.yml"
else
    echo "   ⚠️  Prometheus container not found, using host.docker.internal"
    PROMETHEUS_URL="http://host.docker.internal:9090"
fi

# Create data directory for Grafana
GRAFANA_DATA_DIR="${ROOT_DIR}/.data/grafana-${ENV}"
mkdir -p "$GRAFANA_DATA_DIR"
echo "📁 Grafana data directory: $GRAFANA_DATA_DIR"

# Start Grafana container (following Apple Container CLI pattern - no bind mounts)
# Configuration will be copied into container after startup
echo ""
echo "🚀 Starting Grafana..."
echo "   Port: ${HOST_PORT}:${CONTAINER_PORT} (from ports.nv.yaml)"
echo "   Config: Will be copied into container after startup"

# Start container without volume mounts (following Jaeger pattern)
container run -d \
  --name "$CONTAINER_NAME" \
  -p "${HOST_PORT}:${CONTAINER_PORT}" \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -e GF_SERVER_ROOT_URL=http://localhost:${HOST_PORT} \
  -e GF_INSTALL_PLUGINS=grafana-piechart-panel \
  --cpus 1 \
  --memory 512m \
  "$IMAGE_NAME"

# Wait a moment for container to start
echo "⏳ Waiting for container to be ready..."
sleep 5

# Check if container is running
if ! container list | grep -q "$CONTAINER_NAME.*running"; then
    echo "❌ Container failed to start"
    echo "   Check logs: container logs $CONTAINER_NAME"
    exit 1
fi

# Copy datasource config into container
echo "📝 Copying Grafana datasource configuration..."
cat "${GRAFANA_DATASOURCES_DIR}/prometheus.yml" | container exec -i "$CONTAINER_NAME" sh -c 'mkdir -p /etc/grafana/provisioning/datasources && cat > /etc/grafana/provisioning/datasources/prometheus.yml' || {
    echo "⚠️  Failed to copy datasource config, will try later"
}

# Copy dashboard provisioning config
echo "📝 Copying dashboard provisioning configuration..."
cat "${GRAFANA_DASHBOARDS_DIR}/../dashboards.yml" | container exec -i "$CONTAINER_NAME" sh -c 'mkdir -p /etc/grafana/provisioning/dashboards && cat > /etc/grafana/provisioning/dashboards/default.yml' || {
    echo "⚠️  Failed to copy dashboard config, will try later"
}

# Wait for Grafana to be ready
echo ""
echo "⏳ Waiting for Grafana to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Grafana health API returns JSON, check for "database":"ok"
    if curl -s "http://localhost:${HOST_PORT}/api/health" | grep -q '"database":"ok"'; then
        echo ""
        echo "✅ Grafana is ready!"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📈 Grafana Monitoring Dashboards"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "📍 Grafana UI: http://localhost:${HOST_PORT} (from ports.nv.yaml)"
        echo "   Username: admin"
        echo "   Password: admin"
        echo ""
        echo "📊 Dashboard directory: ${GRAFANA_DASHBOARDS_DIR}"
        echo "🔌 Datasource: Prometheus (auto-configured)"
        echo ""
        exit 0
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 2
done

echo ""
echo "❌ Grafana failed to start within ${MAX_RETRIES} retries"
echo "   Check logs: container logs $CONTAINER_NAME"
exit 1
