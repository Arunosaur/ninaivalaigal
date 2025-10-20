#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC

# Load Test Traefik API Gateway
# Task #83: API Gateway Performance Testing

set -euo pipefail

GATEWAY_URL="${GATEWAY_URL:-http://localhost}"
DURATION="${DURATION:-30}"
CONNECTIONS="${CONNECTIONS:-100}"
THREADS="${THREADS:-4}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚡ Load Testing Traefik API Gateway"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Configuration:"
echo "  URL: $GATEWAY_URL/health"
echo "  Duration: ${DURATION}s"
echo "  Connections: $CONNECTIONS"
echo "  Threads: $THREADS"
echo ""

# Check if wrk is installed
if command -v wrk >/dev/null 2>&1; then
    echo "Using wrk for load testing..."
    echo ""
    wrk -t${THREADS} -c${CONNECTIONS} -d${DURATION}s "${GATEWAY_URL}/health"

elif command -v ab >/dev/null 2>&1; then
    echo "Using Apache Bench for load testing..."
    echo ""
    REQUESTS=$((CONNECTIONS * 10))
    ab -n ${REQUESTS} -c ${CONNECTIONS} "${GATEWAY_URL}/health"

else
    echo "⚠️  No load testing tool found (wrk or ab)"
    echo ""
    echo "Install wrk:"
    echo "  brew install wrk  (macOS)"
    echo "  apt-get install wrk  (Ubuntu)"
    echo ""
    echo "Or install Apache Bench:"
    echo "  brew install httpd  (macOS)"
    echo "  apt-get install apache2-utils  (Ubuntu)"
    echo ""

    # Fallback: Simple curl-based test
    echo "Running simple load test with curl..."
    echo ""

    START=$(date +%s)
    SUCCESS=0
    FAILED=0

    for i in $(seq 1 100); do
        if curl -s -o /dev/null -w "%{http_code}" "${GATEWAY_URL}/health" | grep -q "200"; then
            ((SUCCESS++))
        else
            ((FAILED++))
        fi
    done

    END=$(date +%s)
    DURATION=$((END - START))
    RPS=$(echo "scale=2; 100 / $DURATION" | bc)

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Results:"
    echo "  Total Requests: 100"
    echo "  Successful: $SUCCESS"
    echo "  Failed: $FAILED"
    echo "  Duration: ${DURATION}s"
    echo "  Requests/sec: $RPS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

echo ""
echo "✅ Load test complete"
