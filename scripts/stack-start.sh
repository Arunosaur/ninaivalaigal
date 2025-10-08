#!/usr/bin/env bash
# Bulletproof Stack Startup Script
# Version: 1.0.0 - Day 3 Infrastructure Reliability
# Purpose: Start ninaivalaigal Apple CLI stack with health checks and auto-recovery

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly ENV="${NINA_ENV:-dev}"

# Container names (unified naming convention)
readonly DB_CONTAINER="ninaivalaigal-${ENV}-db"
readonly REDIS_CONTAINER="ninaivalaigal-${ENV}-redis"

# Ports (Apple CLI dev ports from port matrix)
readonly DB_PORT=5452
readonly REDIS_PORT=6399

# Database configuration
readonly DB_NAME="ninaivalaigal_${ENV}"
readonly DB_USER="nina"
readonly DB_PASSWORD="${NINA_DB_PASSWORD:-dev_password_change_in_production}"
readonly REDIS_PASSWORD="${NINA_REDIS_PASSWORD:-dev_redis_password}"

# Health check configuration
readonly MAX_RETRIES=30
readonly RETRY_DELAY=2
readonly HEALTH_CHECK_TIMEOUT=60

# Auto-restart configuration
readonly ENABLE_AUTO_RESTART="${ENABLE_AUTO_RESTART:-true}"
readonly RESTART_POLICY="${RESTART_POLICY:-unless-stopped}"

# Logging functions
log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ℹ️  $*"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✅ $*"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ⚠️  $*"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ❌ $*"
}

# Check if container command is available
check_container_cli() {
    if ! command -v container &> /dev/null; then
        log_error "Apple Container CLI 'container' command not found"
        log_info "Please ensure Apple Container CLI is installed"
        exit 1
    fi
    log_success "Container CLI available"
}

# Check if port is available
check_port_available() {
    local port=$1
    local service=$2

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "Port $port already in use (expected for $service)"
        return 1
    fi
    return 0
}

# Wait for container to be healthy
wait_for_container_healthy() {
    local container_name=$1
    local max_wait=${2:-$HEALTH_CHECK_TIMEOUT}
    local elapsed=0

    log_info "Waiting for $container_name to be healthy (max ${max_wait}s)..."

    while [ $elapsed -lt $max_wait ]; do
        if container list | grep -q "$container_name.*running"; then
            log_success "$container_name is running"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
        echo -n "."
    done

    echo ""
    log_error "$container_name failed to become healthy within ${max_wait}s"
    return 1
}

# Check database health
check_database_health() {
    local retries=0

    log_info "Checking database health..."

    while [ $retries -lt $MAX_RETRIES ]; do
        if PGPASSWORD="$DB_PASSWORD" psql -h localhost -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" >/dev/null 2>&1; then
            log_success "Database is healthy and accepting connections"
            return 0
        fi
        retries=$((retries + 1))
        sleep $RETRY_DELAY
        echo -n "."
    done

    echo ""
    log_error "Database health check failed after $MAX_RETRIES attempts"
    return 1
}

# Check Redis health
check_redis_health() {
    local retries=0

    log_info "Checking Redis health..."

    while [ $retries -lt $MAX_RETRIES ]; do
        if redis-cli -h localhost -p $REDIS_PORT -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q "PONG"; then
            log_success "Redis is healthy and responding"
            return 0
        fi
        retries=$((retries + 1))
        sleep $RETRY_DELAY
        echo -n "."
    done

    echo ""
    log_error "Redis health check failed after $MAX_RETRIES attempts"
    return 1
}

# Stop and remove existing container
cleanup_container() {
    local container_name=$1

    if container list --all | grep -q "$container_name"; then
        log_info "Cleaning up existing $container_name..."
        container stop "$container_name" >/dev/null 2>&1 || true
        container delete "$container_name" >/dev/null 2>&1 || true
        log_success "Cleaned up $container_name"
    fi
}

