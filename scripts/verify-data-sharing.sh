#!/bin/bash
###############################################################################
# Verify Data Sharing Across Runtimes
#
# Tests that all runtimes (Docker, Colima, Apple CLI) share the same database
# and Redis instances per environment.
#
# For each environment (dev/test/prod):
#   1. Start Docker runtime
#   2. Create test staff user
#   3. Stop Docker
#   4. Start Colima runtime
#   5. Verify test user exists (proves data sharing)
#   6. Stop Colima
#   7. Start Apple CLI
#   8. Verify test user exists
#   9. Cleanup test data
###############################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

###############################################################################
# Test Functions
###############################################################################

create_test_staff() {
    local runtime=$1
    local env=$2
    local api_port=$3

    log_info "Creating test staff user via $runtime..."

    local test_email="test_${runtime}@example.com"

    # Create test staff
    local response=$(curl -s -X POST "http://localhost:${api_port}/auth/staff/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"admin@ninaivalaigal.com\", \"password\": \"ChangeMe123!@#\"}")

    local token=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")

    if [ -z "$token" ]; then
        log_error "Failed to get admin token"
        return 1
    fi

    # Create staff via API (assuming endpoint exists)
    # For now, insert directly into database
    local db_container="ninaivalaigal-${env}-db"

    docker exec "$db_container" psql -U nina -d "ninaivalaigal_${env}" -c \
        "INSERT INTO staff (id, name, email, password_hash, role, is_active)
         VALUES (gen_random_uuid(), 'Test ${runtime}', '${test_email}',
                 '\$2b\$12\$dummy_hash_for_testing', 'support', true)
         ON CONFLICT (email) DO NOTHING;" 2>/dev/null

    log_success "Created test user: $test_email"
    echo "$test_email"
}

verify_test_staff() {
    local runtime=$1
    local env=$2
    local test_email=$3

    log_info "Verifying test staff exists via $runtime..."

    local db_container="ninaivalaigal-${env}-db"

    if docker exec "$db_container" psql -U nina -d "ninaivalaigal_${env}" -c \
        "SELECT email FROM staff WHERE email = '${test_email}';" 2>/dev/null | grep -q "$test_email"; then
        log_success "Test user found: $test_email"
        return 0
    else
        log_error "Test user NOT found: $test_email"
        return 1
    fi
}

cleanup_test_staff() {
    local env=$1

    log_info "Cleaning up test staff users..."

    local db_container="ninaivalaigal-${env}-db"

    docker exec "$db_container" psql -U nina -d "ninaivalaigal_${env}" -c \
        "DELETE FROM staff WHERE email LIKE 'test_%@example.com';" 2>/dev/null || true

    log_success "Cleanup complete"
}

