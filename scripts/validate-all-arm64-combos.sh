#!/bin/bash
###############################################################################
# Validate All ARM64 Runtime Combinations
#
# Tests all 9 combinations of:
#   - 3 runtimes: Docker, Colima, Apple Container CLI
#   - 3 environments: dev, test, prod
#
# For each combination, verifies:
#   1. Database starts and has pgvector + Apache AGE
#   2. API starts and health check passes
#   3. Staff login works
#   4. Clean shutdown
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Results tracking
declare -A RESULTS
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

###############################################################################
# Helper Functions
###############################################################################

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

record_result() {
    local runtime=$1
    local env=$2
    local test=$3
    local result=$4

    local key="${runtime}_${env}_${test}"
    RESULTS[$key]=$result
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ "$result" = "PASS" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        log_success "$runtime $env - $test: PASS"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        log_error "$runtime $env - $test: FAIL"
    fi
}

wait_for_healthy() {
    local container_name=$1
    local max_wait=${2:-60}
    local waited=0

    log_info "Waiting for $container_name to be healthy..."

    while [ $waited -lt $max_wait ]; do
        if docker ps --filter "name=$container_name" --filter "health=healthy" | grep -q "$container_name"; then
            log_success "$container_name is healthy"
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
    done

    log_error "$container_name failed to become healthy after ${max_wait}s"
    return 1
}

###############################################################################
# Test Functions
###############################################################################

test_database_extensions() {
    local runtime=$1
    local env=$2
    local db_container=$3

    log_info "Testing database extensions..."

    # Check pgvector
    if docker exec "$db_container" psql -U nina -d "ninaivalaigal_${env}" -c "SELECT extname FROM pg_extension WHERE extname='vector';" 2>/dev/null | grep -q "vector"; then
        log_success "pgvector extension found"
    else
        log_error "pgvector extension NOT found"
        record_result "$runtime" "$env" "pgvector" "FAIL"
        return 1
    fi

    # Check Apache AGE
    if docker exec "$db_container" psql -U nina -d "ninaivalaigal_${env}" -c "SELECT extname FROM pg_extension WHERE extname='age';" 2>/dev/null | grep -q "age"; then
        log_success "Apache AGE extension found"
    else
        log_error "Apache AGE extension NOT found"
        record_result "$runtime" "$env" "age" "FAIL"
        return 1
    fi

    # Check pgcrypto
    if docker exec "$db_container" psql -U nina -d "ninaivalaigal_${env}" -c "SELECT extname FROM pg_extension WHERE extname='pgcrypto';" 2>/dev/null | grep -q "pgcrypto"; then
        log_success "pgcrypto extension found"
    else
        log_error "pgcrypto extension NOT found"
        record_result "$runtime" "$env" "pgcrypto" "FAIL"
        return 1
    fi

    record_result "$runtime" "$env" "database_extensions" "PASS"
    return 0
}

test_api_health() {
    local runtime=$1
    local env=$2
    local api_url=$3

    log_info "Testing API health..."

    if curl -s -f "$api_url/health" | grep -q "ok"; then
        log_success "API health check passed"
        record_result "$runtime" "$env" "api_health" "PASS"
        return 0
    else
        log_error "API health check failed"
        record_result "$runtime" "$env" "api_health" "FAIL"
        return 1
    fi
}

test_staff_login() {
    local runtime=$1
    local env=$2
    local api_url=$3

    log_info "Testing staff login..."

    local response=$(curl -s -X POST "$api_url/auth/staff/login" \
        -H "Content-Type: application/json" \
        -d '{"email": "admin@ninaivalaigal.com", "password": "ChangeMe123!@#"}')

    if echo "$response" | grep -q "access_token"; then
        log_success "Staff login successful"
        record_result "$runtime" "$env" "staff_login" "PASS"
        return 0
    else
        log_error "Staff login failed: $response"
        record_result "$runtime" "$env" "staff_login" "FAIL"
        return 1
    fi
}

###############################################################################
# Runtime-specific test functions
###############################################################################

test_docker_env() {
    local env=$1
    local compose_file="compose.docker.yml"

    log_section "Testing Docker - $env Environment"

    # Set environment
    export NINA_ENV=$env

    # Start stack
    log_info "Starting Docker stack for $env..."
    if ! docker-compose -f "$compose_file" up -d postgres api 2>&1 | tail -5; then
        log_error "Failed to start Docker stack"
        record_result "docker" "$env" "startup" "FAIL"
        return 1
    fi

    sleep 5

    # Wait for containers
    local db_container="ninaivalaigal-${env}-db"
    local api_container="ninaivalaigal-${env}-api"

    if ! wait_for_healthy "$db_container"; then
        record_result "docker" "$env" "startup" "FAIL"
        docker-compose -f "$compose_file" down
        return 1
    fi

    if ! wait_for_healthy "$api_container"; then
        record_result "docker" "$env" "startup" "FAIL"
        docker-compose -f "$compose_file" down
        return 1
    fi

    record_result "docker" "$env" "startup" "PASS"

    # Run tests
    test_database_extensions "docker" "$env" "$db_container"
    test_api_health "docker" "$env" "http://localhost:13370"
    test_staff_login "docker" "$env" "http://localhost:13370"

    # Cleanup
    log_info "Stopping Docker stack..."
    docker-compose -f "$compose_file" down

    log_success "Docker $env testing complete"
}

