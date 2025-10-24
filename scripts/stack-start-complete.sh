#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Complete Ninaivalaigal Stack Startup Script
# Version: 2.0.0 - Day 3 COMPLETE Stack with PgBouncer Mandate
# Components: PostgreSQL → PgBouncer → Redis → API → Customer UI → Admin UI

set -euo pipefail

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly ENV="${NINA_ENV:-dev}"

# Container names (SPEC-086 unified naming + Task #85 Dual PgBouncer)
readonly DB_CONTAINER="ninaivalaigal-${ENV}-db"
readonly PGBOUNCER_TX_CONTAINER="ninaivalaigal-${ENV}-pgbouncer-tx"    # Transaction mode (stateless)
readonly PGBOUNCER_SESS_CONTAINER="ninaivalaigal-${ENV}-pgbouncer-sess"  # Session mode (prepared statements)
readonly REDIS_CONTAINER="ninaivalaigal-${ENV}-redis"
readonly API_CONTAINER="ninaivalaigal-${ENV}-api"
readonly CUSTOMER_APP_CONTAINER="ninaivalaigal-${ENV}-customer-app"
readonly ADMIN_CONSOLE_CONTAINER="ninaivalaigal-${ENV}-admin-console"

# Ports (Apple CLI dev - SPEC-086)
readonly DB_PORT=5452              # Direct DB (admin only)
readonly PGBOUNCER_PORT=6452       # **ALL** app connections through here
readonly REDIS_PORT=6399
readonly API_PORT=13390
readonly CUSTOMER_UI_PORT=8101
readonly ADMIN_UI_PORT=8201

# Database configuration
readonly DB_NAME="ninaivalaigal_${ENV}"
readonly DB_USER="nina"
readonly DB_PASSWORD="${NINA_DB_PASSWORD:-dev_password_change_in_production}"
readonly REDIS_PASSWORD="${NINA_REDIS_PASSWORD:-dev_redis_password}"
readonly JWT_SECRET="${NINA_JWT_SECRET:-dev_jwt_secret_change_in_production}"

# Health check configuration
readonly MAX_RETRIES=30
readonly RETRY_DELAY=2

# Logging
log_info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} ℹ️  $*"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} ✅ $*"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} ⚠️  $*"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} ❌ $*"
}

# Cleanup container
cleanup_container() {
    local container_name=$1
    if container list --all | grep -q "$container_name"; then
        log_info "Cleaning up $container_name..."
        container stop "$container_name" >/dev/null 2>&1 || true
        container delete "$container_name" >/dev/null 2>&1 || true
    fi
}

# Wait for container
wait_for_container() {
    local container_name=$1
    local max_wait=${2:-30}
    local elapsed=0

    while [ $elapsed -lt $max_wait ]; do
        if container list | grep -q "$container_name.*running"; then
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    return 1
}

# Get container IP
get_container_ip() {
    local container_name=$1
    container list | grep "$container_name" | awk '{print $6}'
}

# 1. START POSTGRESQL
start_database() {
    log_info "════════════════════════════════════════"
    log_info "Step 1/6: Starting PostgreSQL Database"
    log_info "════════════════════════════════════════"

    cleanup_container "$DB_CONTAINER"

    log_info "Starting $DB_CONTAINER on port $DB_PORT..."

    # Use GHCR image if available, otherwise local build
    local db_image="${NINA_DB_IMAGE:-nina-intelligence-db:arm64}"

    container run -d --name "$DB_CONTAINER" \
        -p "$DB_PORT:5432" \
        -e POSTGRES_DB="$DB_NAME" \
        -e POSTGRES_USER="$DB_USER" \
        -e POSTGRES_PASSWORD="$DB_PASSWORD" \
        -e POSTGRES_HOST_AUTH_METHOD=md5 \
        -e PGDATA="/var/lib/postgresql/data/pgdata" \
        -v "ninaivalaigal_${ENV}_db_data:/var/lib/postgresql/data" \
        "$db_image"

    if ! wait_for_container "$DB_CONTAINER" 30; then
        log_error "Database failed to start"
        return 1
    fi

    log_info "Waiting for database to accept connections..."
    local retries=0
    while [ $retries -lt $MAX_RETRIES ]; do
        if PGPASSWORD="$DB_PASSWORD" psql -h localhost -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" >/dev/null 2>&1; then
            log_success "PostgreSQL ready (port $DB_PORT)"
            return 0
        fi
        retries=$((retries + 1))
        sleep $RETRY_DELAY
    done

    log_error "Database health check failed"
    return 1
}