test_environment_data_sharing() {
    local env=$1

    log_info "════════════════════════════════════════════════════════"
    log_info "  Testing Data Sharing - $env Environment"
    log_info "════════════════════════════════════════════════════════"
    echo ""

    export NINA_ENV=$env

    # Track created users
    local docker_user=""
    local colima_user=""
    local apple_user=""

    # Test Docker Runtime
    log_info "▶️  Starting Docker runtime..."
    if docker-compose -f compose.docker.yml up -d postgres api 2>&1 | tail -3; then
        sleep 10

        if wait_for_healthy "ninaivalaigal-${env}-db" 30; then
            docker_user=$(create_test_staff "docker" "$env" "13370")

            log_info "Stopping Docker runtime..."
            docker-compose -f compose.docker.yml stop api 2>/dev/null || true
        else
            log_error "Docker database failed to start"
            return 1
        fi
    else
        log_error "Failed to start Docker runtime"
        return 1
    fi

    # Test Colima Runtime (if available)
    if colima status 2>/dev/null | grep -q "running"; then
        log_info "▶️  Starting Colima runtime..."
        if docker-compose -f compose.colima.yml up -d postgres api 2>&1 | tail -3; then
            sleep 10

            if wait_for_healthy "ninaivalaigal-${env}-db" 30; then
                # Verify Docker user visible
                if verify_test_staff "colima" "$env" "$docker_user"; then
                    log_success "✅ DATA SHARING CONFIRMED: Docker → Colima"
                else
                    log_error "❌ DATA SHARING FAILED: Docker user not visible in Colima"
                    docker-compose -f compose.colima.yml down
                    return 1
                fi

                # Create Colima user
                colima_user=$(create_test_staff "colima" "$env" "13370")

                log_info "Stopping Colima runtime..."
                docker-compose -f compose.colima.yml stop api 2>/dev/null || true
            fi
        else
            log_warning "Failed to start Colima runtime (skipping)"
        fi
    else
        log_warning "Colima not running (skipping Colima tests)"
    fi

    # Test Apple CLI Runtime (if available)
    if command -v container &> /dev/null; then
        log_info "▶️  Starting Apple CLI runtime..."
        if docker-compose -f compose.apple.yml up -d postgres api 2>&1 | tail -3; then
            sleep 10

            if wait_for_healthy "ninaivalaigal-${env}-db" 30; then
                # Verify both previous users visible
                if verify_test_staff "apple_cli" "$env" "$docker_user"; then
                    log_success "✅ DATA SHARING CONFIRMED: Docker → Apple CLI"
                else
                    log_error "❌ DATA SHARING FAILED: Docker user not visible in Apple CLI"
                fi

                if [ -n "$colima_user" ] && verify_test_staff "apple_cli" "$env" "$colima_user"; then
                    log_success "✅ DATA SHARING CONFIRMED: Colima → Apple CLI"
                else
                    if [ -n "$colima_user" ]; then
                        log_error "❌ DATA SHARING FAILED: Colima user not visible in Apple CLI"
                    fi
                fi

                # Create Apple user
                apple_user=$(create_test_staff "apple" "$env" "13370")

                log_info "Stopping Apple CLI runtime..."
                docker-compose -f compose.apple.yml stop api 2>/dev/null || true
            fi
        else
            log_warning "Failed to start Apple CLI runtime (skipping)"
        fi
    else
        log_warning "Apple Container CLI not found (skipping Apple tests)"
    fi

    # Final verification: Start Docker again and check all users
    log_info "▶️  Final verification with Docker runtime..."
    if docker-compose -f compose.docker.yml up -d postgres 2>&1 | tail -3; then
        sleep 5

        if wait_for_healthy "ninaivalaigal-${env}-db" 30; then
            local all_present=true

            # Check all created users
            if [ -n "$docker_user" ] && ! verify_test_staff "docker_final" "$env" "$docker_user"; then
                all_present=false
            fi

            if [ -n "$colima_user" ] && ! verify_test_staff "docker_final" "$env" "$colima_user"; then
                all_present=false
            fi

            if [ -n "$apple_user" ] && ! verify_test_staff "docker_final" "$env" "$apple_user"; then
                all_present=false
            fi

            if $all_present; then
                log_success "✅ FULL DATA SHARING CONFIRMED: All users visible across all runtimes"
            else
                log_error "❌ DATA SHARING INCOMPLETE: Some users missing"
            fi
        fi
    fi

    # Cleanup
    cleanup_test_staff "$env"

    # Stop all
    docker-compose -f compose.docker.yml down 2>/dev/null || true
    docker-compose -f compose.colima.yml down 2>/dev/null || true
    docker-compose -f compose.apple.yml down 2>/dev/null || true

    echo ""
    log_success "Data sharing test complete for $env environment"
    echo ""
}

wait_for_healthy() {
    local container_name=$1
    local max_wait=${2:-60}
    local waited=0

    while [ $waited -lt $max_wait ]; do
        if docker ps --filter "name=$container_name" --filter "health=healthy" | grep -q "$container_name"; then
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
    done

    return 1
}

###############################################################################
# Main
###############################################################################

main() {
    log_info "════════════════════════════════════════════════════════"
    log_info "  Data Sharing Verification Across Runtimes"
    log_info "════════════════════════════════════════════════════════"
    echo ""

    log_info "This will verify that:"
    log_info "  1. Docker, Colima, and Apple CLI share the same database per environment"
    log_info "  2. Data created in one runtime is visible in others"
    log_info "  3. Volume configuration is correct"
    echo ""

    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Verification cancelled"
        exit 0
    fi

    # Save current environment
    OLD_ENV=${NINA_ENV:-dev}

    # Test dev environment (most important)
    test_environment_data_sharing "dev"

    # Optionally test other environments
    read -p "Test other environments (test, prod)? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_environment_data_sharing "test"
        test_environment_data_sharing "prod"
    fi

    # Restore environment
    export NINA_ENV=$OLD_ENV

    log_success "════════════════════════════════════════════════════════"
    log_success "  Data Sharing Verification Complete!"
    log_success "════════════════════════════════════════════════════════"
}

main "$@"
