#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Load Grafana dashboards into running container (US#102)
# This script copies dashboard JSON files into the Grafana container
# Dashboards will be auto-loaded by Grafana within 10 seconds

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Loading Grafana Dashboards into Container"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Configuration
ENV="${NINA_ENV:-dev}"
CONTAINER_NAME="ninaivalaigal-${ENV}-grafana"

# Dashboard directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DASHBOARD_DIR="${ROOT_DIR}/config/grafana/dashboards"
PROVISIONING_DIR="/etc/grafana/provisioning/dashboards"

# Check if container is running
if ! container list | grep -q "$CONTAINER_NAME.*running"; then
    echo "❌ Grafana container '$CONTAINER_NAME' is not running"
    echo "   Start Grafana first: ./scripts/nv-grafana-start-apple.sh"
    exit 1
fi

# Check if dashboard directory exists
if [ ! -d "$DASHBOARD_DIR" ]; then
    echo "❌ Dashboard directory not found: $DASHBOARD_DIR"
    exit 1
fi

# Count dashboard files
DASHBOARD_COUNT=$(find "$DASHBOARD_DIR" -name "*.json" | wc -l | tr -d ' ')
if [ "$DASHBOARD_COUNT" -eq 0 ]; then
    echo "❌ No dashboard JSON files found in $DASHBOARD_DIR"
    exit 1
fi

echo "📁 Found $DASHBOARD_COUNT dashboard file(s) in $DASHBOARD_DIR"
echo ""

# Copy each dashboard into container
COPIED=0
for dashboard in "$DASHBOARD_DIR"/*.json; do
    if [ ! -f "$dashboard" ]; then
        continue
    fi

    filename=$(basename "$dashboard")
    echo "📋 Copying: $filename"

    # Create provisioning directory and copy dashboard
    if cat "$dashboard" | container exec -i "$CONTAINER_NAME" sh -c \
        "mkdir -p $PROVISIONING_DIR && cat > $PROVISIONING_DIR/$filename"; then
        echo "   ✅ Copied successfully"
        COPIED=$((COPIED + 1))
    else
        echo "   ❌ Failed to copy"
    fi
done

echo ""
if [ "$COPIED" -eq 0 ]; then
    echo "❌ No dashboards were copied"
    exit 1
fi

echo "✅ Copied $COPIED/$DASHBOARD_COUNT dashboard(s) into container"
echo ""
echo "⏳ Grafana will auto-load dashboards within 10 seconds"
echo "   (configured refresh interval: 10s)"
echo ""
echo "📊 To manually trigger reload:"
echo "   curl -X POST http://localhost:3001/api/admin/provisioning/dashboards/reload \\"
echo "     -u admin:admin"
echo ""
echo "🌐 View dashboards at: http://localhost:3001/dashboards"
echo ""