# Start database container
start_database() {
    log_info "Starting $DB_CONTAINER..."

    cleanup_container "$DB_CONTAINER"

    # Note: Apple Container CLI doesn't support --restart flag
    # Auto-restart must be configured externally (launchd, systemd, etc.)
    if [ "$ENABLE_AUTO_RESTART" = "true" ]; then
        log_info "Auto-restart requested (requires external watchdog)"
    fi

    container run -d --name "$DB_CONTAINER" \
        -p "$DB_PORT:5432" \
        -e POSTGRES_DB="$DB_NAME" \
        -e POSTGRES_USER="$DB_USER" \
        -e POSTGRES_PASSWORD="$DB_PASSWORD" \
        -e PGDATA="/var/lib/postgresql/data/pgdata" \
        -v "ninaivalaigal_${ENV}_db_data:/var/lib/postgresql/data" \
        nina-intelligence-db:arm64

    if [ $? -ne 0 ]; then
        log_error "Failed to start $DB_CONTAINER"
        return 1
    fi

    log_success "$DB_CONTAINER started"

    # Wait for container to be healthy
    if ! wait_for_container_healthy "$DB_CONTAINER" 30; then
        return 1
    fi

    # Check database health
    if ! check_database_health; then
        log_error "Database failed health check"
        container logs "$DB_CONTAINER" 2>&1 | tail -20
        return 1
    fi

    log_success "Database is fully operational"
    return 0
}

# Start Redis container
start_redis() {
    log_info "Starting $REDIS_CONTAINER..."

    cleanup_container "$REDIS_CONTAINER"

    # Note: Apple Container CLI doesn't support --restart flag
    # Auto-restart must be configured externally (launchd, systemd, etc.)

    container run -d --name "$REDIS_CONTAINER" \
        -p "$REDIS_PORT:6379" \
        -v "ninaivalaigal_${ENV}_redis_data:/data" \
        redis:7-alpine redis-server \
            --requirepass "$REDIS_PASSWORD" \
            --maxmemory 512mb \
            --maxmemory-policy allkeys-lru

    if [ $? -ne 0 ]; then
        log_error "Failed to start $REDIS_CONTAINER"
        return 1
    fi

    log_success "$REDIS_CONTAINER started"

    # Wait for container to be healthy
    if ! wait_for_container_healthy "$REDIS_CONTAINER" 20; then
        return 1
    fi

    # Check Redis health
    if ! check_redis_health; then
        log_error "Redis failed health check"
        container logs "$REDIS_CONTAINER" 2>&1 | tail -20
        return 1
    fi

    log_success "Redis is fully operational"
    return 0
}

# Display stack status
show_stack_status() {
    echo ""
    log_info "════════════════════════════════════════════════════════"
    log_success "Stack Started Successfully!"
    log_info "════════════════════════════════════════════════════════"
    echo ""
    echo "📊 Container Status:"
    container list | grep "ninaivalaigal-${ENV}" || echo "  No containers found"
    echo ""
    echo "🔗 Connection Information:"
    echo "  Database:"
    echo "    Host: localhost:$DB_PORT"
    echo "    Name: $DB_NAME"
    echo "    User: $DB_USER"
    echo "    Test: PGPASSWORD=$DB_PASSWORD psql -h localhost -p $DB_PORT -U $DB_USER -d $DB_NAME"
    echo ""
    echo "  Redis:"
    echo "    Host: localhost:$REDIS_PORT"
    echo "    Test: redis-cli -h localhost -p $REDIS_PORT -a $REDIS_PASSWORD ping"
    echo ""
    echo "📋 Management Commands:"
    echo "  Status:  ./scripts/stack-status.sh"
    echo "  Stop:    ./scripts/stack-stop.sh"
    echo "  Restart: ./scripts/stack-restart.sh"
    echo "  Logs:    container logs $DB_CONTAINER"
    echo ""

    log_info "💡 Note: Apple Container CLI doesn't support native auto-restart"
    log_info "    Use 'make test-crash-recovery' to test manual recovery"
    echo ""
    log_info "════════════════════════════════════════════════════════"
}

# Main execution
main() {
    echo ""
    log_info "╔══════════════════════════════════════════════════════╗"
    log_info "║  Ninaivalaigal Stack Startup (Apple Container CLI)  ║"
    log_info "║  Environment: $ENV                                   ║"
    log_info "╚══════════════════════════════════════════════════════╝"
    echo ""

    # Pre-flight checks
    check_container_cli

    # Start services in order
    log_info "Starting infrastructure services..."
    echo ""

    if ! start_database; then
        log_error "Failed to start database"
        exit 1
    fi

    echo ""

    if ! start_redis; then
        log_error "Failed to start Redis"
        exit 1
    fi

    # Show final status
    show_stack_status

    exit 0
}

# Run main function
main "$@"
