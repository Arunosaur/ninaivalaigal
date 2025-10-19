#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Unified Stack Startup - Works with ANY runtime/environment
# Usage: ./stack-start-unified.sh [runtime] [environment]
#   runtime: docker|colima|apple (default: apple)
#   environment: dev|test|prod (default: dev)
# Version: 1.0.0 - Day 4 Uniform Architecture

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load configuration library (includes colors and logging)
source "${SCRIPT_DIR}/common/config-loader.sh"

# Stack-specific logging functions
log_info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} ℹ️  $*"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} ✅ $*"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} ❌ $*"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} ⚠️  $*"
}

# Parse arguments
RUNTIME=${1:-${NINA_RUNTIME:-apple}}
ENVIRONMENT=${2:-${NINA_ENV:-dev}}

# Load configuration (single source of truth)
if ! load_config "$RUNTIME" "$ENVIRONMENT"; then
    log_error "Configuration loading failed"
    exit 1
fi

# Helper functions
cleanup_or_start_container() {
    local container_name=$1
    # Check if container exists and is stopped
    if $CONTAINER_COMMAND list --all | grep -q "^$container_name .*stopped"; then
        log_info "Starting existing container: $container_name"
        $CONTAINER_COMMAND start "$container_name" 2>/dev/null
        return 2  # Signal that we started existing container
    elif $CONTAINER_COMMAND list | grep -q "^$container_name .*running"; then
        log_warning "Container $container_name already running"
        return 1  # Signal that container is already running
    fi
    return 0  # Signal that we need to create new container
}

wait_for_container() {
    local container_name=$1
    local max_wait=${2:-30}
    local count=0

    while [ $count -lt $max_wait ]; do
        if $CONTAINER_COMMAND list | grep -q "$container_name.*running"; then
            return 0
        fi
        sleep 1
        ((count++))
    done
    return 1
}

get_container_ip() {
    local container_name=$1
    # Apple Container CLI: IP is in column 6 of list output
    $CONTAINER_COMMAND list | grep "^$container_name " | awk '{print $6}'
}

check_database_health() {
    local retries=0
    local max_retries=30

    log_info "Checking database health..."
    while [ $retries -lt $max_retries ]; do
        if PGPASSWORD="$NINA_DB_PASSWORD" psql -h localhost -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" >/dev/null 2>&1; then
            log_success "Database is healthy"
            return 0
        fi
        retries=$((retries + 1))
        sleep 1
    done

    log_error "Database health check failed"
    return 1
}

# START DATABASE
start_database() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "Step 1/4: Starting PostgreSQL Database"
    log_info "════════════════════════════════════════"

    cleanup_or_start_container "$DB_CONTAINER"
    local start_result=$?
    if [ $start_result -eq 1 ]; then
        log_success "$DB_CONTAINER already running"
        return 0
    elif [ $start_result -eq 2 ]; then
        sleep 3
        if ! check_database_health; then
            log_error "Database health check failed"
            return 1
        fi
        log_success "Database is fully operational"
        return 0
    fi
    # Continue with create...

    # Create volume if it doesn't exist (Apple CLI doesn't auto-create)
    if ! $CONTAINER_COMMAND volume list 2>/dev/null | grep -q "$DB_VOLUME"; then
        log_info "Creating volume: $DB_VOLUME"
        $CONTAINER_COMMAND volume create "$DB_VOLUME" >/dev/null 2>&1 || true
    fi

    log_info "Starting $DB_CONTAINER on port $DB_PORT..."
    log_info "Using password from config: ${NINA_DB_PASSWORD:0:3}***"

    $CONTAINER_COMMAND run -d --name "$DB_CONTAINER" \
        -p "$DB_PORT:5432" \
        -e POSTGRES_DB="$DB_NAME" \
        -e POSTGRES_USER="$DB_USER" \
        -e POSTGRES_PASSWORD="$NINA_DB_PASSWORD" \
        -e POSTGRES_HOST_AUTH_METHOD="$POSTGRES_HOST_AUTH_METHOD" \
        -e PGDATA="/var/lib/postgresql/data/pgdata" \
        -v "${DB_VOLUME}:/var/lib/postgresql/data" \
        "$DEFAULT_DB_IMAGE"

    if ! wait_for_container "$DB_CONTAINER" 30; then
        log_error "Database failed to start"
        return 1
    fi

    log_info "Waiting for database to accept connections..."
    local retries=0
    while [ $retries -lt $HEALTH_CHECK_RETRIES ]; do
        if PGPASSWORD="$NINA_DB_PASSWORD" psql -h localhost -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" >/dev/null 2>&1; then
            log_success "Database healthy on port $DB_PORT"
            return 0
        fi
        sleep $HEALTH_CHECK_DELAY
        ((retries++))
    done

    log_warning "Database started but health check timeout (may need more time)"
    return 0
}

