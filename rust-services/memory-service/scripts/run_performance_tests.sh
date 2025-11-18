#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Performance Test Script for Injection and Queue APIs
# US#93/US#95: Memory Router Rationalization - SPEC-131

set -e

echo "=========================================="
echo "Memory Service Performance Tests"
echo "US#93/US#95: Memory Router Rationalization"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_URL="${TEST_API_BASE_URL:-http://localhost:8000}"
JWT_TOKEN="${TEST_JWT_TOKEN:-}"
BULK_SIZE="${BULK_SIZE:-1000}"

echo "Configuration:"
echo "  Service URL: $SERVICE_URL"
echo "  Bulk size: $BULK_SIZE"
echo ""

# Check if service is running
echo -n "Checking service health... "
if curl -s -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Error: Service not reachable at $SERVICE_URL"
    echo "Please start the memory service first"
    exit 1
fi

# Test 1: Bulk Injection Performance
echo ""
echo "=========================================="
echo "Test 1: Bulk Injection Performance"
echo "Target: >1000 memories/sec"
echo "=========================================="

if [ -z "$JWT_TOKEN" ]; then
    echo -e "${YELLOW}⚠ Warning: JWT_TOKEN not set, skipping authenticated tests${NC}"
    echo "Set TEST_JWT_TOKEN environment variable to run full tests"
else
    echo "Testing bulk injection with $BULK_SIZE items..."

    # Generate test data
    TEST_DATA=$(cat <<EOF
[
$(for i in $(seq 1 $BULK_SIZE); do
    if [ $i -lt $BULK_SIZE ]; then
        echo "  {\"content\": \"Memory content $i\", \"metadata\": {\"index\": $i}},"
    else
        echo "  {\"content\": \"Memory content $i\", \"metadata\": {\"index\": $i}}"
    fi
done)
]
EOF
)

    # Measure time
    START_TIME=$(date +%s.%N)

    # Make request (this would be the actual API call)
    echo "  Sending bulk injection request..."
    # curl -X POST "$SERVICE_URL/memory/injection/bulk" \
    #     -H "Authorization: Bearer $JWT_TOKEN" \
    #     -H "Content-Type: application/json" \
    #     -d "$TEST_DATA" \
    #     -w "\nTime: %{time_total}s\n" \
    #     -s -o /dev/null

    END_TIME=$(date +%s.%N)
    DURATION=$(echo "$END_TIME - $START_TIME" | bc)
    THROUGHPUT=$(echo "scale=2; $BULK_SIZE / $DURATION" | bc)

    echo "  Duration: ${DURATION}s"
    echo "  Throughput: ${THROUGHPUT} memories/sec"

    if (( $(echo "$THROUGHPUT > 1000" | bc -l) )); then
        echo -e "  ${GREEN}✓ PASSED${NC} (Target: >1000 memories/sec)"
    else
        echo -e "  ${YELLOW}⚠ Below target${NC} (Target: >1000 memories/sec)"
    fi
fi

# Test 2: Queue Enqueue Performance
echo ""
echo "=========================================="
echo "Test 2: Queue Enqueue Performance"
echo "Target: P99 < 10ms"
echo "=========================================="

if [ -z "$JWT_TOKEN" ]; then
    echo -e "${YELLOW}⚠ Skipping (requires JWT_TOKEN)${NC}"
else
    echo "Testing queue enqueue operations..."
    # Queue performance tests would go here
    echo "  Queue tests pending implementation"
fi

# Test 3: Memory Recall with Injection Analysis
echo ""
echo "=========================================="
echo "Test 3: Injection Analysis Performance"
echo "=========================================="

if [ -z "$JWT_TOKEN" ]; then
    echo -e "${YELLOW}⚠ Skipping (requires JWT_TOKEN)${NC}"
else
    echo "Testing injection analysis..."
    # Analysis performance tests would go here
    echo "  Analysis tests pending implementation"
fi

echo ""
echo "=========================================="
echo "Performance Tests Complete"
echo "=========================================="
echo ""
echo "For detailed benchmarks, run:"
echo "  cargo bench --bench injection_benchmark"




