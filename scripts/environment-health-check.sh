#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
set -euo pipefail

# Environment Health Check Script
# This script performs comprehensive health checks on the ninaivalaigal development environment
# and provides detailed diagnostics to prevent environment degradation.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="${PROJECT_ROOT}/logs/health-check-$(date +%Y%m%d-%H%M%S).log"

# Ensure logs directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Status functions
print_status() {
    local status=$1
    local message=$2
    case $status in
        "PASS")
            echo -e "${GREEN}✅ PASS${NC}: $message" | tee -a "$LOG_FILE"
            ;;
        "FAIL")
            echo -e "${RED}❌ FAIL${NC}: $message" | tee -a "$LOG_FILE"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  WARN${NC}: $message" | tee -a "$LOG_FILE"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  INFO${NC}: $message" | tee -a "$LOG_FILE"
            ;;
    esac
}

# Health check functions
check_colima_status() {
    log "Checking Colima status..."

    if ! command -v colima &> /dev/null; then
        print_status "FAIL" "Colima is not installed"
        return 1
    fi

    if colima status &> /dev/null; then
        local colima_info=$(colima status 2>/dev/null)
        print_status "PASS" "Colima is running"
        log "Colima info: $colima_info"
    else
        print_status "FAIL" "Colima is not running"
        return 1
    fi
}

check_docker_status() {
    log "Checking Docker status..."

    if ! command -v docker &> /dev/null; then
        print_status "FAIL" "Docker command is not available"
        return 1
    fi

    if docker info &> /dev/null; then
        print_status "PASS" "Docker is accessible"
        local docker_version=$(docker --version)
        log "Docker version: $docker_version"
    else
        print_status "FAIL" "Docker is not accessible"
        return 1
    fi
}

check_containers() {
    log "Checking container status..."

    local expected_containers=("ninaivalaigal-dev-db" "ninaivalaigal-dev-redis" "ninaivalaigal-dev-api" "ninaivalaigal-dev-ui")
    local running_containers=$(docker ps --format "table {{.Names}}" | tail -n +2)

    for container in "${expected_containers[@]}"; do
        if echo "$running_containers" | grep -q "^$container$"; then
            local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-health-check")
            if [[ "$status" == "healthy" ]]; then
                print_status "PASS" "Container $container is running and healthy"
            elif [[ "$status" == "no-health-check" ]]; then
                print_status "WARN" "Container $container is running but has no health check"
            else
                print_status "WARN" "Container $container is running but health status is: $status"
            fi
        else
            print_status "FAIL" "Container $container is not running"
        fi
    done
}

check_api_health() {
    log "Checking API health..."

    local api_url="http://localhost:13370"

    # Basic health check
    if curl -s -f "$api_url/health" > /dev/null; then
        print_status "PASS" "API basic health check"

        # Detailed health check
        local health_response=$(curl -s "$api_url/health/detailed" 2>/dev/null || echo "")
        if [[ -n "$health_response" ]]; then
            print_status "PASS" "API detailed health check"
            log "Health response: $health_response"
        else
            print_status "WARN" "API detailed health check not available"
        fi

        # OpenAPI schema check
        if curl -s -f "$api_url/openapi.json" > /dev/null; then
            print_status "PASS" "API OpenAPI schema accessible"
        else
            print_status "WARN" "API OpenAPI schema not accessible"
        fi

    else
        print_status "FAIL" "API is not responding"
        return 1
    fi
}

check_ui_health() {
    log "Checking UI health..."

    local ui_url="http://localhost:8081"

    if curl -s -f "$ui_url" > /dev/null; then
        print_status "PASS" "UI is accessible"

        # Check response time
        local response_time=$(curl -o /dev/null -s -w '%{time_total}' "$ui_url")
        local response_time_ms=$(echo "$response_time * 1000" | bc -l | cut -d. -f1)

        if [[ $response_time_ms -lt 2000 ]]; then
            print_status "PASS" "UI response time is acceptable (${response_time_ms}ms)"
        else
            print_status "WARN" "UI response time is slow (${response_time_ms}ms)"
        fi
    else
        print_status "FAIL" "UI is not accessible"
        return 1
    fi
}

check_database_connectivity() {
    log "Checking database connectivity..."

    # Use docker exec to test database connection
    if docker exec ninaivalaigal-dev-db pg_isready -U ninaivalaigal -d ninaivalaigal &> /dev/null; then
        print_status "PASS" "Database is accepting connections"

        # Test basic query
        local query_result=$(docker exec ninaivalaigal-dev-db psql -U ninaivalaigal -d ninaivalaigal -t -c "SELECT 1;" 2>/dev/null | xargs)
        if [[ "$query_result" == "1" ]]; then
            print_status "PASS" "Database query execution"
        else
            print_status "WARN" "Database query execution failed"
        fi
    else
        print_status "FAIL" "Database is not accepting connections"
        return 1
    fi
}