# 2. START PGBOUNCER
start_pgbouncer() {
    log_info "════════════════════════════════════════"
    log_info "Step 2/6: Starting PgBouncer (Connection Gateway)"
    log_info "════════════════════════════════════════"

    # Task #85: Start dual PgBouncer instances
    log_info "Task #85: Starting dual PgBouncer (transaction + session modes)..."

    # Use dedicated start scripts for dual PgBouncer
    if [ -f "$ROOT_DIR/scripts/nv-pgbouncer-tx-start.sh" ]; then
        log_info "Starting PgBouncer-TX (transaction mode)..."
        "$ROOT_DIR/scripts/nv-pgbouncer-tx-start.sh" > /dev/null 2>&1 || {
            log_error "PgBouncer-TX failed to start"
            return 1
        }
        log_success "PgBouncer-TX ready (port 6432)"
    else
        log_error "nv-pgbouncer-tx-start.sh not found"
        return 1
    fi

    if [ -f "$ROOT_DIR/scripts/nv-pgbouncer-sess-start.sh" ]; then
        log_info "Starting PgBouncer-SESS (session mode)..."
        "$ROOT_DIR/scripts/nv-pgbouncer-sess-start.sh" > /dev/null 2>&1 || {
            log_error "PgBouncer-SESS failed to start"
            return 1
        }
        log_success "PgBouncer-SESS ready (port 6433)"
    else
        log_error "nv-pgbouncer-sess-start.sh not found"
        return 1
    fi

    log_success "Dual PgBouncer started successfully"
    log_info "  TX Mode (port 6432):   For Core API, GraphOps, Business Service, Graph Service"
    log_info "  SESS Mode (port 6433): For Memory Service (SQLx/prepared statements)"
    return 0
}

# 3. START REDIS
start_redis() {
    log_info "════════════════════════════════════════"
    log_info "Step 3/6: Starting Redis Cache"
    log_info "════════════════════════════════════════"

    cleanup_container "$REDIS_CONTAINER"

    log_info "Starting $REDIS_CONTAINER on port $REDIS_PORT..."
    container run -d --name "$REDIS_CONTAINER" \
        -p "$REDIS_PORT:6379" \
        -v "ninaivalaigal_${ENV}_redis_data:/data" \
        redis:7-alpine redis-server \
            --requirepass "$REDIS_PASSWORD" \
            --maxmemory 512mb \
            --maxmemory-policy allkeys-lru

    if ! wait_for_container "$REDIS_CONTAINER" 20; then
        log_error "Redis failed to start"
        return 1
    fi

    log_info "Testing Redis connection..."
    local retries=0
    while [ $retries -lt $MAX_RETRIES ]; do
        if redis-cli -h localhost -p $REDIS_PORT -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q "PONG"; then
            log_success "Redis ready (port $REDIS_PORT)"
            return 0
        fi
        retries=$((retries + 1))
        sleep $RETRY_DELAY
    done

    log_error "Redis health check failed"
    return 1
}

