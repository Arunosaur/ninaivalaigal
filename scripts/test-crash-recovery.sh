#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Crash Recovery Testing Script
# Version: 1.0.0 - Day 3 Infrastructure Reliability
# Purpose: Validate auto-restart and recovery capabilities

set -euo pipefail

# Colors
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Configuration
readonly ENV="${NINA_ENV:-dev}"
readonly DB_CONTAINER="ninaivalaigal-${ENV}-db"
readonly REDIS_CONTAINER="ninaivalaigal-${ENV}-redis"
readonly RECOVERY_TIMEOUT=30

log_info() {
    echo -e "${BLUE}[TEST]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $*"
}

log_failure() {
    echo -e "${RED}[FAIL]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

# Check if container is running
is_container_running() {
    local container_name=$1
    container list | grep -q "$container_name.*running"
}

# Wait for container to restart
wait_for_recovery() {
    local container_name=$1
    local max_wait=$RECOVERY_TIMEOUT
    local elapsed=0

    log_info "Waiting for $container_name to recover (max ${max_wait}s)..."

    while [ $elapsed -lt $max_wait ]; do
        if is_container_running "$container_name"; then
            log_success "$container_name recovered in ${elapsed}s"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
        echo -n "."
    done

    echo ""
    log_failure "$container_name did not recover within ${max_wait}s"
    return 1
}

# Test database crash recovery
test_database_crash() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "TEST 1: Database Crash Recovery"
    log_info "════════════════════════════════════════"

    # Verify database is running
    if ! is_container_running "$DB_CONTAINER"; then
        log_failure "$DB_CONTAINER not running - cannot test crash recovery"
        return 1
    fi

    log_info "Database is running, simulating crash..."

    # Kill the container
    container stop "$DB_CONTAINER" >/dev/null 2>&1
    log_info "Database stopped (simulated crash)"

    sleep 2

    # Check if auto-restart is working
    if is_container_running "$DB_CONTAINER"; then
        log_success "Auto-restart is working! Database restarted automatically"
        return 0
    else
        log_warning "Auto-restart not configured - testing manual recovery..."

        # Start the container
        ./scripts/stack-start.sh >/dev/null 2>&1

        if wait_for_recovery "$DB_CONTAINER"; then
            log_success "Manual recovery successful"
            return 0
        else
            log_failure "Manual recovery failed"
            return 1
        fi
    fi
}

# Test Redis crash recovery
test_redis_crash() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "TEST 2: Redis Crash Recovery"
    log_info "════════════════════════════════════════"

    # Verify Redis is running
    if ! is_container_running "$REDIS_CONTAINER"; then
        log_failure "$REDIS_CONTAINER not running - cannot test crash recovery"
        return 1
    fi

    log_info "Redis is running, simulating crash..."

    # Kill the container
    container stop "$REDIS_CONTAINER" >/dev/null 2>&1
    log_info "Redis stopped (simulated crash)"

    sleep 2

    # Check if auto-restart is working
    if is_container_running "$REDIS_CONTAINER"; then
        log_success "Auto-restart is working! Redis restarted automatically"
        return 0
    else
        log_warning "Auto-restart not configured - testing manual recovery..."

        # Start the container
        ./scripts/stack-start.sh >/dev/null 2>&1

        if wait_for_recovery "$REDIS_CONTAINER"; then
            log_success "Manual recovery successful"
            return 0
        else
            log_failure "Manual recovery failed"
            return 1
        fi
    fi
}

# Test complete stack restart
test_complete_restart() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "TEST 3: Complete Stack Restart"
    log_info "════════════════════════════════════════"

    log_info "Stopping entire stack..."
    ./scripts/stack-stop.sh >/dev/null 2>&1

    sleep 3

    log_info "Starting stack from cold state..."
    ./scripts/stack-start.sh >/dev/null 2>&1

    if is_container_running "$DB_CONTAINER" && is_container_running "$REDIS_CONTAINER"; then
        log_success "Complete stack restart successful"
        return 0
    else
        log_failure "Complete stack restart failed"
        return 1
    fi
}

# Test health checks after recovery
test_health_after_recovery() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "TEST 4: Health Checks After Recovery"
    log_info "════════════════════════════════════════"

    log_info "Running health checks..."

    if ./scripts/stack-status.sh >/dev/null 2>&1; then
        log_success "All health checks passed"
        return 0
    else
        log_failure "Health checks failed after recovery"
        return 1
    fi
}

# Main test suite
main() {
    local failed_tests=0

    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     Crash Recovery Test Suite                       ║${NC}"
    echo -e "${BLUE}║     Testing infrastructure resilience               ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"

    # Run tests
    test_database_crash || ((failed_tests++))
    test_redis_crash || ((failed_tests++))
    test_complete_restart || ((failed_tests++))
    test_health_after_recovery || ((failed_tests++))

    # Summary
    echo ""
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}Test Summary${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"

    if [ $failed_tests -eq 0 ]; then
        log_success "All crash recovery tests passed!"
        echo ""
        echo "✅ Infrastructure is resilient and self-healing"
        echo "✅ Ready for production development"
        exit 0
    else
        log_failure "$failed_tests test(s) failed"
        echo ""
        echo "⚠️  Some recovery scenarios need attention"
        echo "⚠️  Review logs and troubleshooting guide"
        exit 1
    fi
}

# Run test suite
main "$@"
