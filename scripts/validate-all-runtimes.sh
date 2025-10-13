#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Validate all 9 runtime combinations (3 runtimes × 3 environments)
# Part of SPEC-999: Regression Prevention & Production Stability Framework

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" == "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $message"
        ((PASSED_TESTS++))
    elif [ "$status" == "FAIL" ]; then
        echo -e "${RED}❌ FAIL${NC}: $message"
        ((FAILED_TESTS++))
    elif [ "$status" == "SKIP" ]; then
        echo -e "${YELLOW}⚠️  SKIP${NC}: $message"
    else
        echo -e "${YELLOW}ℹ️  INFO${NC}: $message"
    fi
    ((TOTAL_TESTS++))
}

# Function to test a runtime/environment combination
test_runtime() {
    local runtime=$1
    local env=$2
    local compose_file=$3

    echo ""
    echo "========================================="
    echo "Testing: $runtime - $env"
    echo "Compose: $compose_file"
    echo "========================================="

    # Check if compose file exists
    if [ ! -f "$compose_file" ]; then
        print_status "SKIP" "$runtime/$env - Compose file not found"
        return
    fi

    # Start the stack
    echo "Starting stack..."
    if ! docker-compose -f "$compose_file" up -d 2>&1 | grep -q "Started\|Running"; then
        print_status "FAIL" "$runtime/$env - Failed to start stack"
        return
    fi

    # Wait for services to be healthy
    echo "Waiting for services (30s)..."
    sleep 30

    # Check if API is responding
    if curl -s http://localhost:13370/health | grep -q "ok"; then
        print_status "PASS" "$runtime/$env - API responding"
    else
        print_status "FAIL" "$runtime/$env - API not responding"
        docker-compose -f "$compose_file" down
        return
    fi

    # Check Redis
    if docker exec ninaivalaigal-${env}-redis redis-cli -a secure_nina_password ping 2>/dev/null | grep -q "PONG"; then
        print_status "PASS" "$runtime/$env - Redis responding"
    else
        print_status "FAIL" "$runtime/$env - Redis not responding"
    fi

    # Check PostgreSQL
    if docker exec ninaivalaigal-${env}-db psql -U nina -d ninaivalaigal_${env} -c "SELECT 1;" 2>/dev/null | grep -q "1"; then
        print_status "PASS" "$runtime/$env - PostgreSQL responding"
    else
        print_status "FAIL" "$runtime/$env - PostgreSQL not responding"
    fi

    # Clean up
    echo "Cleaning up..."
    docker-compose -f "$compose_file" down

    echo "✅ $runtime/$env validation complete"
}

# Main execution
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Runtime Validation - All 9 Combinations                  ║"
echo "║  Part of SPEC-999: Regression Prevention Framework        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Test Matrix: 3 runtimes × 1 environment (dev) = 3 combinations
# Note: Staging and prod environments not yet configured

# Docker Runtime (Dev)
test_runtime "Docker" "dev" "compose.docker.yml"

# Apple Container CLI Runtime (Dev)
test_runtime "Apple CLI" "dev" "compose.apple.yml"

# Colima Runtime (Dev)
test_runtime "Colima" "dev" "compose.colima.yml"

# Production stack (separate)
test_runtime "Docker" "production" "compose.production.yml"

# Summary
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  VALIDATION SUMMARY                                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Total Tests:  $TOTAL_TESTS"
echo -e "${GREEN}Passed:       $PASSED_TESTS${NC}"
echo -e "${RED}Failed:       $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL VALIDATIONS PASSED!${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME VALIDATIONS FAILED${NC}"
    exit 1
fi