# 4. START API
start_api() {
    log_info "════════════════════════════════════════"
    log_info "Step 4/6: Starting FastAPI Backend"
    log_info "════════════════════════════════════════"

    cleanup_container "$API_CONTAINER"

    # Get container IPs (Task #85: Use TX mode for stateless API)
    local pgbouncer_ip=$(get_container_ip "$PGBOUNCER_TX_CONTAINER")
    local redis_ip=$(get_container_ip "$REDIS_CONTAINER")

    log_info "PgBouncer-TX IP: $pgbouncer_ip (transaction mode)"
    log_info "Redis IP: $redis_ip"

    # **CRITICAL**: API connects to PgBouncer-TX (transaction mode), NOT direct DB
    local database_url="postgresql://${DB_USER}:${DB_PASSWORD}@${pgbouncer_ip}:6432/${DB_NAME}"

    log_info "Starting $API_CONTAINER on port $API_PORT..."

    # Check if API image exists
    if ! container image list | grep -q "nina-api.*arm64"; then
        log_warning "API image not found. Build with: container build -t nina-api:arm64 -f Dockerfile.api ."
        log_warning "Skipping API startup"
        return 0
    fi

    container run -d --name "$API_CONTAINER" \
        -p "$API_PORT:8000" \
        -e DATABASE_URL="$database_url" \
        -e NINAIVALAIGAL_DATABASE_URL="$database_url" \
        -e REDIS_HOST="$redis_ip" \
        -e REDIS_PORT=6379 \
        -e REDIS_PASSWORD="$REDIS_PASSWORD" \
        -e NINAIVALAIGAL_JWT_SECRET="$JWT_SECRET" \
        -e NINA_ENV="$ENV" \
        -e PYTHONPATH=/app:/app/server \
        nina-api:arm64

    if ! wait_for_container "$API_CONTAINER" 30; then
        log_error "API failed to start"
        return 1
    fi

    log_info "Testing API health endpoint..."
    local retries=0
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -sf "http://localhost:$API_PORT/health" >/dev/null 2>&1; then
            log_success "API ready (port $API_PORT)"
            log_success "API is connected through PgBouncer ✓"
            return 0
        fi
        retries=$((retries + 1))
        sleep $RETRY_DELAY
    done

    log_warning "API health check timeout (may still be starting...)"
    log_info "Check logs: container logs $API_CONTAINER"
    return 0  # Don't fail, API might need more time
}

# 5. START CUSTOMER UI
start_customer_ui() {
    log_info "════════════════════════════════════════"
    log_info "Step 5/6: Starting Customer UI (External)"
    log_info "════════════════════════════════════════"

    # Check if customer app image exists
    if ! container image list | grep -q "ninaivalaigal-ui\|customer-app"; then
        log_warning "Customer UI image not found. Build with: docker-compose -f compose.docker.yml build customer-app"
        log_info "Skipping Customer UI (optional)"
        return 0
    fi

    cleanup_container "$CUSTOMER_APP_CONTAINER"

    log_info "Starting $CUSTOMER_APP_CONTAINER on port $CUSTOMER_UI_PORT..."

    # Try ninaivalaigal-ui first, fallback to customer-app specific image
    local ui_image="ninaivalaigal-ui:latest"
    if ! container image list | grep -q "ninaivalaigal-ui"; then
        ui_image="ninaivalaigal-customer-app:latest"
    fi

    container run -d --name "$CUSTOMER_APP_CONTAINER" \
        -p "$CUSTOMER_UI_PORT:8081" \
        -e NODE_ENV=production \
        -e API_URL="http://localhost:$API_PORT" \
        -e NINA_ENV="$ENV" \
        "$ui_image" 2>/dev/null || {
        log_warning "Customer UI failed to start (optional component)"
        return 0
    }

    if wait_for_container "$CUSTOMER_APP_CONTAINER" 20; then
        log_success "Customer UI ready (port $CUSTOMER_UI_PORT)"
    else
        log_info "Customer UI starting in background..."
    fi
    return 0
}