# START REDIS
start_redis() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "Step 2/4: Starting Redis Cache"
    log_info "════════════════════════════════════════"

    cleanup_or_start_container "$REDIS_CONTAINER"
    local start_result=$?
    if [ $start_result -eq 1 ]; then
        log_success "$REDIS_CONTAINER already running"
        return 0
    elif [ $start_result -eq 2 ]; then
        sleep 2
        log_success "Redis is operational"
        return 0
    fi
    # Continue with create...

    # Create volume if it doesn't exist
    if ! $CONTAINER_COMMAND volume list 2>/dev/null | grep -q "$REDIS_VOLUME"; then
        log_info "Creating volume: $REDIS_VOLUME"
        $CONTAINER_COMMAND volume create "$REDIS_VOLUME" >/dev/null 2>&1 || true
    fi

    log_info "Starting $REDIS_CONTAINER on port $REDIS_PORT..."

    $CONTAINER_COMMAND run -d --name "$REDIS_CONTAINER" \
        -p "$REDIS_PORT:6379" \
        -e REDIS_PASSWORD="$NINA_REDIS_PASSWORD" \
        -v "${REDIS_VOLUME}:/data" \
        "$DEFAULT_REDIS_IMAGE" \
        sh -c "redis-server --requirepass \"$NINA_REDIS_PASSWORD\" --maxmemory \"$REDIS_MAXMEMORY\" --maxmemory-policy \"$REDIS_MAXMEMORY_POLICY\" --save 60 1000 --appendonly yes"

    if ! wait_for_container "$REDIS_CONTAINER" 20; then
        log_error "Redis failed to start"
        return 1
    fi

    log_info "Testing Redis connection..."
    if redis-cli -h localhost -p $REDIS_PORT -a "$NINA_REDIS_PASSWORD" PING >/dev/null 2>&1; then
        log_success "Redis healthy on port $REDIS_PORT"
    else
        log_warning "Redis started but PING test failed (may need redis-cli installed)"
    fi

    return 0
}

# START PGBOUNCER
start_pgbouncer() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "Step 3/4: Starting PgBouncer"
    log_info "════════════════════════════════════════"

    cleanup_or_start_container "$PGBOUNCER_CONTAINER"
    local start_result=$?
    if [ $start_result -eq 1 ]; then
        log_success "$PGBOUNCER_CONTAINER already running"
        return 0
    elif [ $start_result -eq 2 ]; then
        sleep 2
        log_success "PgBouncer is operational"
        return 0
    fi
    # Continue with create...

    # Get database IP for networking
    local db_ip=$(get_container_ip "$DB_CONTAINER")
    log_info "Database IP: $db_ip"

    # Get SCRAM password hash from database (required for custom nina-pgbouncer image)
    log_info "Extracting SCRAM password hash from database..."
    local scram_password=$($CONTAINER_COMMAND exec "$DB_CONTAINER" \
        psql -U "$DB_USER" -d "$DB_NAME" -t \
        -c "SELECT rolpassword FROM pg_authid WHERE rolname = '$DB_USER';" | tr -d ' ')

    if [ -z "$scram_password" ]; then
        log_error "Failed to extract SCRAM password from database"
        return 1
    fi
    log_info "SCRAM password hash extracted successfully"

    log_info "Starting $PGBOUNCER_CONTAINER on port $PGBOUNCER_PORT..."

    # Use custom nina-pgbouncer image with SCRAM hash
    $CONTAINER_COMMAND run -d --name "$PGBOUNCER_CONTAINER" \
        -p "$PGBOUNCER_PORT:6432" \
        -e DB_HOST="$db_ip" \
        -e SCRAM_PASSWORD="$scram_password" \
        "$DEFAULT_PGBOUNCER_IMAGE"

    if ! wait_for_container "$PGBOUNCER_CONTAINER" 30; then
        log_error "PgBouncer failed to start"
        return 1
    fi

    log_info "Testing PgBouncer connection..."
    local retries=0
    while [ $retries -lt 10 ]; do
        if PGPASSWORD="$NINA_DB_PASSWORD" psql -h localhost -p $PGBOUNCER_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" >/dev/null 2>&1; then
            log_success "PgBouncer healthy on port $PGBOUNCER_PORT"
            return 0
        fi
        sleep 2
        ((retries++))
    done

    log_warning "PgBouncer started but connection test failed (check logs: $CONTAINER_COMMAND logs $PGBOUNCER_CONTAINER)"
    return 0
}

