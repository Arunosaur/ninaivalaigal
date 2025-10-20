#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC

# Check Traefik API Gateway Status
# Task #83: API Gateway Deployment

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Traefik API Gateway Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if gateway is running
if docker ps --format "{{.Names}}" | grep -q "^ninaivalaigal-gateway$"; then
    echo "✅ Gateway: Running"

    # Get container status
    STATUS=$(docker inspect ninaivalaigal-gateway --format '{{.State.Status}}')
    HEALTH=$(docker inspect ninaivalaigal-gateway --format '{{.State.Health.Status}}' 2>/dev/null || echo "no healthcheck")

    echo "   Status: $STATUS"
    echo "   Health: $HEALTH"

    # Check ports
    echo ""
    echo "📡 Ports:"
    docker port ninaivalaigal-gateway | sed 's/^/   /'

    # Test endpoints
    echo ""
    echo "🔍 Endpoint Tests:"

    # Test dashboard
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/overview 2>/dev/null | grep -q "200"; then
        echo "   ✅ Dashboard: http://localhost:8080"
    else
        echo "   ❌ Dashboard: Not responding"
    fi

    # Test ping
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:80/ping 2>/dev/null | grep -q "200"; then
        echo "   ✅ Health: http://localhost/health"
    else
        echo "   ⚠️  Health: Not responding"
    fi

    echo ""
    echo "📝 Logs (last 10 lines):"
    docker logs --tail 10 ninaivalaigal-gateway 2>&1 | sed 's/^/   /'

else
    echo "❌ Gateway: Not running"
    echo ""
    echo "Start with: ./scripts/gateway-start.sh"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
