#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Check Core API service status

NINA_ENV=${NINA_ENV:-dev}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-core-api"
# Port allocation per config/ports.nv.yaml (apple.dev.api = 13390)
PORT_EXTERNAL=13390

echo "📊 Core API Service Status"
echo "=========================="
echo ""

# Check if container exists and is running
if container list | grep -q "$CONTAINER_NAME"; then
    echo "✅ Container Status: RUNNING"

    # Get container IP
    CORE_API_IP=$(container inspect "$CONTAINER_NAME" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
    echo "   Container IP: $CORE_API_IP"
    echo "   External Port: $PORT_EXTERNAL"

    # Check health endpoint
    echo ""
    echo "🏥 Health Check:"
    if curl -s "http://localhost:${PORT_EXTERNAL}/health" > /tmp/core-api-health.json 2>&1; then
        echo "   ✅ Service is responding"
        echo "   Response:"
        cat /tmp/core-api-health.json | jq '.' 2>/dev/null || cat /tmp/core-api-health.json
        rm -f /tmp/core-api-health.json
    else
        echo "   ❌ Service not responding on port $PORT_EXTERNAL"
    fi

    # Show recent logs
    echo ""
    echo "📝 Recent Logs (last 10 lines):"
    echo "---"
    container logs --tail 10 "$CONTAINER_NAME" 2>&1
    echo "---"

else
    echo "❌ Container Status: NOT RUNNING"
    echo "   Container: $CONTAINER_NAME"
    echo ""
    echo "To start:"
    echo "   ./nv-core-api-start.sh"
fi

echo ""
echo "📍 Quick Commands:"
echo "   Start:   ./nv-core-api-start.sh"
echo "   Stop:    ./nv-core-api-stop.sh"
echo "   Logs:    container logs -f $CONTAINER_NAME"
echo "   List:    container list | grep ninaivalaigal"
echo ""
