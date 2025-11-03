#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Import Grafana dashboards via API
# Usage: ./scripts/import-grafana-dashboards.sh [password]
#
# If password not provided, will prompt for it

set -euo pipefail

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
DASHBOARD_DIR="${DASHBOARD_DIR:-$(dirname "$0")/../config/grafana/dashboards}"

# Get password
if [ $# -eq 0 ]; then
    read -sp "Enter Grafana admin password: " GRAFANA_PASSWORD
    echo ""
else
    GRAFANA_PASSWORD="$1"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Importing Grafana Dashboards via API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Grafana URL: $GRAFANA_URL"
echo "User: $GRAFANA_USER"
echo "Dashboard Directory: $DASHBOARD_DIR"
echo ""

# Check if Grafana is accessible
if ! curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" "$GRAFANA_URL/api/health" >/dev/null 2>&1; then
    echo "❌ Cannot connect to Grafana at $GRAFANA_URL"
    echo "   Check if Grafana is running and credentials are correct"
    exit 1
fi

echo "✅ Connected to Grafana"
echo ""

# Import each dashboard
SUCCESS=0
FAILED=0

for dashboard_file in "$DASHBOARD_DIR"/*.json; do
    if [ ! -f "$dashboard_file" ]; then
        continue
    fi

    filename=$(basename "$dashboard_file")
    echo "📋 Importing: $filename"

    # Wrap dashboard in API format (Grafana API expects {"dashboard": {...}, "overwrite": false})
    # Our JSON files already have the dashboard object, so we check if they need wrapping
    if jq -e '.dashboard' "$dashboard_file" >/dev/null 2>&1; then
        # Already wrapped
        DASHBOARD_JSON=$(cat "$dashboard_file" | jq '. + {"overwrite": false}')
    else
        # Needs wrapping
        DASHBOARD_JSON=$(jq -n --argjson dashboard "$(cat "$dashboard_file")" '{dashboard: $dashboard, overwrite: false}')
    fi

    # Import via API
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
        -H "Content-Type: application/json" \
        -d "$DASHBOARD_JSON" \
        "$GRAFANA_URL/api/dashboards/db" 2>/dev/null)

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "200" ]; then
        DASHBOARD_TITLE=$(echo "$BODY" | jq -r '.dashboard.title // .title // "Unknown"' 2>/dev/null || echo "Unknown")
        echo "   ✅ Imported: $DASHBOARD_TITLE"
        SUCCESS=$((SUCCESS + 1))
    else
        ERROR_MSG=$(echo "$BODY" | jq -r '.message // .error // "Unknown error"' 2>/dev/null || echo "HTTP $HTTP_CODE")
        echo "   ❌ Failed: $ERROR_MSG"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Import Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Success: $SUCCESS"
echo "❌ Failed: $FAILED"
echo ""
echo "🌐 View dashboards at: $GRAFANA_URL/dashboards"
echo ""