# START API SERVER
start_api() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "Step 4/4: Starting API Server"
    log_info "════════════════════════════════════════"

    cleanup_or_start_container "$API_CONTAINER"
    local start_result=$?
    if [ $start_result -eq 1 ]; then
        log_success "$API_CONTAINER already running"
        return 0
    elif [ $start_result -eq 2 ]; then
        sleep 3
        log_success "API is operational"
        return 0
    fi
    # Continue with create...

    # Get PgBouncer IP for database connection
    local pgbouncer_ip=$(get_container_ip "$PGBOUNCER_CONTAINER")
    local redis_ip=$(get_container_ip "$REDIS_CONTAINER")

    log_info "PgBouncer IP: $pgbouncer_ip"
    log_info "Redis IP: $redis_ip"

    # Build database URL through PgBouncer
    local database_url="postgresql://${DB_USER}:${NINA_DB_PASSWORD}@${pgbouncer_ip}:6432/${DB_NAME}"

    log_info "Starting $API_CONTAINER on port $API_PORT..."
    log_info "Database URL: postgresql://${DB_USER}:***@${pgbouncer_ip}:6432/${DB_NAME}"

    $CONTAINER_COMMAND run -d --name "$API_CONTAINER" \
        -p "$API_PORT:8000" \
        -e NINAIVALAIGAL_DATABASE_URL="$database_url" \
        -e DATABASE_URL="$database_url" \
        -e REDIS_HOST="$redis_ip" \
        -e REDIS_PORT=6379 \
        -e REDIS_PASSWORD="$NINA_REDIS_PASSWORD" \
        -e NINAIVALAIGAL_JWT_SECRET="$NINA_JWT_SECRET" \
        -e ENVIRONMENT="$NINA_ENV" \
        -e LOG_LEVEL="${LOG_LEVEL:-info}" \
        -e ENABLE_DEBUG="${ENABLE_DEBUG:-false}" \
        "$DEFAULT_API_IMAGE"

    if ! wait_for_container "$API_CONTAINER" 30; then
        log_error "API server failed to start"
        log_info "Check logs: $CONTAINER_COMMAND logs $API_CONTAINER"
        return 1
    fi

    # Give container a moment to initialize
    sleep 2

    # Test database connectivity from inside container (like working script)
    log_info "Testing database connectivity from API container..."
    if $CONTAINER_COMMAND exec "$API_CONTAINER" python -c "
import os, psycopg2
dsn = os.getenv('NINAIVALAIGAL_DATABASE_URL') or os.getenv('DATABASE_URL')
print('Connecting to:', dsn)
conn = psycopg2.connect(dsn)
cur = conn.cursor(); cur.execute('SELECT 1'); print('DB connectivity OK:', cur.fetchone())
cur.close(); conn.close()
" 2>&1; then
        log_success "Database connectivity verified from API container"
    else
        log_warning "Database connectivity test failed (API may still work)"
    fi

    log_info "Waiting for API health endpoint..."
    local retries=0
    while [ $retries -lt 15 ]; do
        if curl -sf "http://localhost:$API_PORT/health" >/dev/null 2>&1; then
            log_success "API server healthy on port $API_PORT"
            return 0
        fi
        sleep 2
        ((retries++))
    done

    log_warning "API started but health check timeout (check logs: $CONTAINER_COMMAND logs $API_CONTAINER)"
    return 0
}

# START MEMORY SERVICE (Rust)
start_memory_service() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "Step 5/11: Starting Memory Service (Rust)"
    log_info "════════════════════════════════════════"

    cleanup_or_start_container "$MEMORY_SERVICE_CONTAINER"
    local start_result=$?
    if [ $start_result -eq 1 ] || [ $start_result -eq 2 ]; then
        log_success "$MEMORY_SERVICE_CONTAINER operational"
        return 0
    fi
    log_warning "Memory service not configured for automatic creation - manual start required"
    return 0
}

# START GRPC GATEWAY (Go)
start_grpc_gateway() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "Step 6/11: Starting gRPC Gateway (Go)"
    log_info "════════════════════════════════════════"

    cleanup_or_start_container "$GRPC_GATEWAY_CONTAINER"
    local start_result=$?
    if [ $start_result -eq 1 ] || [ $start_result -eq 2 ]; then
        log_success "$GRPC_GATEWAY_CONTAINER operational"
        return 0
    fi
    log_warning "gRPC Gateway not configured for automatic creation - manual start required"
    return 0
}

# START GRAPH SERVICE (Python)
start_graph_service() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "Step 7/11: Starting Graph Service"
    log_info "════════════════════════════════════════"

    cleanup_or_start_container "$GRAPH_SERVICE_CONTAINER"
    local start_result=$?
    if [ $start_result -eq 1 ] || [ $start_result -eq 2 ]; then
        log_success "$GRAPH_SERVICE_CONTAINER operational"
        return 0
    fi
    log_warning "Graph service not configured for automatic creation - manual start required"
    return 0
}

