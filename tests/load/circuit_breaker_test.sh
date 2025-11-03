#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#

##############################################################################
# Circuit Breaker Load Test Script
#
# This script validates circuit breaker behavior by simulating service
# failures and monitoring state transitions.
#
# Usage:
#   ./tests/load/circuit_breaker_test.sh [service_name]
#
# Example:
#   ./tests/load/circuit_breaker_test.sh redis
#
# Author: Developer C
# Date: November 1, 2025
# Related: US#407 - Platform Stability Monitoring
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
SERVICE_NAME="${1:-redis}"
FAILURE_THRESHOLD=5
SUCCESS_THRESHOLD=2
RECOVERY_TIMEOUT=60

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to get circuit breaker state
get_circuit_state() {
    local service=$1
    curl -s "${API_URL}/platform/health/containers/${service}" | \
        jq -r '.circuit_breaker_state // "unknown"'
}

# Function to get failure count
get_failure_count() {
    local service=$1
    curl -s "${API_URL}/platform/health/containers/${service}" | \
        jq -r '.failure_count // 0'
}

# Function to simulate service failure
simulate_failure() {
    local service=$1
    log_info "Simulating failure for ${service}..."

    # This would typically involve:
    # - Stopping the service container
    # - Blocking network access
    # - Injecting errors

    # For testing, we'll just make a request that should fail
    curl -s -X POST "${API_URL}/platform/health/check" > /dev/null
}

# Function to wait for state change
wait_for_state() {
    local service=$1
    local expected_state=$2
    local timeout=$3
    local elapsed=0

    log_info "Waiting for circuit breaker to reach state: ${expected_state}"

    while [ $elapsed -lt $timeout ]; do
        current_state=$(get_circuit_state "$service")

        if [ "$current_state" == "$expected_state" ]; then
            log_success "Circuit breaker reached ${expected_state} state after ${elapsed}s"
            return 0
        fi

        echo -n "."
        sleep 1
        elapsed=$((elapsed + 1))
    done

    echo ""
    log_error "Timeout waiting for ${expected_state} state"
    return 1
}

# Function to display circuit breaker status
display_status() {
    local service=$1

    echo ""
    echo "=========================================="
    echo "Circuit Breaker Status: ${service}"
    echo "=========================================="

    response=$(curl -s "${API_URL}/platform/health/containers/${service}")

    echo "$response" | jq '{
        service: .service,
        status: .status,
        circuit_breaker_state: .circuit_breaker_state,
        failure_count: .failure_count,
        success_count: .success_count,
        last_failure_time: .last_failure_time,
        response_time_ms: .response_time_ms
    }'

    echo "=========================================="
    echo ""
}

##############################################################################
# Test 1: Circuit Opens After Failures
##############################################################################
test_circuit_opens() {
    log_info "TEST 1: Verifying circuit opens after ${FAILURE_THRESHOLD} failures"

    # Get initial state
    initial_state=$(get_circuit_state "$SERVICE_NAME")
    log_info "Initial circuit state: ${initial_state}"

    # Simulate failures
    log_info "Simulating ${FAILURE_THRESHOLD} consecutive failures..."
    for i in $(seq 1 $FAILURE_THRESHOLD); do
        log_info "Failure ${i}/${FAILURE_THRESHOLD}"
        simulate_failure "$SERVICE_NAME"
        sleep 1

        failure_count=$(get_failure_count "$SERVICE_NAME")
        log_info "Current failure count: ${failure_count}"
    done

    # Check if circuit opened
    sleep 2
    current_state=$(get_circuit_state "$SERVICE_NAME")

    if [ "$current_state" == "open" ]; then
        log_success "✓ Circuit breaker opened after ${FAILURE_THRESHOLD} failures"
        display_status "$SERVICE_NAME"
        return 0
    else
        log_error "✗ Circuit breaker did not open (current state: ${current_state})"
        display_status "$SERVICE_NAME"
        return 1
    fi
}

##############################################################################
# Test 2: Circuit Enters Half-Open After Timeout
##############################################################################
test_circuit_half_open() {
    log_info "TEST 2: Verifying circuit enters half-open after ${RECOVERY_TIMEOUT}s"

    # Ensure circuit is open
    current_state=$(get_circuit_state "$SERVICE_NAME")
    if [ "$current_state" != "open" ]; then
        log_warning "Circuit not in open state, skipping test"
        return 1
    fi

    # Wait for recovery timeout
    log_info "Waiting ${RECOVERY_TIMEOUT}s for recovery timeout..."
    if wait_for_state "$SERVICE_NAME" "half_open" $((RECOVERY_TIMEOUT + 10)); then
        log_success "✓ Circuit breaker entered half-open state"
        display_status "$SERVICE_NAME"
        return 0
    else
        log_error "✗ Circuit breaker did not enter half-open state"
        display_status "$SERVICE_NAME"
        return 1
    fi
}

