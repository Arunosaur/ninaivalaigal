#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Check Jaeger status

set -euo pipefail

CONTAINER_NAME="ninaivalaigal-dev-jaeger"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Jaeger Distributed Tracing Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "✅ Jaeger: Running"
    echo ""

    # Get container info
    JAEGER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$CONTAINER_NAME")
    JAEGER_STATE=$(docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")
    JAEGER_HEALTH=$(docker inspect -f '{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "none")

    echo "📊 Container Info:"
    echo "   Status:     $JAEGER_STATE"
    echo "   Health:     $JAEGER_HEALTH"
    echo "   IP:         $JAEGER_IP"
    echo ""

    # Test endpoints
    echo "🔍 Endpoint Health:"
    if curl -s -f http://localhost:16686/ > /dev/null 2>&1; then
        echo "   ✅ UI (16686):       Accessible"
    else
        echo "   ❌ UI (16686):       Not responding"
    fi

    if nc -z localhost 4317 2>/dev/null; then
        echo "   ✅ OTLP gRPC (4317): Open"
    else
        echo "   ❌ OTLP gRPC (4317): Closed"
    fi

    if nc -z localhost 14268 2>/dev/null; then
        echo "   ✅ HTTP (14268):     Open"
    else
        echo "   ❌ HTTP (14268):     Closed"
    fi

    echo ""
    echo "📡 Access URLs:"
    echo "   UI:         http://localhost:16686"
    echo "   OTLP gRPC:  localhost:4317"
    echo "   OTLP HTTP:  localhost:4318"
    echo ""

    # Show recent logs
    echo "📝 Recent Logs (last 10 lines):"
    docker logs --tail 10 "$CONTAINER_NAME" 2>&1 | sed 's/^/   /'

else
    echo "❌ Jaeger: Not running"
    echo ""
    echo "Start with: ./scripts/nv-jaeger-start.sh"
fi

echo ""