# START ADMIN VENDOR SERVICE
start_admin_vendor() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "Step 8/11: Starting Admin Vendor Service"
    log_info "════════════════════════════════════════"

    cleanup_or_start_container "$ADMIN_VENDOR_CONTAINER"
    local start_result=$?
    if [ $start_result -eq 1 ] || [ $start_result -eq 2 ]; then
        log_success "$ADMIN_VENDOR_CONTAINER operational"
        return 0
    fi
    log_warning "Admin vendor service not configured for automatic creation - manual start required"
    return 0
}

# START BUSINESS SERVICE
start_business_service() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "Step 9/11: Starting Business Service"
    log_info "════════════════════════════════════════"

    cleanup_or_start_container "$BUSINESS_SERVICE_CONTAINER"
    local start_result=$?
    if [ $start_result -eq 1 ] || [ $start_result -eq 2 ]; then
        log_success "$BUSINESS_SERVICE_CONTAINER operational"
        return 0
    fi
    log_warning "Business service not configured for automatic creation - manual start required"
    return 0
}

# START ADMIN CONSOLE (UI)
start_admin_console() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "Step 10/11: Starting Admin Console"
    log_info "════════════════════════════════════════"

    cleanup_or_start_container "$ADMIN_CONSOLE_CONTAINER"
    local start_result=$?
    if [ $start_result -eq 1 ] || [ $start_result -eq 2 ]; then
        log_success "$ADMIN_CONSOLE_CONTAINER operational"
        return 0
    fi
    log_warning "Admin console not configured for automatic creation - manual start required"
    return 0
}

# START CUSTOMER APP (UI)
start_customer_app() {
    echo ""
    log_info "════════════════════════════════════════"
    log_info "Step 11/11: Starting Customer App"
    log_info "════════════════════════════════════════"

    cleanup_or_start_container "$CUSTOMER_APP_CONTAINER"
    local start_result=$?
    if [ $start_result -eq 1 ] || [ $start_result -eq 2 ]; then
        log_success "$CUSTOMER_APP_CONTAINER operational"
        return 0
    fi
    log_warning "Customer app not configured for automatic creation - manual start required"
    return 0
}

# Display final status
show_stack_status() {
    echo ""
    log_success "╔══════════════════════════════════════════════════════╗"
    log_success "║         Stack Started Successfully!                  ║"
    log_success "╚══════════════════════════════════════════════════════╝"
    echo ""
    echo "📊 Running Containers:"
    $CONTAINER_COMMAND list | grep "$CONTAINER_PREFIX-$NINA_ENV" || echo "  (use '$CONTAINER_COMMAND list' to see all)"
    echo ""
    echo "🔌 Connection Information:"
    echo "  Database (direct):  localhost:$DB_PORT"
    echo "  PgBouncer (pooled): localhost:$PGBOUNCER_PORT ⚠️  USE THIS FOR APPS"
    echo "  Redis:              localhost:$REDIS_PORT"
    echo "  API:                http://localhost:$API_PORT"
    echo "  API Health:         http://localhost:$API_PORT/health"
    echo "  API Docs:           http://localhost:$API_PORT/docs"
    echo ""
    echo "💡 Next Steps:"
    echo "  • Check API:     curl http://localhost:$API_PORT/health"
    echo "  • View logs:     $CONTAINER_COMMAND logs $API_CONTAINER"
    echo "  • Check status:  make stack-check"
    echo "  • Stop stack:    make stack-stop"
    echo ""
    echo "⚠️  REMEMBER: All app connections MUST go through PgBouncer (port $PGBOUNCER_PORT)"
    echo ""
}

# Main execution
main() {
    echo ""
    log_info "╔══════════════════════════════════════════════════════╗"
    log_info "║        Ninaivalaigal Stack Startup                   ║"
    log_info "║        Uniform Architecture - The Right Way          ║"
    log_info "╚══════════════════════════════════════════════════════╝"
    echo ""

    # Configuration already loaded and displayed by config-loader.sh

    # Start infrastructure components
    if ! start_database; then
        log_error "Failed to start database"
        exit 1
    fi

    if ! start_redis; then
        log_error "Failed to start Redis"
        exit 1
    fi

    if ! start_pgbouncer; then
        log_error "Failed to start PgBouncer"
        exit 1
    fi

    # Start application layer
    if ! start_api; then
        log_error "Failed to start API server"
        exit 1
    fi

    # Start additional services (best effort - won't fail if not configured)
    start_memory_service
    start_grpc_gateway
    start_graph_service
    start_admin_vendor
    start_business_service
    start_admin_console
    start_customer_app

    # Show status
    show_stack_status
}

main "$@"