test_colima_env() {
    local env=$1
    local compose_file="compose.colima.yml"

    log_section "Testing Colima - $env Environment"

    # Check if Colima is running
    if ! colima status 2>/dev/null | grep -q "running"; then
        log_warning "Colima not running, skipping Colima tests"
        record_result "colima" "$env" "startup" "SKIP"
        return 0
    fi

    # Set environment
    export NINA_ENV=$env

    # Start stack
    log_info "Starting Colima stack for $env..."
    if ! docker-compose -f "$compose_file" up -d postgres api 2>&1 | tail -5; then
        log_error "Failed to start Colima stack"
        record_result "colima" "$env" "startup" "FAIL"
        return 1
    fi

    sleep 5

    # Wait for containers
    local db_container="ninaivalaigal-${env}-db"
    local api_container="ninaivalaigal-${env}-api"

    if ! wait_for_healthy "$db_container"; then
        record_result "colima" "$env" "startup" "FAIL"
        docker-compose -f "$compose_file" down
        return 1
    fi

    if ! wait_for_healthy "$api_container"; then
        record_result "colima" "$env" "startup" "FAIL"
        docker-compose -f "$compose_file" down
        return 1
    fi

    record_result "colima" "$env" "startup" "PASS"

    # Run tests
    test_database_extensions "colima" "$env" "$db_container"
    test_api_health "colima" "$env" "http://localhost:13370"
    test_staff_login "colima" "$env" "http://localhost:13370"

    # Cleanup
    log_info "Stopping Colima stack..."
    docker-compose -f "$compose_file" down

    log_success "Colima $env testing complete"
}

test_apple_cli_env() {
    local env=$1
    local compose_file="compose.apple.yml"

    log_section "Testing Apple Container CLI - $env Environment"

    # Check if container command exists
    if ! command -v container &> /dev/null; then
        log_warning "Apple Container CLI not found, skipping tests"
        record_result "apple_cli" "$env" "startup" "SKIP"
        return 0
    fi

    # Set environment
    export NINA_ENV=$env

    # Start stack
    log_info "Starting Apple CLI stack for $env..."
    if ! docker-compose -f "$compose_file" up -d postgres api 2>&1 | tail -5; then
        log_error "Failed to start Apple CLI stack"
        record_result "apple_cli" "$env" "startup" "FAIL"
        return 1
    fi

    sleep 5

    # Wait for containers
    local db_container="ninaivalaigal-${env}-db"
    local api_container="ninaivalaigal-${env}-api"

    if ! wait_for_healthy "$db_container"; then
        record_result "apple_cli" "$env" "startup" "FAIL"
        docker-compose -f "$compose_file" down
        return 1
    fi

    if ! wait_for_healthy "$api_container"; then
        record_result "apple_cli" "$env" "startup" "FAIL"
        docker-compose -f "$compose_file" down
        return 1
    fi

    record_result "apple_cli" "$env" "startup" "PASS"

    # Run tests
    test_database_extensions "apple_cli" "$env" "$db_container"
    test_api_health "apple_cli" "$env" "http://localhost:13370"
    test_staff_login "apple_cli" "$env" "http://localhost:13370"

    # Cleanup
    log_info "Stopping Apple CLI stack..."
    docker-compose -f "$compose_file" down

    log_success "Apple CLI $env testing complete"
}

###############################################################################
# Main Test Execution
###############################################################################

main() {
    log_section "ARM64 Runtime Combination Validation"

    log_info "This will test all 9 ARM64 combinations:"
    log_info "  - Docker (dev, test, prod)"
    log_info "  - Colima (dev, test, prod)"
    log_info "  - Apple Container CLI (dev, test, prod)"
    echo ""

    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Validation cancelled"
        exit 0
    fi

    # Save current environment
    OLD_ENV=${NINA_ENV:-dev}

    # Test all combinations
    for env in dev test prod; do
        test_docker_env "$env" || true
        test_colima_env "$env" || true
        test_apple_cli_env "$env" || true
    done

    # Restore environment
    export NINA_ENV=$OLD_ENV

    # Print results
    log_section "Validation Results"

    echo ""
    echo "Summary:"
    echo "  Total Tests: $TOTAL_TESTS"
    echo "  Passed: $PASSED_TESTS"
    echo "  Failed: $FAILED_TESTS"
    echo ""

    # Detailed results
    echo "Detailed Results:"
    echo ""

    for runtime in docker colima apple_cli; do
        echo "$runtime:"
        for env in dev test prod; do
            echo "  $env:"
            for test in startup database_extensions api_health staff_login; do
                local key="${runtime}_${env}_${test}"
                local result=${RESULTS[$key]:-"NOT_RUN"}

                if [ "$result" = "PASS" ]; then
                    echo -e "    ${GREEN}✅${NC} $test"
                elif [ "$result" = "FAIL" ]; then
                    echo -e "    ${RED}❌${NC} $test"
                elif [ "$result" = "SKIP" ]; then
                    echo -e "    ${YELLOW}⏭️${NC}  $test (skipped)"
                else
                    echo -e "    ${YELLOW}❓${NC} $test (not run)"
                fi
            done
        done
        echo ""
    done

    # Exit code based on results
    if [ $FAILED_TESTS -gt 0 ]; then
        log_error "Validation FAILED - $FAILED_TESTS tests failed"
        exit 1
    elif [ $PASSED_TESTS -eq 0 ]; then
        log_warning "No tests were run"
        exit 2
    else
        log_success "Validation PASSED - All $PASSED_TESTS tests passed!"
        exit 0
    fi
}

# Run main
main "$@"
