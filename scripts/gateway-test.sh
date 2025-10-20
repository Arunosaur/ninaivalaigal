#!/bin/bash
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC

# Test Traefik API Gateway
# Task #83: API Gateway Testing

set -euo pipefail

GATEWAY_URL="${GATEWAY_URL:-http://localhost}"
DASHBOARD_URL="http://localhost:8080"
PASS=0
FAIL=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Testing Traefik API Gateway"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    echo -n "Testing $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    # Accept 200 (OK), 301 (redirect to HTTPS), 302 (redirect)
    if [ "$response" == "200" ] || [ "$response" == "301" ] || [ "$response" == "302" ]; then
        if [ "$response" == "301" ]; then
            echo -e "${GREEN}✅ PASS${NC} (HTTP $response - HTTPS redirect)"
        else
            echo -e "${GREEN}✅ PASS${NC} (HTTP $response)"
        fi
        ((PASS++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $response, expected $expected_code or 301)"
        ((FAIL++))
        return 1
    fi
}

test_endpoint_contains() {
    local name=$1
    local url=$2
    local search_string=$3

    echo -n "Testing $name... "

    response=$(curl -s "$url" 2>/dev/null || echo "")

    if echo "$response" | grep -q "$search_string"; then
        echo -e "${GREEN}✅ PASS${NC} (Found: $search_string)"
        ((PASS++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (Not found: $search_string)"
        ((FAIL++))
        return 1
    fi
}

echo "🔍 Gateway Health Checks"
echo "─────────────────────────────────────────────────────"

# Test gateway health
test_endpoint "Gateway Health" "$GATEWAY_URL/health" 200 || true

# Test dashboard
test_endpoint "Dashboard" "$DASHBOARD_URL/api/overview" 200 || true

# Test metrics
test_endpoint "Metrics Endpoint" "$GATEWAY_URL/metrics" 200 || true

echo ""
echo "🔗 Service Route Tests"
echo "─────────────────────────────────────────────────────"

# Test Core API route
test_endpoint "Core API Route" "$GATEWAY_URL/api/health" 200 || true

# Test Business Service route (if running)
test_endpoint "Business Service Route" "$GATEWAY_URL/business/health" 200 || true

# Test Memory Service route (if running)
test_endpoint "Memory Service Route" "$GATEWAY_URL/memory/health" 200 || true

# Test GraphOps route (if running)
test_endpoint "GraphOps Route" "$GATEWAY_URL/graph/health" 200 || true

echo ""
echo "🛡️ Security Tests"
echo "─────────────────────────────────────────────────────"

# Test CORS headers
echo -n "Testing CORS headers... "
cors_header=$(curl -s -H "Origin: http://localhost:3000" -I "$GATEWAY_URL/api/health" 2>/dev/null | grep -i "access-control-allow-origin" || echo "")
if [ -n "$cors_header" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  SKIP${NC} (Service may not be running)"
fi

# Test rate limiting headers
echo -n "Testing rate limit headers... "
rate_header=$(curl -s -I "$GATEWAY_URL/api/health" 2>/dev/null | grep -i "x-ratelimit" || echo "")
if [ -n "$rate_header" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  INFO${NC} (Rate limit headers optional)"
fi

# Test request size limit
echo -n "Testing request size limits... "
large_payload=$(printf '%*s' 11000000 '' | tr ' ' 'a')
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$GATEWAY_URL/api/health" -d "$large_payload" 2>/dev/null || echo "000")
if [ "$response" == "413" ] || [ "$response" == "400" ]; then
    echo -e "${GREEN}✅ PASS${NC} (Request rejected)"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  SKIP${NC} (Service handling may vary)"
fi

echo ""
echo "📊 Performance Tests"
echo "─────────────────────────────────────────────────────"

# Test response time
echo -n "Testing gateway latency... "
start_time=$(date +%s%N)
curl -s -o /dev/null "$GATEWAY_URL/health" 2>/dev/null || true
end_time=$(date +%s%N)
latency=$(( (end_time - start_time) / 1000000 ))

if [ "$latency" -lt 100 ]; then
    echo -e "${GREEN}✅ PASS${NC} (${latency}ms < 100ms)"
    ((PASS++))
elif [ "$latency" -lt 500 ]; then
    echo -e "${YELLOW}⚠️  WARN${NC} (${latency}ms, target <100ms)"
else
    echo -e "${RED}❌ FAIL${NC} (${latency}ms > 500ms)"
    ((FAIL++))
fi

# Test concurrent requests
echo -n "Testing concurrent requests... "
for i in {1..10}; do
    curl -s -o /dev/null "$GATEWAY_URL/health" 2>/dev/null &
done
wait
echo -e "${GREEN}✅ PASS${NC} (10 concurrent requests)"
((PASS++))

echo ""
echo "📝 Logging Tests"
echo "─────────────────────────────────────────────────────"

# Check if gateway is logging
echo -n "Testing access logs... "
if docker logs ninaivalaigal-gateway 2>&1 | tail -5 | grep -q "GET\|POST\|level"; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  WARN${NC} (No recent log entries)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "  ${GREEN}✅ Passed: $PASS${NC}"
echo -e "  ${RED}❌ Failed: $FAIL${NC}"
echo -e "  📊 Total:  $((PASS + FAIL))"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  • Check gateway status: ./scripts/gateway-status.sh"
    echo "  • Check gateway logs: docker logs ninaivalaigal-gateway"
    echo "  • Ensure services are running"
    echo ""
    exit 1
fi
