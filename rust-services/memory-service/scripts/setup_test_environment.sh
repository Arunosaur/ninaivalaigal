#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Setup test environment for Memory Service integration tests
# US#93/US#95: Memory Router Rationalization - SPEC-131

set -e

echo "=========================================="
echo "Memory Service Test Environment Setup"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Check if service is running
echo "Checking service status..."
SERVICE_URL="${TEST_API_BASE_URL:-http://localhost:13393}"

if curl -s -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo "✅ Service is running at $SERVICE_URL"
else
    echo "⚠️  Service not running at $SERVICE_URL"
    echo ""
    echo "To start the service:"
    echo "  cd $PROJECT_ROOT/rust-services/memory-service"
    echo "  make deploy"
    echo "  cd $PROJECT_ROOT/scripts"
    echo "  ./nv-memory-service-start.sh"
    echo ""
    read -p "Would you like to start the service now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PROJECT_ROOT/rust-services/memory-service"
        make deploy
        cd "$PROJECT_ROOT/scripts"
        ./nv-memory-service-start.sh
    else
        echo "Please start the service manually and run this script again"
        exit 1
    fi
fi

echo ""

# Check for JWT token
if [ -z "${TEST_JWT_TOKEN:-}" ]; then
    echo "⚠️  TEST_JWT_TOKEN not set"
    echo ""
    echo "To get a JWT token, you can:"
    echo "  1. Login via Core API and extract token"
    echo "  2. Use a test token from your auth system"
    echo "  3. Set TEST_JWT_TOKEN environment variable"
    echo ""
    echo "Example:"
    echo "  export TEST_JWT_TOKEN='your-jwt-token-here'"
    echo ""
else
    echo "✅ TEST_JWT_TOKEN is set"
fi

echo ""

# Check database connection (via service health)
echo "Checking database connection..."
HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health" || echo "{}")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Database connection OK"
else
    echo "⚠️  Database connection may have issues"
fi

echo ""

# Check Redis connection (via queue health)
echo "Checking Redis connection..."
QUEUE_HEALTH=$(curl -s "$SERVICE_URL/queue/health" 2>/dev/null || echo "{}")
if echo "$QUEUE_HEALTH" | grep -q "connected"; then
    echo "✅ Redis connection OK"
else
    echo "⚠️  Redis connection may have issues"
fi

echo ""
echo "=========================================="
echo "Test Environment Ready"
echo "=========================================="
echo ""
echo "Environment Variables:"
echo "  TEST_API_BASE_URL=${TEST_API_BASE_URL:-http://localhost:13393}"
echo "  TEST_JWT_TOKEN=${TEST_JWT_TOKEN:+SET}"
echo ""
echo "To run integration tests:"
echo "  cargo test --test injection_api_tests -- --nocapture"
echo "  cargo test --test queue_api_tests -- --nocapture"
echo ""




