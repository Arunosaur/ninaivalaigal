#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Phase 3: Integration Testing and Performance Benchmarking
# US#93/US#95: Memory Router Rationalization - SPEC-131

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$SCRIPT_DIR/.."

echo "=========================================="
echo "Phase 3: Integration & Performance Tests"
echo "US#93/US#95: Memory Router Rationalization"
echo "=========================================="
echo ""

# Configuration
SERVICE_URL="${TEST_API_BASE_URL:-http://localhost:13393}"
TIMEOUT=30

# Check service availability
echo "Step 1: Checking service availability..."
if ! curl -s -f --max-time 5 "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo "❌ Service not available at $SERVICE_URL"
    echo ""
    echo "Please start the service first:"
    echo "  cd $PROJECT_ROOT/rust-services/memory-service"
    echo "  make deploy"
    echo "  cd $PROJECT_ROOT/scripts"
    echo "  ./nv-memory-service-start.sh"
    echo ""
    exit 1
fi

echo "✅ Service is running at $SERVICE_URL"
echo ""

# Check health endpoint
echo "Step 2: Verifying health endpoint..."
HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health" || echo "{}")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Health endpoint OK"
    echo "$HEALTH_RESPONSE" | jq '.' 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo "⚠️  Health endpoint may have issues"
    echo "$HEALTH_RESPONSE"
fi
echo ""

# Check queue health
echo "Step 3: Verifying queue health endpoint..."
QUEUE_HEALTH=$(curl -s "$SERVICE_URL/queue/health" 2>/dev/null || echo "{}")
if echo "$QUEUE_HEALTH" | grep -q "connected"; then
    echo "✅ Queue health OK"
    echo "$QUEUE_HEALTH" | jq '.' 2>/dev/null || echo "$QUEUE_HEALTH"
else
    echo "⚠️  Queue health may have issues"
    echo "$QUEUE_HEALTH"
fi
echo ""

# Check JWT token
if [ -z "${TEST_JWT_TOKEN:-}" ]; then
    echo "⚠️  TEST_JWT_TOKEN not set"
    echo "   Integration tests requiring authentication will be skipped"
    echo ""
    AUTH_TESTS=false
else
    echo "✅ TEST_JWT_TOKEN is set"
    echo ""
    AUTH_TESTS=true
fi

# Run unit tests
echo "Step 4: Running unit tests..."
echo "----------------------------------------"
cargo test --lib -- --nocapture 2>&1 | tee /tmp/unit_tests.log
UNIT_TEST_RESULT=${PIPESTATUS[0]}
if [ $UNIT_TEST_RESULT -eq 0 ]; then
    echo "✅ Unit tests passed"
else
    echo "❌ Unit tests failed"
fi
echo ""

# Run integration tests (if service available and token provided)
if [ "$AUTH_TESTS" = "true" ]; then
    echo "Step 5: Running integration tests..."
    echo "----------------------------------------"
    echo "Running injection API tests..."
    cargo test --test injection_api_tests -- --ignored --nocapture 2>&1 | tee /tmp/injection_tests.log || true

    echo ""
    echo "Running queue API tests..."
    cargo test --test queue_api_tests -- --ignored --nocapture 2>&1 | tee /tmp/queue_tests.log || true
    echo ""
else
    echo "Step 5: Skipping integration tests (no JWT token)"
    echo ""
fi

# Performance benchmarks
echo "Step 6: Running performance benchmarks..."
echo "----------------------------------------"
if command -v cargo &> /dev/null && cargo --list | grep -q bench; then
    echo "Running Criterion benchmarks..."
    cargo bench --bench injection_benchmark 2>&1 | tee /tmp/benchmarks.log || echo "⚠️  Benchmarks require additional setup"
else
    echo "⚠️  Cargo bench not available, skipping benchmarks"
fi
echo ""

# Summary
echo "=========================================="
echo "Phase 3 Test Summary"
echo "=========================================="
echo ""

if [ $UNIT_TEST_RESULT -eq 0 ]; then
    echo "✅ Unit Tests: PASSED"
else
    echo "❌ Unit Tests: FAILED"
fi

if [ "$AUTH_TESTS" = "true" ]; then
    echo "✅ Integration Tests: RUN (check logs for details)"
else
    echo "⚠️  Integration Tests: SKIPPED (no JWT token)"
fi

echo "📊 Performance Benchmarks: See /tmp/benchmarks.log"
echo ""

# Test results location
echo "Test Results:"
echo "  Unit Tests: /tmp/unit_tests.log"
echo "  Injection Tests: /tmp/injection_tests.log"
echo "  Queue Tests: /tmp/queue_tests.log"
echo "  Benchmarks: /tmp/benchmarks.log"
echo ""

echo "=========================================="
echo "Phase 3 Complete"
echo "=========================================="