# 6. START ADMIN UI
start_admin_ui() {
    log_info "════════════════════════════════════════"
    log_info "Step 6/6: Starting Admin Console (Internal)"
    log_info "════════════════════════════════════════"

    # Check if admin console image exists
    if ! container image list | grep -q "ninaivalaigal-ui\|admin-console"; then
        log_warning "Admin Console image not found. Build with: docker-compose -f compose.docker.yml build admin-console"
        log_info "Skipping Admin Console (optional)"
        return 0
    fi

    cleanup_container "$ADMIN_CONSOLE_CONTAINER"

    log_info "Starting $ADMIN_CONSOLE_CONTAINER on port $ADMIN_UI_PORT..."

    # Try ninaivalaigal-ui first, fallback to admin-console specific image
    local admin_image="ninaivalaigal-ui:latest"
    if ! container image list | grep -q "ninaivalaigal-ui"; then
        admin_image="ninaivalaigal-admin-console:latest"
    fi

    container run -d --name "$ADMIN_CONSOLE_CONTAINER" \
        -p "$ADMIN_UI_PORT:8181" \
        -e NODE_ENV=production \
        -e API_URL="http://localhost:$API_PORT" \
        -e NINA_ENV="$ENV" \
        "$admin_image" 2>/dev/null || {
        log_warning "Admin Console failed to start (optional component)"
        return 0
    }

    if wait_for_container "$ADMIN_CONSOLE_CONTAINER" 20; then
        log_success "Admin Console ready (port $ADMIN_UI_PORT)"
    else
        log_info "Admin Console starting in background..."
    fi
    return 0
}

# Display final status
show_stack_status() {
    echo ""
    log_success "╔══════════════════════════════════════════════════════╗"
    log_success "║       Complete Stack Started Successfully!          ║"
    log_success "╚══════════════════════════════════════════════════════╝"
    echo ""
    echo "📊 Running Containers:"
    container list | grep "ninaivalaigal-${ENV}" || echo "  No containers found"
    echo ""
    echo "🔗 Connection Information:"
    echo "  Database (Direct - Admin Only):"
    echo "    → localhost:$DB_PORT"
    echo ""
    echo "  ⭐ PgBouncer (Application Gateway):"
    echo "    → localhost:$PGBOUNCER_PORT"
    echo "    → ALL app connections MUST use this!"
    echo ""
    echo "  Redis Cache:"
    echo "    → localhost:$REDIS_PORT"
    echo ""
    echo "  API (Backend):"
    echo "    → http://localhost:$API_PORT"
    echo "    → Health: http://localhost:$API_PORT/health"
    echo "    → Docs: http://localhost:$API_PORT/docs"
    echo ""
    echo "  Customer UI (External):"
    echo "    → http://localhost:$CUSTOMER_UI_PORT"
    echo ""
    echo "  Admin Console (Internal):"
    echo "    → http://localhost:$ADMIN_UI_PORT"
    echo ""
    echo "📋 Management Commands:"
    echo "  Status:  make stack-check"
    echo "  Stop:    make stack-stop"
    echo "  Restart: make stack-restart"
    echo ""
    log_warning "⚠️  Database Connection Rules:"
    log_warning "   - Applications → PgBouncer:$PGBOUNCER_PORT"
    log_warning "   - Direct DB:$DB_PORT is for admin tasks only!"
    echo ""
}

# Main execution
main() {
    echo ""
    log_info "╔══════════════════════════════════════════════════════╗"
    log_info "║    Complete Ninaivalaigal Stack Startup              ║"
    log_info "║    Environment: $ENV                                 ║"
    log_info "║    Architecture: SPEC-086 Compliant                  ║"
    log_info "╚══════════════════════════════════════════════════════╝"
    echo ""

    # Start all components in order
    start_database || exit 1
    echo ""
    start_pgbouncer || exit 1
    echo ""
    start_redis || exit 1
    echo ""
    start_api || exit 1
    echo ""
    start_customer_ui
    echo ""
    start_admin_ui

    # Show final status
    show_stack_status

    exit 0
}

main "$@"