##############################################################################
# Test 3: Circuit Closes After Successes
##############################################################################
test_circuit_closes() {
    log_info "TEST 3: Verifying circuit closes after ${SUCCESS_THRESHOLD} successes"

    # Ensure circuit is half-open
    current_state=$(get_circuit_state "$SERVICE_NAME")
    if [ "$current_state" != "half_open" ]; then
        log_warning "Circuit not in half-open state, skipping test"
        return 1
    fi

    # Simulate successful requests
    log_info "Simulating ${SUCCESS_THRESHOLD} successful requests..."
    for i in $(seq 1 $SUCCESS_THRESHOLD); do
        log_info "Success ${i}/${SUCCESS_THRESHOLD}"
        curl -s "${API_URL}/platform/health/summary" > /dev/null
        sleep 1
    done

    # Check if circuit closed
    sleep 2
    current_state=$(get_circuit_state "$SERVICE_NAME")

    if [ "$current_state" == "closed" ]; then
        log_success "✓ Circuit breaker closed after ${SUCCESS_THRESHOLD} successes"
        display_status "$SERVICE_NAME"
        return 0
    else
        log_error "✗ Circuit breaker did not close (current state: ${current_state})"
        display_status "$SERVICE_NAME"
        return 1
    fi
}

##############################################################################
# Test 4: Circuit Blocks Requests When Open
##############################################################################
test_circuit_blocks_requests() {
    log_info "TEST 4: Verifying circuit blocks requests when open"

    # Force circuit to open
    test_circuit_opens

    # Try to make request
    log_info "Attempting request with open circuit..."
    response=$(curl -s -w "\n%{http_code}" "${API_URL}/platform/health/containers/${SERVICE_NAME}")
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)

    # Circuit should block or return error
    if [ "$http_code" == "503" ] || echo "$body" | grep -q "circuit.*open"; then
        log_success "✓ Circuit breaker blocked request when open"
        return 0
    else
        log_warning "Circuit may not be blocking requests (HTTP ${http_code})"
        echo "$body" | jq '.'
        return 1
    fi
}

##############################################################################
# Test 5: Monitor State Transitions
##############################################################################
test_monitor_transitions() {
    log_info "TEST 5: Monitoring complete state transition cycle"

    log_info "Starting state transition monitoring..."
    echo ""
    echo "State Transition Timeline:"
    echo "=========================="

    # Monitor for 3 minutes
    end_time=$(($(date +%s) + 180))
    prev_state=""

    while [ $(date +%s) -lt $end_time ]; do
        current_state=$(get_circuit_state "$SERVICE_NAME")

        if [ "$current_state" != "$prev_state" ]; then
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            echo "${timestamp} - State changed: ${prev_state} → ${current_state}"
            prev_state=$current_state
        fi

        sleep 5
    done

    log_success "✓ State transition monitoring complete"
}

##############################################################################
# Main Test Execution
##############################################################################
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║         Circuit Breaker Load Test - US#407                     ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    log_info "Testing service: ${SERVICE_NAME}"
    log_info "API URL: ${API_URL}"
    log_info "Failure threshold: ${FAILURE_THRESHOLD}"
    log_info "Success threshold: ${SUCCESS_THRESHOLD}"
    log_info "Recovery timeout: ${RECOVERY_TIMEOUT}s"
    echo ""

    # Check if API is accessible
    if ! curl -s "${API_URL}/platform/health/summary" > /dev/null; then
        log_error "Cannot reach API at ${API_URL}"
        log_error "Please ensure Core API is running"
        exit 1
    fi

    log_success "API is accessible"
    echo ""

    # Display initial status
    display_status "$SERVICE_NAME"

    # Run tests
    test_results=()

    echo "Running Circuit Breaker Tests..."
    echo "================================"
    echo ""

    # Test 1: Circuit Opens
    if test_circuit_opens; then
        test_results+=("PASS")
    else
        test_results+=("FAIL")
    fi
    echo ""

    # Test 2: Circuit Half-Open
    if test_circuit_half_open; then
        test_results+=("PASS")
    else
        test_results+=("FAIL")
    fi
    echo ""

    # Test 3: Circuit Closes
    if test_circuit_closes; then
        test_results+=("PASS")
    else
        test_results+=("FAIL")
    fi
    echo ""

    # Test 4: Blocks Requests
    if test_circuit_blocks_requests; then
        test_results+=("PASS")
    else
        test_results+=("FAIL")
    fi
    echo ""

    # Display final status
    display_status "$SERVICE_NAME"

    # Summary
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                      Test Summary                              ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    passed=0
    failed=0

    for i in "${!test_results[@]}"; do
        test_num=$((i + 1))
        result="${test_results[$i]}"

        if [ "$result" == "PASS" ]; then
            echo -e "Test ${test_num}: ${GREEN}✓ PASSED${NC}"
            passed=$((passed + 1))
        else
            echo -e "Test ${test_num}: ${RED}✗ FAILED${NC}"
            failed=$((failed + 1))
        fi
    done

    echo ""
    echo "Total: ${passed} passed, ${failed} failed"
    echo ""

    if [ $failed -eq 0 ]; then
        log_success "All circuit breaker tests passed! ✓"
        exit 0
    else
        log_error "Some circuit breaker tests failed"
        exit 1
    fi
}

# Run main function
main "$@"
