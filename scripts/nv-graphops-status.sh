#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Check GraphOps gRPC Service Status

set -euo pipefail

CONTAINER_NAME="ninaivalaigal-dev-graphops"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 GraphOps gRPC Service Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if container list | grep -q "$CONTAINER_NAME"; then
    echo "✅ GraphOps: Running"
    echo ""

    # Get container info
    GRAPHOPS_IP=$(container list | grep "$CONTAINER_NAME" | awk '{print $6}')
    GRAPHOPS_STATE=$(container list | grep "$CONTAINER_NAME" | awk '{print $5}')

    echo "📊 Container Info:"
    echo "   Name:   $CONTAINER_NAME"
    echo "   IP:     $GRAPHOPS_IP"
    echo "   State:  $GRAPHOPS_STATE"
    echo ""

    echo "🔗 Endpoints:"
    echo "   Port:    localhost:13398"
    echo "   Metrics: http://localhost:13398/metrics"
    echo ""

    # Test health check
    echo "🏥 Health Check:"
    if container exec "$CONTAINER_NAME" /usr/local/bin/graphops --health-check 2>&1 | grep -q "PASSED"; then
        echo "   ✅ Health check passed"
    else
        echo "   ⚠️  Health check failed or service starting"
    fi

    echo ""
    echo "📝 Recent Logs:"
    container logs "$CONTAINER_NAME" 2>&1 | tail -10 | sed 's/^/   /'

else
    echo "❌ GraphOps: Not running"
    echo ""
    echo "Start with: ./scripts/nv-graphops-start.sh"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
