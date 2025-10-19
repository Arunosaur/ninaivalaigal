#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Health Endpoints Test Script
# Tests all health endpoints and displays results

set -e

# Configuration
API_URL="${API_URL:-http://localhost:13390}"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🏥 Testing Health Endpoints"
echo "API URL: $API_URL"
echo "================================"
echo ""

# Test basic health
echo -n "Testing /health ... "
RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/health")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASSED${NC} (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
else
    echo -e "${RED}✗ FAILED${NC} (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
fi
echo ""

# Test liveness probe
echo -n "Testing /health/live (K8s liveness) ... "
RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/health/live")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASSED${NC} (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
else
    echo -e "${RED}✗ FAILED${NC} (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
fi
echo ""

# Test readiness probe
echo -n "Testing /health/ready (K8s readiness) ... "
RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/health/ready")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASSED${NC} (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
    echo "   ${GREEN}Pod is READY to receive traffic${NC}"
elif [ "$HTTP_CODE" = "503" ]; then
    echo -e "${YELLOW}⚠ DEGRADED${NC} (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
    echo "   ${YELLOW}Pod is NOT READY (will be removed from load balancer)${NC}"
else
    echo -e "${RED}✗ FAILED${NC} (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
fi
echo ""

# Test detailed health
echo "Testing /health/detailed (monitoring) ... "
RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/health/detailed")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASSED${NC} (HTTP $HTTP_CODE)"
    echo "   Response:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo -e "${RED}✗ FAILED${NC} (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
fi
echo ""

echo "================================"
echo "✅ Health endpoint tests complete"