check_redis_connectivity() {
    log "Checking Redis connectivity..."

    # Use docker exec to test Redis connection
    if docker exec ninaivalaigal-dev-redis redis-cli ping &> /dev/null; then
        print_status "PASS" "Redis is responding to ping"

        # Test basic operations
        if docker exec ninaivalaigal-dev-redis redis-cli set health_check_test "ok" &> /dev/null && \
           docker exec ninaivalaigal-dev-redis redis-cli get health_check_test &> /dev/null; then
            print_status "PASS" "Redis basic operations"
            docker exec ninaivalaigal-dev-redis redis-cli del health_check_test &> /dev/null
        else
            print_status "WARN" "Redis basic operations failed"
        fi
    else
        print_status "FAIL" "Redis is not responding"
        return 1
    fi
}

check_disk_space() {
    log "Checking disk space..."

    local disk_usage=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//')

    if [[ $disk_usage -lt 80 ]]; then
        print_status "PASS" "Disk space is adequate (${disk_usage}% used)"
    elif [[ $disk_usage -lt 90 ]]; then
        print_status "WARN" "Disk space is getting low (${disk_usage}% used)"
    else
        print_status "FAIL" "Disk space is critically low (${disk_usage}% used)"
    fi
}

check_memory_usage() {
    log "Checking memory usage..."

    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')

    if [[ $memory_usage -lt 80 ]]; then
        print_status "PASS" "Memory usage is normal (${memory_usage}%)"
    elif [[ $memory_usage -lt 90 ]]; then
        print_status "WARN" "Memory usage is high (${memory_usage}%)"
    else
        print_status "FAIL" "Memory usage is critically high (${memory_usage}%)"
    fi
}

check_port_availability() {
    log "Checking port availability..."

    local ports=("5432:Database" "6379:Redis" "13370:API" "8081:UI")

    for port_info in "${ports[@]}"; do
        local port=$(echo "$port_info" | cut -d: -f1)
        local service=$(echo "$port_info" | cut -d: -f2)

        if lsof -i ":$port" &> /dev/null; then
            print_status "PASS" "Port $port ($service) is in use"
        else
            print_status "FAIL" "Port $port ($service) is not in use"
        fi
    done
}

run_smoke_tests() {
    log "Running smoke tests..."

    cd "$PROJECT_ROOT" || exit

    if [[ -f "requirements.txt" ]] && [[ -d "tests/smoke" ]]; then
        # Install test dependencies if needed
        if ! python -c "import pytest" &> /dev/null; then
            print_status "WARN" "pytest not available, installing..."
            pip install pytest requests psycopg2-binary redis &> /dev/null || true
        fi

        # Run smoke tests
        if python -m pytest tests/smoke/ -v --tb=short &> /dev/null; then
            print_status "PASS" "Smoke tests passed"
        else
            print_status "FAIL" "Smoke tests failed"
            log "Running smoke tests with output for debugging..."
            python -m pytest tests/smoke/ -v --tb=short 2>&1 | tee -a "$LOG_FILE" || true
        fi
    else
        print_status "WARN" "Smoke tests not available (missing requirements.txt or tests/smoke/)"
    fi
}

generate_summary() {
    log "Generating health check summary..."

    local total_checks=$(grep -c "PASS\|FAIL\|WARN" "$LOG_FILE" || echo "0")
    local passed_checks=$(grep -c "PASS" "$LOG_FILE" || echo "0")
    local failed_checks=$(grep -c "FAIL" "$LOG_FILE" || echo "0")
    local warning_checks=$(grep -c "WARN" "$LOG_FILE" || echo "0")

    echo ""
    echo "========================================="
    echo "HEALTH CHECK SUMMARY"
    echo "========================================="
    echo "Total checks: $total_checks"
    echo "Passed: $passed_checks"
    echo "Failed: $failed_checks"
    echo "Warnings: $warning_checks"
    echo ""

    if [[ $failed_checks -eq 0 ]]; then
        if [[ $warning_checks -eq 0 ]]; then
            print_status "PASS" "Environment is healthy"
            return 0
        else
            print_status "WARN" "Environment is mostly healthy with some warnings"
            return 1
        fi
    else
        print_status "FAIL" "Environment has critical issues"
        return 2
    fi
}

# Main execution
main() {
    echo "========================================="
    echo "NINAIVALAIGAL ENVIRONMENT HEALTH CHECK"
    echo "========================================="
    echo "Started at: $(date)"
    echo "Log file: $LOG_FILE"
    echo ""

    # Run all health checks
    check_colima_status || true
    check_docker_status || true
    check_containers || true
    check_port_availability || true
    check_database_connectivity || true
    check_redis_connectivity || true
    check_api_health || true
    check_ui_health || true
    check_disk_space || true
    check_memory_usage || true
    run_smoke_tests || true

    # Generate summary and exit with appropriate code
    generate_summary
    local exit_code=$?

    echo ""
    echo "Health check completed at: $(date)"
    echo "Full log available at: $LOG_FILE"

    exit $exit_code
}

# Run main function
main "$@"
